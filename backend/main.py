# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Depends, HTTPException, Query, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
import threading
from supabase import create_client, Client
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
from dotenv import load_dotenv

load_dotenv()

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the background scraper scheduler in a separate thread
    from scraper.scheduler import start_scheduler
    scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()
    yield

app = FastAPI(title="PharmaCare API", version="1.0.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security: CORS Policy
origins = [
    "http://localhost:3000", # Next.js frontend
    "https://pharmacare.in", # Production domain
    "https://pharma-care-alpha.vercel.app", # Vercel deployment
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET"], # Strictly GET for public API
    allow_headers=["*"],
)

# Supabase Client setup (Singleton - created once at startup)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

_supabase_client: Client | None = None

def _create_supabase_client() -> Client:
    """Create Supabase client once at module level."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Supabase credentials not configured in .env")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    _supabase_client = _create_supabase_client()
except Exception as e:
    import logging
    logging.warning(f"Could not create Supabase client at startup: {e}")
    _supabase_client = None

def get_supabase() -> Client:
    if _supabase_client is None:
        raise HTTPException(status_code=500, detail="Supabase credentials not configured.")
    return _supabase_client

@app.get("/")
def read_root():
    return {"message": "Welcome to PharmaCare API"}

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "ok", "service": "pharmacare-api"}

@app.get("/cron/update-prices")
def cron_update_prices(background_tasks: BackgroundTasks):
    """
    Endpoint to trigger the scraper manually or via external cron services (e.g. cron-job.org).
    """
    from scraper.engine import run_engine
    background_tasks.add_task(run_engine)
    return {"status": "Scraper job started in the background"}

@app.get("/search")
@limiter.limit("60/minute")
def search_products(request: Request, q: str = Query(..., min_length=2), supabase: Client = Depends(get_supabase)):
    """
    Fuzzy search implementation for products.
    Rate limited to 60 requests per minute per IP.
    """
    # Uses Supabase's text search (which leverages pg_trgm in the background if configured via RPC, 
    # or ilike for basic operations)
    response = supabase.table("products").select("id, name, slug, category, image_url").ilike("name", f"%{q}%").limit(10).execute()
    return response.data

@app.get("/products")
@limiter.limit("60/minute")
def list_products(request: Request, category: str = None, supabase: Client = Depends(get_supabase)):
    """
    Fetch a list of recent products, optionally filtered by category.
    Sorted by:
    1. Has fetched prices
    2. Has platform links mapped
    3. Created recently
    """
    # Fetch all matching products with their nested relations
    query = supabase.table("products").select("id, name, slug, category, image_url, created_at, platform_product_links(id, price_history(id))")
    if category:
        query = query.eq("category", category)
    
    response = query.execute()
    products = response.data

    def get_priority(p):
        links = p.get("platform_product_links", [])
        if not links:
            return 0
        has_prices = any(len(link.get("price_history", [])) > 0 for link in links)
        if has_prices:
            return 2
        return 1

    # Sort by priority DESC, then by created_at DESC
    sorted_products = sorted(products, key=lambda p: (get_priority(p), p.get("created_at", "")), reverse=True)
    
    # Clean up relations before returning
    for p in sorted_products:
        p.pop("platform_product_links", None)
        p.pop("created_at", None)
        
    return sorted_products[:20]

@app.get("/product/{slug}")
@limiter.limit("60/minute")
def get_product(request: Request, slug: str, supabase: Client = Depends(get_supabase)):
    """
    Fetch current prices and 30-day history data for a specific product.
    """
    # 1. Fetch product details
    try:
        product_res = supabase.table("products").select("*").eq("slug", slug).single().execute()
        product = product_res.data
    except Exception:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # 2. Fetch platform mappings and latest prices
    mappings_res = supabase.table("platform_product_links").select(
        "id, affiliate_url, scrape_url, platforms(name, logo_url)"
    ).eq("product_id", product["id"]).execute()
    
    mappings = mappings_res.data
    
    # 3. Fetch price history for these mappings for the last 30 days
    from datetime import datetime, timedelta, timezone
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    
    mapping_ids = [m["id"] for m in mappings]
    history_data = []
    
    if mapping_ids:
        history_res = supabase.table("price_history").select("*").in_("mapping_id", mapping_ids).gte("scraped_at", thirty_days_ago).order("scraped_at", desc=False).execute()
        history_data = history_res.data
        
    for mapping in mappings:
        mapping["history"] = [h for h in history_data if h["mapping_id"] == mapping["id"]]
        if mapping["history"]:
            mapping["latest_price"] = mapping["history"][-1]
        else:
            mapping["latest_price"] = None
    
    # 4. Fetch alternatives (products with same composition)
    alternatives = []
    if product.get("composition"):
        try:
            alt_res = supabase.table("products").select("id, name, slug, category, composition, image_url").eq("composition", product["composition"]).neq("id", product["id"]).limit(4).execute()
            alternatives = alt_res.data
        except Exception as e:
            import logging
            logging.warning(f"Failed to fetch alternatives: {e}")
            
    return {
        "product": product,
        "platforms": mappings,
        "alternatives": alternatives
    }

@app.get("/redirect")
@limiter.limit("60/minute")
def redirect_to_platform(request: Request, mapping_id: str, supabase: Client = Depends(get_supabase)):
    """
    Redirects to the affiliate URL of the platform via HTTP 307.
    """
    try:
        mapping_res = supabase.table("platform_product_links").select("affiliate_url, scrape_url").eq("id", mapping_id).single().execute()
        mapping_data = mapping_res.data
    except Exception:
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    if not mapping_data:
        raise HTTPException(status_code=404, detail="Mapping not found")
        
    target_url = mapping_data.get("affiliate_url") or mapping_data.get("scrape_url")
    if not target_url:
        raise HTTPException(status_code=404, detail="No redirect URL available")
    
    return RedirectResponse(url=target_url, status_code=307)
