import asyncio
import os
import logging
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from scraper.lab_test_scraper import GenericLabTestScraper

logging.basicConfig(level=logging.INFO)

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

async def main():
    scraper = GenericLabTestScraper(platform_id=4, platform_name="Agilus Diagnostics")
    url = "https://agilusdiagnostics.com/test/delhi/100000216/cbc-complete-blood-count-test"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        await stealth_async(page)
        
        logging.info(f"Testing scraper on URL: {url}")
        
        data = await scraper.scrape_page(page, url)
        if data:
            logging.info(f"SUCCESS: Extracted Data: {data}")
        else:
            logging.info("FAILED: No data extracted.")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
