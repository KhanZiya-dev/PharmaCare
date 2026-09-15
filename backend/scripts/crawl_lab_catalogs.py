import os
import sys
import logging
import asyncio
from dotenv import load_dotenv
from supabase import create_client

from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load env
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(env_path)

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not supabase_url or not supabase_key:
    logger.error("Missing Supabase credentials.")
    sys.exit(1)

supabase = create_client(supabase_url, supabase_key)


async def crawl_metropolis(page):
    """
    Crawls Metropolis India for lab tests.
    """
    logger.info("Starting Metropolis Crawl...")
    tests = []
    
    try:
        # Metropolis lists tests under their tests directory or we can search
        # We will visit a common category page for tests
        await page.goto("https://www.metropolisindia.com/lab-tests", timeout=60000, wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)
        
        # Look for links
        links = await page.locator("a[href*='/lab-tests/']").all()
        for link in links:
            href = await link.get_attribute("href")
            text = await link.inner_text()
            if text:
                text = text.strip()
            
            if href and text and len(text) > 3 and "Book" not in text:
                url = href if href.startswith("http") else f"https://www.metropolisindia.com{href}"
                slug = text.lower().replace(" ", "-").replace("(", "").replace(")", "").replace("/", "-")
                tests.append({
                    "name": text,
                    "slug": slug,
                    "platform_name": "Metropolis",
                    "scrape_url": url,
                    "affiliate_url": url
                })
                if len(tests) >= 10:
                    break # Limit for POC
    except Exception as e:
        logger.error(f"Metropolis crawl failed: {e}")
        
    return tests

async def crawl_thyrocare(page):
    """
    Crawls Thyrocare for lab tests.
    """
    logger.info("Starting Thyrocare Crawl...")
    tests = []
    
    try:
        # Thyrocare lists tests
        await page.goto("https://www.thyrocare.com/wellness/tests", timeout=60000, wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)
        
        links = await page.locator("a[href*='/wellness/tests/']").all()
        for link in links:
            href = await link.get_attribute("href")
            text = await link.inner_text()
            if text:
                text = text.strip()
            
            if href and text and len(text) > 3:
                url = href if href.startswith("http") else f"https://www.thyrocare.com{href}"
                slug = text.lower().replace(" ", "-").replace("(", "").replace(")", "").replace("/", "-")
                tests.append({
                    "name": text,
                    "slug": slug,
                    "platform_name": "Thyrocare",
                    "scrape_url": url,
                    "affiliate_url": url
                })
                if len(tests) >= 10:
                    break # Limit for POC
    except Exception as e:
        logger.error(f"Thyrocare crawl failed: {e}")
        
    return tests

async def main():
    logger.info("Initializing Playwright...")
    async with async_playwright() as p:
        # We MUST run headless=False because Cloudflare blocks headless browsers
        # The user will need to solve the captcha if it appears.
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await stealth_async(page)
        
        all_tests = []
        
        # Crawl platforms
        all_tests.extend(await crawl_metropolis(page))
        await page.wait_for_timeout(2000)
        all_tests.extend(await crawl_thyrocare(page))
        
        await browser.close()
        
    logger.info(f"Crawled {len(all_tests)} tests. Inserting to database...")
    
    if not all_tests:
        logger.warning("No tests found to insert.")
        return

    # Fetch platform IDs
    platform_res = supabase.table("platforms").select("id, name").execute()
    platforms_map = {p["name"].lower(): p["id"] for p in platform_res.data}
    
    for test in all_tests:
        # 1. Insert or get Lab Test
        res = supabase.table("lab_tests").select("id").eq("slug", test["slug"]).execute()
        if res.data:
            lab_test_id = res.data[0]["id"]
        else:
            inserted = supabase.table("lab_tests").insert({
                "name": test["name"],
                "slug": test["slug"]
            }).execute()
            lab_test_id = inserted.data[0]["id"]
            
        # 2. Insert Platform Link
        p_name = test["platform_name"].lower()
        p_id = platforms_map.get(p_name)
        if not p_id:
            # Create platform if missing
            new_p = supabase.table("platforms").insert({"name": test["platform_name"]}).execute()
            p_id = new_p.data[0]["id"]
            platforms_map[p_name] = p_id
            
        # Check if link exists
        link_res = supabase.table("platform_lab_test_links").select("id").eq("lab_test_id", lab_test_id).eq("platform_id", p_id).execute()
        if not link_res.data:
            supabase.table("platform_lab_test_links").insert({
                "lab_test_id": lab_test_id,
                "platform_id": p_id,
                "scrape_url": test["scrape_url"],
                "affiliate_url": test["affiliate_url"]
            }).execute()

    logger.info("Successfully ingested lab tests into database.")

if __name__ == "__main__":
    asyncio.run(main())
