# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Depends, HTTPException, Query, Request, BackgroundTasks, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
import threading
from supabase import create_client, Client
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import tempfile
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
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
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
def search_products(
    request: Request,
    q: str = Query(..., min_length=2),
    category: str = Query(None, description="Filter by category: medicine, diagnostic, etc."),
    supabase: Client = Depends(get_supabase),
):
    """
    Smart search: uses pg_trgm fuzzy matching + composition search with relevance ranking.
    Supports both medicines and lab tests via optional category filter.
    Falls back to ilike if RPC hasn't been deployed yet.
    """
    import logging

    results = []

    # Try ranked RPC search first
    try:
        rpc_params = {"query": q}
        if category:
            rpc_params["category_filter"] = category

        rpc_res = supabase.rpc("search_products_smart", rpc_params).execute()
        results = rpc_res.data or []

    except Exception:
        # RPC not deployed yet — fall back to ilike
        logging.info("search_products_smart RPC not available, falling back to ilike.")
        query = supabase.table("products").select("id, name, slug, category, composition, image_url")
        if category:
            query = query.eq("category", category)
        response = query.ilike("name", f"%{q}%").limit(10).execute()
        results = response.data or []

    # Log missing search if no results found (min 5 chars to avoid partial typing fragments)
    if not results and len(q.strip()) >= 5:
        try:
            existing = supabase.table("missing_searches").select("id").eq("search_query", q).execute()
            if not existing.data:
                supabase.table("missing_searches").insert({
                    "search_query": q,
                    "search_type": "text"
                }).execute()
        except Exception as e:
            import logging
            logging.warning(f"Failed to log missing search: {e}")

    return results

@app.post("/api/vision-search")
@limiter.limit("20/minute")
async def vision_search(request: Request, file: UploadFile = File(...), supabase: Client = Depends(get_supabase)):
    """
    Accepts an image file, uses Gemini API to extract medicine names,
    and returns matching products from the database using fuzzy search.
    Uses pg_trgm similarity() via RPC for typo-tolerant matching,
    with ilike fallback if the RPC function hasn't been deployed yet.
    """
    from vision import extract_medicines_from_image
    import logging

    # --- Input Validation ---
    ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, and WebP images are allowed.")

    contents = await file.read()
    MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
    if len(contents) > MAX_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="Image too large. Maximum size is 10MB.")

    # --- Process image ---
    tmp_path = None
    try:
        suffix = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        extracted_names = extract_medicines_from_image(tmp_path)

        if not extracted_names:
            return {"results": [], "extracted_text": [], "not_found": []}

        # --- Fuzzy DB search: try pg_trgm RPC, fallback to ilike ---
        all_matches = []
        seen_ids = set()
        not_found_names = []

        try:
            rpc_res = supabase.rpc(
                "search_medicines_fuzzy", {"search_names": extracted_names}
            ).execute()

            matched_terms = set()
            for row in (rpc_res.data or []):
                if row.get("product_id"):
                    matched_terms.add(row["search_term"])
                    if row["product_id"] not in seen_ids:
                        seen_ids.add(row["product_id"])
                        all_matches.append({
                            "id": row["product_id"],
                            "name": row["product_name"],
                            "slug": row["product_slug"],
                            "category": row["product_category"],
                            "image_url": row["product_image_url"],
                        })
            not_found_names = [n for n in extracted_names if n not in matched_terms]

        except Exception:
            # RPC not deployed yet — fall back to per-name ilike search
            logging.info("search_medicines_fuzzy RPC not available, falling back to ilike.")
            for name in extracted_names:
                res = (
                    supabase.table("products")
                    .select("id, name, slug, category, image_url")
                    .ilike("name", f"%{name}%")
                    .limit(3)
                    .execute()
                )
                if not res.data:
                    not_found_names.append(name)
                else:
                    for product in res.data:
                        if product["id"] not in seen_ids:
                            seen_ids.add(product["id"])
                            all_matches.append(product)

        # --- Log missing searches (deduplicated) ---
        if not_found_names:
            try:
                existing = (
                    supabase.table("missing_searches")
                    .select("search_query")
                    .in_("search_query", not_found_names)
                    .execute()
                )
                existing_names = {row["search_query"] for row in existing.data}
                new_names = [n for n in not_found_names if n not in existing_names]

                if new_names:
                    inserts = [{"search_query": n, "search_type": "vision"} for n in new_names]
                    supabase.table("missing_searches").insert(inserts).execute()
            except Exception as e:
                logging.warning(f"Failed to log missing vision searches: {e}")

        return {
            "results": all_matches,
            "extracted_text": extracted_names,
            "not_found": not_found_names,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Always clean up temp file, even on error
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

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
    query = supabase.table("products").select("id, name, slug, category, composition, image_url, created_at, platform_product_links(id, price_history(id))")
    if category:
        query = query.eq("category", category)
    
    response = query.execute()
    products = response.data

    def get_priority(p):
        links = p.get("platform_product_links") or []
        if not links:
            return 0
        has_prices = any(len(link.get("price_history") or []) > 0 for link in links)
        if has_prices:
            return 2
        return 1

    # Sort by priority DESC (-priority), then alphabetically by name ASC
    sorted_products = sorted(products, key=lambda p: (-get_priority(p), p.get("name", "").lower()))
    
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
