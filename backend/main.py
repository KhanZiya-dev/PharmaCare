# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Depends, HTTPException, Query, Request, BackgroundTasks, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
import time
from supabase import create_client, Client
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import json
import logging
import asyncio
import tempfile
from scraper.zeno import fetch_zeno_price
from dotenv import load_dotenv

# Ensure backend/.env is properly loaded
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(_env_path if os.path.exists(_env_path) else None)

# ─── In-Memory TTL Cache ────────────────────────────────────────────
# Simple, zero-dependency cache. ~2KB per product entry means 500 products ≈ 1MB.
_cache: dict[str, tuple[float, any]] = {}  # key -> (expiry_timestamp, value)

def cache_get(key: str) -> any:
    """Return cached value if key exists and hasn't expired, else None."""
    entry = _cache.get(key)
    if entry is None:
        return None
    expiry, value = entry
    if time.time() > expiry:
        _cache.pop(key, None)
        return None
    return value

def cache_set(key: str, value: any, ttl: int = 300) -> None:
    """Store a value with TTL (seconds). Default 5 minutes."""
    _cache[key] = (time.time() + ttl, value)
    # Lazy eviction: purge expired entries when cache grows large
    if len(_cache) > 2000:
        now = time.time()
        expired = [k for k, (exp, _) in _cache.items() if now > exp]
        for k in expired:
            _cache.pop(k, None)

