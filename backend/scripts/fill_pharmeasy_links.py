"""
Fill missing PharmEasy links for all products.

Uses async Playwright to search pharmeasy.in for each product
missing a PharmEasy mapping, validates the name match, and inserts
the link into platform_product_links.

Usage:
    cd backend
    python scripts/fill_pharmeasy_links.py
"""
import os
import sys
import asyncio
import logging
from dotenv import load_dotenv
from supabase import create_client
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from platform_search import search_pharmeasy_async

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

PHARMEASY_PLATFORM_ID = 2
BATCH_PAUSE = 3.0       # Seconds between requests
CONTEXT_ROTATE = 25      # Rotate browser context every N requests
PROGRESS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pharmeasy_fill_progress.json")


def load_progress():
    """Load set of already-processed product IDs to allow resuming."""
    import json
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_progress(processed: set):
    import json
    with open(PROGRESS_FILE, "w") as f:
        json.dump(list(processed), f)


async def main():
    # 1. Get all products missing PharmEasy links
    all_products = supabase.table("products").select("id, name").order("name").execute()
    pharmeasy_links = supabase.table("platform_product_links").select("product_id").eq(
        "platform_id", PHARMEASY_PLATFORM_ID
    ).execute()
    linked_ids = {l["product_id"] for l in pharmeasy_links.data}
    
    missing = [p for p in all_products.data if p["id"] not in linked_ids]
    
    # Filter out already-processed (allows resuming)
    processed = load_progress()
    to_process = [p for p in missing if p["id"] not in processed]
    
    logger.info(f"Total products: {len(all_products.data)}")
    logger.info(f"Already linked to PharmEasy: {len(linked_ids)}")
    logger.info(f"Missing PharmEasy link: {len(missing)}")
    logger.info(f"Already processed (from prev run): {len(processed)}")
    logger.info(f"Remaining to search: {len(to_process)}")
    
    if not to_process:
        logger.info("Nothing to do!")
        return
    
    # Shuffle to avoid predictable patterns
    random.shuffle(to_process)
    
    found_count = 0
    not_found_count = 0
    error_count = 0
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        await stealth_async(page)
        
        for idx, product in enumerate(to_process, 1):
            prod_id = product["id"]
            prod_name = product["name"]
            
            logger.info(f"[{idx}/{len(to_process)}] Searching PharmEasy for: {prod_name}")
            
            try:
                found_url = await search_pharmeasy_async(page, prod_name)
                
                if found_url:
                    # Insert into DB
                    supabase.table("platform_product_links").insert({
                        "product_id": prod_id,
                        "platform_id": PHARMEASY_PLATFORM_ID,
                        "scrape_url": found_url,
                    }).execute()
                    found_count += 1
                    logger.info(f"  -> FOUND & SAVED: {found_url}")
                else:
                    not_found_count += 1
                    logger.info(f"  -> Not found on PharmEasy")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"  -> Error: {e}")
            
            # Mark as processed (regardless of result)
            processed.add(prod_id)
            
            # Save progress every 5 products
            if idx % 5 == 0:
                save_progress(processed)
            
            # Rotate context periodically
            if idx % CONTEXT_ROTATE == 0:
                logger.info(f"  Rotating browser context...")
                await page.close()
                await context.close()
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080}
                )
                page = await context.new_page()
                await stealth_async(page)
            
            # Human-like delay
            await asyncio.sleep(random.uniform(BATCH_PAUSE, BATCH_PAUSE + 2.0))
        
        await browser.close()
    
    # Final save
    save_progress(processed)
    
    logger.info("=" * 60)
    logger.info(f"DONE! Results:")
    logger.info(f"  Found & saved: {found_count}")
    logger.info(f"  Not found:     {not_found_count}")
    logger.info(f"  Errors:        {error_count}")
    logger.info(f"  Total:         {found_count + not_found_count + error_count}")
    logger.info("=" * 60)


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
