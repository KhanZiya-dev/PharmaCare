import os
import logging
import asyncio
import random
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

# ═══════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════
DELAY_MIN = 5.0          # Min seconds between requests to same platform
DELAY_MAX = 8.0          # Max seconds between requests to same platform
RETRY_DELAY_MIN = 15.0   # Min cooldown before retrying a failed scrape
RETRY_DELAY_MAX = 30.0   # Max cooldown before retrying a failed scrape
BLOCK_COOLDOWN = 45.0    # Extra cooldown if block/captcha detected
CONTEXT_ROTATE_EVERY = 50  # Rotate browser context every N requests
MAX_RETRIES = 1          # Number of retries per failed URL


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


def classify_platform(platform_name: str) -> str:
    """Map a platform name to a canonical key for grouping."""
    name = platform_name.lower()
    if "1mg" in name:
        return "1mg"
    elif "pharmeasy" in name:
        return "pharmeasy"
    elif "apollo" in name:
        return "apollo"
    else:
        return "other"


async def detect_block(page) -> bool:
    """
    Detect if the page is showing a captcha or block page instead of product content.
    Returns True if blocked.
    """
    try:
        # Check for common captcha/block signals
        page_title = await page.title()
        title_lower = (page_title or "").lower()
        
        block_title_signals = [
            "captcha", "blocked", "access denied", "403 forbidden",
            "just a moment", "checking your browser", "attention required",
            "are you a robot", "bot detection",
        ]
        for signal in block_title_signals:
            if signal in title_lower:
                logger.warning(f"Block detected via title: '{page_title}'")
                return True
        
        # Check for Cloudflare challenge or reCAPTCHA iframe
        cf_challenge = await page.locator("#challenge-form, .cf-browser-verification, iframe[src*='recaptcha'], iframe[src*='captcha']").count()
        if cf_challenge > 0:
            logger.warning("Block detected: Cloudflare challenge or CAPTCHA iframe found")
            return True
        
        # Check if page body is suspiciously empty (< 500 chars)
        try:
            body_text = await page.inner_text("body", timeout=3000)
            if len(body_text.strip()) < 200:
                logger.warning(f"Block suspected: page body too short ({len(body_text.strip())} chars)")
                return True
        except Exception:
            pass
            
    except Exception as e:
        logger.debug(f"Block detection error: {e}")
    
    return False


