import os
import logging
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime, timezone
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from fake_useragent import UserAgent

from .onemg_scraper import OneMgScraper
from .pharmeasy_scraper import PharmEasyScraper
from .apollo_scraper import ApolloScraper
from .lab_test_scraper import GenericLabTestScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Generate realistic user agents
ua = UserAgent(browsers=['chrome', 'edge', 'safari'])

def get_supabase_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise ValueError("Missing Supabase credentials in .env file.")
    return create_client(url, key)

def get_scraper_for_platform(platform_name: str, platform_id: int):
    name = platform_name.lower()
    if "1mg" in name:
        return OneMgScraper(platform_id)
    elif "pharmeasy" in name:
        return PharmEasyScraper(platform_id)
    elif "apollo" in name:
        return ApolloScraper(platform_id)
    elif "agilus" in name or "metropolis" in name or "general diagnostics" in name or "thyrocare" in name or "lal pathlabs" in name:
        return GenericLabTestScraper(platform_id, platform_name)
    else:
        logger.warning(f"No specific scraper found for platform: {platform_name}")
        return None

async def worker(name, queue: asyncio.Queue, browser, results_list):
    """
    Worker task that pulls URLs from the queue and scrapes them using a persistent browser context.
    """
    logger.info(f"Worker {name} started")
    
    # Create a fresh context for this worker to isolate cookies/sessions slightly and use a unique User-Agent
    context = await browser.new_context(
        user_agent=ua.random,
        viewport={"width": 1920, "height": 1080}
    )
    
    while True:
        try:
            link = await queue.get()
            
            link_id = link.get("id")
            scrape_url = link.get("scrape_url")
            platform = link.get("platforms")
            platform_id = platform.get("id")
            platform_name = platform.get("name")
            link_type = link.get("_link_type")
            
            scraper = get_scraper_for_platform(platform_name, platform_id)
            if scraper:
                page = await context.new_page()
                await stealth_async(page)
                
                # Jitter delay before request to mimic human speed and avoid bursting
                await scraper._random_delay(1.5, 4.0) 
                
                data = await scraper.scrape_page(page, scrape_url)
                
                if data and (data.get("selling_price") or data.get("is_restricted")):
                    now = datetime.now(timezone.utc).isoformat()
                    
                    mrp = data.get("mrp") or data.get("selling_price") or 0
                    selling = data.get("selling_price") or 0
                    
                    # ── Post-scrape validation ──────────────────────────
                    
                    # Fix 1: If selling > MRP, swap them (common extraction error)
                    if selling > 0 and mrp > 0 and selling > mrp:
                        logger.warning(f"Worker {name}: Selling ({selling}) > MRP ({mrp}) for {scrape_url}, swapping.")
                        selling, mrp = mrp, selling
                    
                    # Fix 2: Reject obviously wrong prices
                    if selling > 0 and (selling < 1 or selling > 100000):
                        logger.warning(f"Worker {name}: Suspicious selling price {selling} for {scrape_url}, skipping.")
                        selling = 0
                    if mrp > 0 and (mrp < 1 or mrp > 100000):
                        logger.warning(f"Worker {name}: Suspicious MRP {mrp} for {scrape_url}, resetting to selling.")
                        mrp = selling
                    
                    # Fix 3: Calculate discount safely
                    discount_pct = round(((mrp - selling) / mrp) * 100, 2) if mrp and mrp > 0 and selling > 0 else 0
                    # Clamp discount to reasonable range (0-90%)
                    if discount_pct < 0:
                        discount_pct = 0
                    elif discount_pct > 90:
                        logger.warning(f"Worker {name}: Unusual discount {discount_pct}% for {scrape_url}")
                    
                    record = {
                        "mapping_id": link_id,
                        "selling_price": selling if selling > 0 else None,
                        "mrp": mrp if mrp > 0 else None,
                        "in_stock": data.get("in_stock", True),
                        "is_restricted": data.get("is_restricted", False),
                        "discount_pct": discount_pct,
                        "scraped_at": now,
                        "_link_type": link_type,
                    }
                    
                    product_id = link.get("product_id")
                    if data.get("image_url") and product_id and link_type == "product":
                        record["_image_url"] = data.get("image_url")
                        record["_product_id"] = product_id
                        
                    results_list.append(record)
                    logger.info(f"Worker {name}: Successfully scraped {platform_name} price for link {link_id}")
                else:
                    logger.warning(f"Worker {name}: Failed to get data for {scrape_url}")
                
                await page.close()
            
            queue.task_done()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Worker {name} encountered error: {e}")
            queue.task_done()
            
    await context.close()


