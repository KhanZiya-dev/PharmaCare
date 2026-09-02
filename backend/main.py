# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="PharmaCare API", version="1.0.0")

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

# Supabase Client setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def get_supabase() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise HTTPException(status_code=500, detail="Supabase credentials not configured.")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@app.get("/")
def read_root():
    return {"message": "Welcome to PharmaCare API"}

@app.get("/search")
def search_products(q: str = Query(..., min_length=2), supabase: Client = Depends(get_supabase)):
    """
    Fuzzy search implementation for products.
    """
    # Uses Supabase's text search (which leverages pg_trgm in the background if configured via RPC, 
    # or ilike for basic operations)
    response = supabase.table("products").select("id, name, slug, category, image_url").ilike("name", f"%{q}%").limit(10).execute()
    return response.data

@app.get("/product/{slug}")
def get_product(slug: str, supabase: Client = Depends(get_supabase)):
    """
    Fetch current prices and 30-day history data for a specific product.
    """
    # 1. Fetch product details
    product_res = supabase.table("products").select("*").eq("slug", slug).single().execute()
    if not product_res.data:
        raise HTTPException(status_code=404, detail="Product not found")
        
    product = product_res.data
    
    # 2. Fetch platform mappings and latest prices
    mappings_res = supabase.table("platform_product_links").select(
        "id, affiliate_url, platforms(name, logo_url)"
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
    
    return {
        "product": product,
        "platforms": mappings
    }

@app.get("/redirect")
def redirect_to_platform(mapping_id: str, supabase: Client = Depends(get_supabase)):
    """
    Redirects to the affiliate URL of the platform.
    """
    mapping_res = supabase.table("platform_product_links").select("affiliate_url, scrape_url").eq("id", mapping_id).single().execute()
    if not mapping_res.data:
        raise HTTPException(status_code=404, detail="Mapping not found")
        
    target_url = mapping_res.data.get("affiliate_url") or mapping_res.data.get("scrape_url")
    return {"redirect_url": target_url} # Frontend will handle the actual redirection