async def platform_worker(
    worker_name: str,
    links: list,
    browser,
    results_list: list,
    products_needing_image: set,
):
    """
    Dedicated worker for a single platform. Processes its URLs sequentially
    with human-like delays. Retries failed scrapes once after a cooldown.
    
    This ensures we NEVER send 2+ simultaneous requests to the same website.
    """
    if not links:
        return
    
    platform_name = links[0].get("platforms", {}).get("name", worker_name)
    logger.info(f"Worker [{worker_name}] starting with {len(links)} URLs for {platform_name}")
    
    # Shuffle to avoid predictable order
    random.shuffle(links)
    
    # Track failed URLs for retry
    failed_links = []
    
    # Create initial browser context
    context = await browser.new_context(
        user_agent=ua.random,
        viewport={"width": 1920, "height": 1080}
    )
    request_count = 0
    
    async def process_link(link, is_retry=False):
        nonlocal context, request_count
        
        link_id = link.get("id")
        scrape_url = link.get("scrape_url")
        platform = link.get("platforms")
        platform_id = platform.get("id")
        p_name = platform.get("name")
        link_type = link.get("_link_type")
        
        scraper = get_scraper_for_platform(p_name, platform_id)
        if not scraper:
            return False
        
        # Rotate context every N requests (fresh cookies + UA)
        request_count += 1
        if request_count % CONTEXT_ROTATE_EVERY == 0:
            logger.info(f"Worker [{worker_name}]: Rotating browser context after {request_count} requests")
            await context.close()
            context = await browser.new_context(
                user_agent=ua.random,
                viewport={"width": 1920, "height": 1080}
            )
        
        page = await context.new_page()
        await stealth_async(page)
        
        try:
            # Human-like delay before request
            delay = random.uniform(DELAY_MIN, DELAY_MAX)
            if is_retry:
                delay = random.uniform(RETRY_DELAY_MIN, RETRY_DELAY_MAX)
            await asyncio.sleep(delay)
            
            data = await scraper.scrape_page(page, scrape_url)
            
            # Check for blocking
            if not data or (not data.get("selling_price") and not data.get("is_restricted")):
                is_blocked = await detect_block(page)
                if is_blocked:
                    logger.warning(f"Worker [{worker_name}]: BLOCKED on {scrape_url}, cooling down {BLOCK_COOLDOWN}s")
                    await asyncio.sleep(BLOCK_COOLDOWN)
                    # Also rotate context after a block
                    await context.close()
                    context = await browser.new_context(
                        user_agent=ua.random,
                        viewport={"width": 1920, "height": 1080}
                    )
                return False
            
            # ── Post-scrape validation ──
            mrp = data.get("mrp") or data.get("selling_price") or 0
            selling = data.get("selling_price") or 0
            
            if selling > 0 and mrp > 0 and selling > mrp:
                logger.warning(f"Worker [{worker_name}]: Selling ({selling}) > MRP ({mrp}) for {scrape_url}, swapping.")
                selling, mrp = mrp, selling
            
            if selling > 0 and (selling < 1 or selling > 100000):
                logger.warning(f"Worker [{worker_name}]: Suspicious selling price {selling} for {scrape_url}, skipping.")
                selling = 0
            if mrp > 0 and (mrp < 1 or mrp > 100000):
                logger.warning(f"Worker [{worker_name}]: Suspicious MRP {mrp} for {scrape_url}, resetting to selling.")
                mrp = selling
            
            discount_pct = round(((mrp - selling) / mrp) * 100, 2) if mrp and mrp > 0 and selling > 0 else 0
            if discount_pct < 0:
                discount_pct = 0
            elif discount_pct > 90:
                logger.warning(f"Worker [{worker_name}]: Unusual discount {discount_pct}% for {scrape_url}")
            
            now = datetime.now(timezone.utc).isoformat()
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
            retry_tag = " (retry)" if is_retry else ""
            logger.info(f"Worker [{worker_name}]: ✅ Scraped {p_name} price for {link_id}{retry_tag}")
            return True
            
        except Exception as e:
            logger.error(f"Worker [{worker_name}]: Error scraping {scrape_url}: {e}")
            return False
        finally:
            await page.close()
    
    # ── Pass 1: Process all links ──
    for idx, link in enumerate(links, 1):
        prefix = f"[{idx}/{len(links)}]"
        scrape_url = link.get("scrape_url", "???")
        logger.info(f"Worker [{worker_name}] {prefix} Scraping: {scrape_url}")
        
        success = await process_link(link)
        if not success:
            failed_links.append(link)
    
    # ── Pass 2: Retry failed links once ──
    if failed_links:
        logger.info(f"Worker [{worker_name}]: Retrying {len(failed_links)} failed URLs after cooldown...")
        # Extra cooldown before retry pass
        await asyncio.sleep(random.uniform(30, 60))
        
        # Rotate context for fresh start
        await context.close()
        context = await browser.new_context(
            user_agent=ua.random,
            viewport={"width": 1920, "height": 1080}
        )
        
        retry_success = 0
        for idx, link in enumerate(failed_links, 1):
            prefix = f"[RETRY {idx}/{len(failed_links)}]"
            scrape_url = link.get("scrape_url", "???")
            logger.info(f"Worker [{worker_name}] {prefix} Retrying: {scrape_url}")
            
            success = await process_link(link, is_retry=True)
            if success:
                retry_success += 1
        
        logger.info(f"Worker [{worker_name}]: Retry pass recovered {retry_success}/{len(failed_links)} URLs")
    
    await context.close()
    logger.info(f"Worker [{worker_name}]: Finished. Processed {len(links)} URLs, "
                f"{len(links) - len(failed_links)} succeeded on first pass.")


async def run_engine_async():
    logger.info("Initializing Anti-Block Scraper Engine v2...")
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

    # ── Group links by platform ──
    platform_groups = {}
    for link in all_links:
        if not link.get("scrape_url") or not link.get("platforms"):
            continue
        platform_key = classify_platform(link["platforms"].get("name", ""))
        if platform_key not in platform_groups:
            platform_groups[platform_key] = []
        platform_groups[platform_key].append(link)
    
    for key, links in platform_groups.items():
        logger.info(f"Platform '{key}': {len(links)} URLs to scrape")

    results = []
    
    proxy_url = os.getenv("PROXY_URL")
    launch_options = {"headless": True}
    if proxy_url:
        launch_options["proxy"] = {"server": proxy_url}
        logger.info(f"Using proxy: {proxy_url}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(**launch_options)
        
        # Spawn one dedicated worker per platform — all run in parallel
        # but each worker processes its own URLs SEQUENTIALLY
        worker_tasks = []
        for platform_key, links in platform_groups.items():
            task = asyncio.create_task(
                platform_worker(
                    worker_name=platform_key,
                    links=links,
                    browser=browser,
                    results_list=results,
                    products_needing_image=products_needing_image,
                )
            )
            worker_tasks.append(task)
        
        # Wait for ALL platform workers to complete
        await asyncio.gather(*worker_tasks, return_exceptions=True)
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
                
    logger.info("Anti-Block Scraper Engine v2 run complete.")


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