async def run_engine_async():
    logger.info("Initializing Async Scraper Engine...")
    try:
        supabase = get_supabase_client()
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {e}", exc_info=True)
        return

    logger.info("Fetching products without images...")
    no_image_products_res = supabase.table("products").select("id").is_("image_url", "null").execute()
    products_needing_image = {p["id"] for p in no_image_products_res.data}
    logger.info(f"Found {len(products_needing_image)} products needing images.")

    logger.info("Fetching platform product links...")
    links_res = supabase.table("platform_product_links").select(
        "id, scrape_url, product_id, platforms(id, name)"
    ).execute()
    product_links = links_res.data or []

    logger.info("Fetching platform lab test links...")
    lab_links_res = supabase.table("platform_lab_test_links").select(
        "id, scrape_url, lab_test_id, platforms(id, name)"
    ).execute()
    lab_links = lab_links_res.data or []

    all_links = []
    for link in product_links:
        link["_link_type"] = "product"
        all_links.append(link)
    for link in lab_links:
        link["_link_type"] = "lab_test"
        all_links.append(link)

    if not all_links:
        logger.warning("No active links found to scrape.")
        return

    logger.info(f"Found {len(all_links)} links to scrape.")

    queue = asyncio.Queue()
    for link in all_links:
        if link.get("scrape_url") and link.get("platforms"):
            queue.put_nowait(link)

    results = []
    
    proxy_url = os.getenv("PROXY_URL")
    launch_options = {"headless": True}
    if proxy_url:
        launch_options["proxy"] = {"server": proxy_url}
        logger.info(f"Using proxy: {proxy_url}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(**launch_options)
        
        # Spawn 5 concurrent workers
        num_workers = 5
        tasks = []
        for i in range(num_workers):
            task = asyncio.create_task(worker(f"W-{i+1}", queue, browser, results))
            tasks.append(task)
            
        # Wait until queue is completely processed
        await queue.join()
        
        # Cancel workers now that queue is empty
        for task in tasks:
            task.cancel()
            
        # Wait until all worker tasks have been cancelled
        await asyncio.gather(*tasks, return_exceptions=True)
        await browser.close()
        
    logger.info(f"Scraping phase finished. Acquired {len(results)} successful results. Batch updating database...")
    
    if results:
        # Collect image updates and clean up results for history tables
        image_updates = {}
        product_results = []
        lab_test_results = []
        
        for res in results:
            if "_image_url" in res and res.get("_product_id") in products_needing_image:
                image_updates[res["_product_id"]] = res["_image_url"]
            
            link_type = res.get("_link_type")
            cleaned_res = {k: v for k, v in res.items() if not k.startswith("_")}
            
            if link_type == "product":
                product_results.append(cleaned_res)
            elif link_type == "lab_test":
                lab_test_results.append(cleaned_res)
            
        # Batch update product images
        if image_updates:
            logger.info(f"Updating images for {len(image_updates)} products...")
            for prod_id, img_url in image_updates.items():
                try:
                    supabase.table("products").update({"image_url": img_url}).eq("id", prod_id).execute()
                except Exception as e:
                    logger.error(f"Failed to update image for product {prod_id}: {e}")
            logger.info("Product images updated successfully.")
            
        # Batch insert price history for products
        chunk_size = 100
        for i in range(0, len(product_results), chunk_size):
            chunk = product_results[i:i+chunk_size]
            try:
                supabase.table("price_history").insert(chunk).execute()
                logger.info(f"Batch inserted {len(chunk)} product price history records.")
            except Exception as e:
                logger.error(f"Batch insert product history failed: {e}")

        # Batch insert price history for lab tests
        for i in range(0, len(lab_test_results), chunk_size):
            chunk = lab_test_results[i:i+chunk_size]
            try:
                supabase.table("lab_test_price_history").insert(chunk).execute()
                logger.info(f"Batch inserted {len(chunk)} lab test price history records.")
            except Exception as e:
                logger.error(f"Batch insert lab test history failed: {e}")
                
        # Update last_scraped timestamps
        now = datetime.now(timezone.utc).isoformat()
        product_mapping_ids = [res["mapping_id"] for res in results if res.get("_link_type") == "product"]
        lab_test_mapping_ids = [res["mapping_id"] for res in results if res.get("_link_type") == "lab_test"]
        
        if product_mapping_ids:
            try:
                for i in range(0, len(product_mapping_ids), chunk_size):
                    chunk_ids = product_mapping_ids[i:i+chunk_size]
                    supabase.table("platform_product_links").update({"last_scraped": now}).in_("id", chunk_ids).execute()
            except Exception as e:
                logger.error(f"Failed to batch update product last_scraped: {e}")

        if lab_test_mapping_ids:
            try:
                for i in range(0, len(lab_test_mapping_ids), chunk_size):
                    chunk_ids = lab_test_mapping_ids[i:i+chunk_size]
                    supabase.table("platform_lab_test_links").update({"last_scraped": now}).in_("id", chunk_ids).execute()
            except Exception as e:
                logger.error(f"Failed to batch update lab test last_scraped: {e}")
                
    logger.info("Async Scraper Engine run complete.")


def run_engine():
    """Wrapper to run the async engine synchronously (e.g. from FastAPI BackgroundTasks)"""
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_engine_async())
    finally:
        loop.close()

if __name__ == "__main__":
    run_engine()