# ─── Rate Limiter ───────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Scheduler removed — use external cron (cron-job.org) hitting /cron/update-prices
    # This saves ~5-10% CPU on the 0.1 CPU Render instance.
    logging.info("PharmaCare API started. Use /cron/update-prices for scraper triggers.")
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
    Smart search with 5-min cache.
    """
    cache_key = f"search:{q.lower().strip()}:{category or ''}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    results = []

    # Try ranked RPC search first for products
    try:
        rpc_params = {"query": q}
        if category and category != 'lab_test':
            rpc_params["category_filter"] = category

        if category != 'lab_test':
            rpc_res = supabase.rpc("search_products_smart", rpc_params).execute()
            results.extend(rpc_res.data or [])
    except Exception:
        pass
        
    # Fallback to ilike if RPC returned nothing or failed
    if not results:
        if category == 'lab_test':
            query_b = supabase.table("lab_tests").select("id, name, slug, description, sample_type")
            response = query_b.ilike("name", f"%{q}%").limit(10).execute()
            for r in response.data or []:
                r['category'] = 'lab_test'
                r['composition'] = r.pop('description', '')
                results.append(r)
        else:
            query_b = supabase.table("products").select("id, name, slug, category, composition, image_url")
            if category:
                query_b = query_b.eq("category", category)
            response = query_b.ilike("name", f"%{q}%").limit(10).execute()
            results.extend(response.data or [])

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
            logging.warning(f"Failed to log missing search: {e}")

    cache_set(cache_key, results, ttl=300)  # 5 min
    return results

@app.get("/lab-tests")
@limiter.limit("60/minute")
def list_lab_tests(request: Request, limit: int = 40, supabase: Client = Depends(get_supabase)):
    """
    Fetch a list of lab tests with 10-min cache.
    """
    cache_key = f"lab_tests:all:{limit}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    query = supabase.table("lab_tests").select("id, name, slug, description, sample_type")
    response = query.order("name").limit(limit).execute()
    result = []
    for r in response.data or []:
        r['category'] = 'lab_test'
        r['composition'] = r.pop('description', '')
        result.append(r)
        
    cache_set(cache_key, result, ttl=600)  # 10 min
    return result

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
    except ValueError as e:
        # AI service quota/demand errors from vision.py
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Always clean up temp file, even on error
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

@app.get("/products")
@limiter.limit("60/minute")
def list_products(request: Request, category: str = None, limit: int = 40, supabase: Client = Depends(get_supabase)):
    """
    Fetch a list of products with 10-min cache.
    Optimized: lightweight query without heavy nested joins.
    """
    cache_key = f"products:{category or 'all'}:{limit}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    # Lightweight query — just product fields, no nested joins
    query = supabase.table("products").select("id, name, slug, category, composition, image_url")
    if category:
        query = query.eq("category", category)
    
    response = query.order("name").limit(limit).execute()
    result = response.data or []
        
    cache_set(cache_key, result, ttl=600)  # 10 min
    return result

@app.get("/product/{slug}")
@limiter.limit("60/minute")
async def get_product(request: Request, slug: str, supabase: Client = Depends(get_supabase)):
    """
    Fetch product data with 5-min cache, parallel DB queries, and cached Zeno API.
    """
    # ── Check full-response cache first ──
    cache_key = f"product:{slug}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    # 1. Fetch product details (must be first — need product ID for parallel queries)
    try:
        product_res = supabase.table("products").select("*").eq("slug", slug).single().execute()
        product = product_res.data
    except Exception:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    from datetime import datetime, timedelta, timezone
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

    # 2. Run remaining DB queries IN PARALLEL using asyncio.to_thread
    async def fetch_mappings():
        return supabase.table("platform_product_links").select(
            "id, affiliate_url, scrape_url, platforms(name, logo_url)"
        ).eq("product_id", product["id"]).execute()

    async def fetch_alternatives():
        if not product.get("composition"):
            return None
        try:
            return supabase.table("products").select(
                "id, name, slug, category, composition, image_url"
            ).eq("composition", product["composition"]).neq("id", product["id"]).limit(4).execute()
        except Exception:
            return None

    async def fetch_zeno_cached():
        """Fetch Zeno data with its own 15-min cache."""
        if product.get("category") == "lab_test":
            return None
        zeno_cache_key = f"zeno:{product['name']}"
        zeno_cached = cache_get(zeno_cache_key)
        if zeno_cached is not None:
            return zeno_cached
        try:
            result = await fetch_zeno_price(product["name"])
            cache_set(zeno_cache_key, result, ttl=900)  # 15 min
            return result
        except Exception:
            return None

    # Fire all three in parallel
    mappings_res, alt_res, zeno_data = await asyncio.gather(
        fetch_mappings(),
        fetch_alternatives(),
        fetch_zeno_cached(),
    )
    
    mappings = mappings_res.data if mappings_res else []
    alternatives = alt_res.data if alt_res else []
    
    # 3. Fetch price history (needs mapping_ids, so runs after mappings)
    mapping_ids = [m["id"] for m in mappings]
    history_data = []
    if mapping_ids:
        history_res = await asyncio.to_thread(
            lambda: supabase.table("price_history").select("*").in_("mapping_id", mapping_ids).gte("scraped_at", thirty_days_ago).order("scraped_at", desc=False).execute()
        )
        history_data = history_res.data
        
    for mapping in mappings:
        mapping["history"] = [h for h in history_data if h["mapping_id"] == mapping["id"]]
        if mapping["history"]:
            mapping["latest_price"] = mapping["history"][-1]
        else:
            mapping["latest_price"] = None

    # 4. Append Zeno data to mappings
    if zeno_data:
        now = datetime.now(timezone.utc)
        td_ago = now - timedelta(days=30)
        if zeno_data.get("price") and zeno_data.get("price") > 0:
            latest_price_obj = {
                "selling_price": zeno_data["price"],
                "mrp": zeno_data["mrp"],
                "in_stock": zeno_data["in_stock"],
                "is_restricted": False,
                "scraped_at": now.isoformat()
            }
            past_price_obj = {
                "selling_price": zeno_data["price"],
                "mrp": zeno_data["mrp"],
                "in_stock": zeno_data["in_stock"],
                "is_restricted": False,
                "scraped_at": td_ago.isoformat()
            }
            mappings.append({
                "id": "zeno_live",
                "affiliate_url": zeno_data["url"],
                "scrape_url": zeno_data["url"],
                "platforms": {
                    "name": "Zeno Health",
                    "logo_url": "https://d3pmeofo468e0p.cloudfront.net/zeno-app-v1/images/other/user_stats.svg"
                },
                "history": [past_price_obj, latest_price_obj],
                "latest_price": latest_price_obj
            })
        else:
            mappings.append({
                "id": "zeno_live",
                "affiliate_url": None,
                "scrape_url": "https://www.zeno.health",
                "platforms": {
                    "name": "Zeno Health",
                    "logo_url": "https://d3pmeofo468e0p.cloudfront.net/zeno-app-v1/images/other/user_stats.svg"
                },
                "history": [],
                "latest_price": None
            })
    
    response = {
        "product": product,
        "platforms": mappings,
        "alternatives": alternatives,
        "generics": zeno_data.get("generics", []) if zeno_data else []
    }
    
    cache_set(cache_key, response, ttl=300)  # 5 min
    return response

@app.get("/trends/variance")
def get_high_variance_trends(supabase: Client = Depends(get_supabase)):
    """
    Returns products with the highest price variance. Cached for 30 minutes (heavy query).
    """
    cached = cache_get("trends:variance")
    if cached is not None:
        return cached

    try:
        res = supabase.table("products").select(
            "id, name, slug, category, image_url, platform_product_links(id, price_history(mrp, selling_price, in_stock, is_restricted))"
        ).limit(100).execute()
        
        variances = []
        for p in res.data:
            prices = []
            has_restricted = False
            for m in p.get("platform_product_links", []):
                history = m.get("price_history", [])
                if history:
                    latest = history[0]
                    # Skip restricted/not-for-sale entries
                    if latest.get("is_restricted"):
                        has_restricted = True
                        continue
                    # Skip out-of-stock entries
                    if latest.get("in_stock") is False:
                        continue
                    sp = latest.get("selling_price")
                    if sp and sp > 0:
                        prices.append(sp)
            
            # Skip if all platforms are restricted
            if has_restricted and not prices:
                continue
            
            if len(prices) > 1:
                min_p = min(prices)
                max_p = max(prices)
                variance = max_p - min_p
                var_pct = (variance / min_p) * 100
                discount_pct = (variance / max_p) * 100
                
                # Filter out suspicious data:
                # - Lowest price should be at least ₹10 (not some glitch)
                # - Highest price should be under ₹50,000
                # - Variance shouldn't exceed 85% (likely a data error)
                if min_p < 10 or max_p > 50000 or var_pct > 85:
                    continue
                
                if var_pct > 0:
                    variances.append({
                        "id": p["id"],
                        "name": p["name"],
                        "slug": p["slug"],
                        "category": p["category"],
                        "image_url": p.get("image_url"),
                        "lowestPrice": min_p,
                        "highestPrice": max_p,
                        "variance_pct": round(var_pct, 2),
                        "discount_pct": round(discount_pct, 2),
                        "platformCount": len(prices)
                    })
        
        variances.sort(key=lambda x: x["variance_pct"], reverse=True)
        result = variances[:12]
        cache_set("trends:variance", result, ttl=1800)  # 30 min
        return result
        
    except Exception as e:
        logging.error(f"Error computing trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch trends")

@app.get("/redirect")
@limiter.limit("60/minute")
def redirect_to_platform(request: Request, mapping_id: str, supabase: Client = Depends(get_supabase)):
    """
    Redirects to the affiliate URL of the platform via HTTP 307.
    """
    if mapping_id == "zeno_live":
        return RedirectResponse(url="https://www.zeno.health", status_code=307)
        
    try:
        mapping_res = supabase.table("platform_product_links").select("affiliate_url, scrape_url").eq("id", mapping_id).single().execute()
        mapping_data = mapping_res.data
    except Exception:
        mapping_data = None
        
    if not mapping_data:
        try:
            mapping_res = supabase.table("platform_lab_test_links").select("affiliate_url, scrape_url").eq("id", mapping_id).single().execute()
            mapping_data = mapping_res.data
        except Exception:
            mapping_data = None
    
    if not mapping_data:
        raise HTTPException(status_code=404, detail="Mapping not found")
        
    target_url = mapping_data.get("affiliate_url") or mapping_data.get("scrape_url")
    if not target_url:
        raise HTTPException(status_code=404, detail="No redirect URL available")
    
    return RedirectResponse(url=target_url, status_code=307)

@app.get("/lab-test/{slug}")
@limiter.limit("60/minute")
def get_lab_test(request: Request, slug: str, supabase: Client = Depends(get_supabase)):
    """
    Fetch current prices and 30-day history data for a specific lab test.
    """
    # 1. Fetch lab test details
    try:
        test_res = supabase.table("lab_tests").select("*").eq("slug", slug).single().execute()
        lab_test = test_res.data
    except Exception:
        raise HTTPException(status_code=404, detail="Lab test not found")
    
    if not lab_test:
        raise HTTPException(status_code=404, detail="Lab test not found")
    
    # 2. Fetch platform mappings and latest prices
    mappings_res = supabase.table("platform_lab_test_links").select(
        "id, affiliate_url, scrape_url, platforms(name, logo_url)"
    ).eq("lab_test_id", lab_test["id"]).execute()
    
    mappings = mappings_res.data
    
    # 3. Fetch price history for these mappings for the last 30 days
    from datetime import datetime, timedelta, timezone
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    
    mapping_ids = [m["id"] for m in mappings]
    history_data = []
    
    if mapping_ids:
        history_res = supabase.table("lab_test_price_history").select("*").in_("mapping_id", mapping_ids).gte("scraped_at", thirty_days_ago).order("scraped_at", desc=False).execute()
        history_data = history_res.data
        
    for mapping in mappings:
        mapping["history"] = [h for h in history_data if h["mapping_id"] == mapping["id"]]
        if mapping["history"]:
            mapping["latest_price"] = mapping["history"][-1]
        else:
            mapping["latest_price"] = None
    
    # Append category for frontend consistency
    lab_test["category"] = "lab_test"
            
    return {
        "product": lab_test,
        "platforms": mappings,
        "alternatives": []
    }
