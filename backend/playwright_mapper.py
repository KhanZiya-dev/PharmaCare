import os
import logging
import asyncio
from dotenv import load_dotenv
from supabase import create_client
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import urllib.parse
from fake_useragent import UserAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv("d:/BSc.CS/Sem5/Pharmacare/backend/.env")

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

platforms_res = supabase.table("platforms").select("*").execute()
platforms = {p["name"].lower(): p["id"] for p in platforms_res.data}
ua = UserAgent(browsers=['chrome', 'edge'])

async def search_1mg(page, medicine_name):
    query = urllib.parse.quote(medicine_name)
    url = f"https://www.1mg.com/search/all?name={query}"
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        locator = page.locator('a[href*="/drugs/"]').first
        if await locator.count() > 0:
            href = await locator.get_attribute('href')
            if href:
                return "https://www.1mg.com" + href if href.startswith('/') else href
    except Exception:
        pass
    return None

async def search_pharmeasy(page, medicine_name):
    query = urllib.parse.quote(medicine_name)
    url = f"https://pharmeasy.in/search/all?name={query}"
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        locator = page.locator('a[href*="/online-medicine-order/"]').first
        if await locator.count() > 0:
            href = await locator.get_attribute('href')
            if href:
                return "https://pharmeasy.in" + href if href.startswith('/') else href
    except Exception:
        pass
    return None

async def search_apollo(page, medicine_name):
    query = urllib.parse.quote(medicine_name)
    url = f"https://www.apollopharmacy.in/search-medicines/{query}"
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        locator = page.locator('a[href*="/medicine/"]').first
        if await locator.count() > 0:
            href = await locator.get_attribute('href')
            if href:
                return "https://www.apollopharmacy.in" + href if href.startswith('/') else href
    except Exception:
        pass
    return None

async def worker(name, queue, browser, results_list):
    logger.info(f"Worker {name} started")
    context = await browser.new_context(user_agent=ua.random, viewport={"width": 1920, "height": 1080})
    
    while True:
        try:
            prod = await queue.get()
            page = await context.new_page()
            await stealth_async(page)
            
            logger.info(f"Worker {name} searching for: {prod['name']}")
            links_found = 0
            
            # 1mg
            link_1mg = await search_1mg(page, prod['name'])
            if link_1mg:
                pid = next((v for k, v in platforms.items() if "1mg" in k), None)
                if pid:
                    results_list.append({"product_id": prod["id"], "platform_id": pid, "scrape_url": link_1mg})
                    links_found += 1
                    
            # PharmEasy
            link_pe = await search_pharmeasy(page, prod['name'])
            if link_pe:
                pid = next((v for k, v in platforms.items() if "pharmeasy" in k), None)
                if pid:
                    results_list.append({"product_id": prod["id"], "platform_id": pid, "scrape_url": link_pe})
                    links_found += 1
                    
            # Apollo
            link_apollo = await search_apollo(page, prod['name'])
            if link_apollo:
                pid = next((v for k, v in platforms.items() if "apollo" in k), None)
                if pid:
                    results_list.append({"product_id": prod["id"], "platform_id": pid, "scrape_url": link_apollo})
                    links_found += 1

            logger.info(f"Worker {name} found {links_found} links for {prod['name']}")
            await page.close()
            queue.task_done()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Worker {name} error: {e}")
            queue.task_done()
    
    await context.close()

async def map_medicines():
    products_res = supabase.table("products").select("id, name").execute()
    products = products_res.data
    links_res = supabase.table("platform_product_links").select("product_id").execute()
    linked_product_ids = {link["product_id"] for link in links_res.data}

    unlinked_products = [p for p in products if p["id"] not in linked_product_ids]
    logger.info(f"Found {len(unlinked_products)} unlinked products.")

    if not unlinked_products:
        return

    queue = asyncio.Queue()
    for p in unlinked_products:
        queue.put_nowait(p)

    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        num_workers = 5
        tasks = []
        for i in range(num_workers):
            task = asyncio.create_task(worker(f"W-{i+1}", queue, browser, results))
            tasks.append(task)
            
        await queue.join()
        
        for task in tasks:
            task.cancel()
            
        await asyncio.gather(*tasks, return_exceptions=True)
        await browser.close()
    
    logger.info(f"Finished mapping. Acquired {len(results)} new platform links.")
    
    if results:
        chunk_size = 100
        for i in range(0, len(results), chunk_size):
            chunk = results[i:i+chunk_size]
            try:
                supabase.table("platform_product_links").insert(chunk).execute()
                logger.info(f"Batch inserted {len(chunk)} links.")
            except Exception as e:
                logger.error(f"Failed batch insert: {e}")
        
if __name__ == "__main__":
    asyncio.run(map_medicines())
