import os
import asyncio
import pandas as pd
import urllib.parse
from dotenv import load_dotenv
from supabase import create_client
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import logging
import sys

# Allow importing from scripts/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts"))
from platform_search import search_1mg_async, search_pharmeasy_async, search_apollo_async

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

file_path = r'C:\Users\Ziyaurrahman Khan\OneDrive\Desktop\Medicines_PharmEasy_1mg_Apollo_Links.xlsx'


async def search_and_save_validated(page, med_name, search_fn, platform_name, platform_id, product_id):
    """
    Search for a medicine using validated name-matching search functions.
    Only saves the link if the found product name actually matches.
    """
    try:
        found_url = await search_fn(page, med_name)
        if found_url:
            logger.info(f"  [{platform_name}] ✓ Validated: {found_url}")
            supabase.table("platform_product_links").insert({
                "product_id": product_id,
                "platform_id": platform_id,
                "scrape_url": found_url
            }).execute()
            return True
        else:
            logger.debug(f"  [{platform_name}] ✗ No valid match for '{med_name}'")
    except Exception as e:
        logger.error(f"  [{platform_name}] Error: {e}")
    return False


async def main():
    df = pd.read_excel(file_path, skiprows=3)
    
    platforms_res = supabase.table("platforms").select("id, name").execute()
    p_map = {p["name"].lower(): p["id"] for p in platforms_res.data}
    
    platform_1mg_id = None
    platform_apollo_id = None
    platform_pharmeasy_id = None
    for k, v in p_map.items():
        if "1mg" in k: platform_1mg_id = v
        if "apollo" in k: platform_apollo_id = v
        if "pharmeasy" in k: platform_pharmeasy_id = v
    
    products_res = supabase.table("products").select("id, name").execute()
    product_map = {p["name"].lower().strip(): p["id"] for p in products_res.data}
    
    # Load all existing links to avoid redundant searches
    all_links_res = supabase.table("platform_product_links").select("product_id, platform_id").execute()
    from collections import defaultdict
    existing_links = defaultdict(set)
    for row in all_links_res.data:
        existing_links[row["product_id"]].add(row["platform_id"])
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        
        # Create 3 pages for parallel searching
        page_1mg = await context.new_page()
        page_apollo = await context.new_page()
        page_pharm = await context.new_page()
        
        await stealth_async(page_1mg)
        await stealth_async(page_apollo)
        await stealth_async(page_pharm)
        
        logger.info(f"Starting to process {len(df)} medicines...")
        for index, row in df.iterrows():
            med_name = str(row['Medicine Name']).strip()
            if med_name.lower() not in product_map:
                continue
                
            product_id = product_map[med_name.lower()]
            
            has_1mg = platform_1mg_id in existing_links.get(product_id, set())
            has_apollo = platform_apollo_id in existing_links.get(product_id, set())
            has_pharm = platform_pharmeasy_id in existing_links.get(product_id, set())
            
            if has_1mg and has_apollo and has_pharm:
                logger.info(f"[{index+1}/{len(df)}] Skipping {med_name} (all links present)")
                continue
            
            logger.info(f"[{index+1}/{len(df)}] Searching for: {med_name}")
            
            tasks = []
            if not has_1mg:
                tasks.append(search_and_save_validated(
                    page_1mg, med_name, search_1mg_async,
                    "1mg", platform_1mg_id, product_id
                ))
            if not has_apollo:
                tasks.append(search_and_save_validated(
                    page_apollo, med_name, search_apollo_async,
                    "Apollo", platform_apollo_id, product_id
                ))
            if not has_pharm:
                tasks.append(search_and_save_validated(
                    page_pharm, med_name, search_pharmeasy_async,
                    "PharmEasy", platform_pharmeasy_id, product_id
                ))
                
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for r in results:
                    if isinstance(r, Exception):
                        logger.error(f"Error in parallel task: {r}")
                
        await browser.close()
        logger.info(f"Finished!")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())

