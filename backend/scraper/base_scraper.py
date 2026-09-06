from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
import logging
import random
import time
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseScraper:
    def __init__(self, platform_id: int, platform_name: str):
        self.platform_id = platform_id
        self.platform_name = platform_name
        self.proxy_url = os.getenv("PROXY_URL")  # Optional: rotating proxy URL

    def _random_delay(self, min_sec: float = 3.5, max_sec: float = 7.2):
        """Add a randomized delay between requests to avoid IP bans."""
        delay = random.uniform(min_sec, max_sec)
        logger.info(f"Waiting {delay:.1f}s before next action...")
        time.sleep(delay)

    def scrape(self, url: str):
        """
        Base method to be overridden by child classes.
        Initializes Playwright with stealth to bypass anti-bot mechanisms.
        """
        logger.info(f"Starting scrape for {self.platform_name} at {url}")
        
        with sync_playwright() as p:
            # Configure browser launch options
            launch_options = {"headless": True}
            
            # Add proxy if configured
            if self.proxy_url:
                launch_options["proxy"] = {"server": self.proxy_url}
                logger.info(f"Using proxy: {self.proxy_url}")

            browser = p.chromium.launch(**launch_options)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            # Apply stealth to avoid detection
            stealth_sync(page)
            
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(5000) # Give SPAs time to render pricing
                return self.extract_data(page)
            except Exception as e:
                logger.error(f"Failed to scrape {url}: {str(e)}")
                return None
            finally:
                browser.close()

    def extract_data(self, page):
        """
        Override this method in specific platform scrapers (e.g., OneMgScraper, PharmEasyScraper)
        to extract MRP, Selling Price, and Stock Status using CSS selectors.
        """
        raise NotImplementedError("Subclasses must implement extract_data")
