from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
import logging
import random
import time
import re
import json
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

    # ── Shared extraction utilities ──────────────────────────────────────

    def _extract_json_ld(self, page) -> dict | None:
        """
        Extract price data from JSON-LD (schema.org Product) structured data.
        This is the most reliable method because sites embed it for SEO and it
        rarely changes format, unlike CSS class names.
        """
        try:
            scripts = page.locator('script[type="application/ld+json"]').all()
            for script in scripts:
                try:
                    raw = script.inner_text(timeout=3000)
                    data = json.loads(raw)

                    # Handle both single objects and arrays
                    items = data if isinstance(data, list) else [data]

                    for item in items:
                        product = self._find_product_in_jsonld(item)
                        if product:
                            return self._parse_product_jsonld(product)
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f"JSON-LD extraction failed: {e}")
        return None

    def _find_product_in_jsonld(self, obj: dict) -> dict | None:
        """Recursively search for a Product schema object."""
        if not isinstance(obj, dict):
            return None
        
        obj_type = obj.get("@type", "")
        if isinstance(obj_type, list):
            type_str = " ".join(obj_type).lower()
        else:
            type_str = obj_type.lower()

        if "product" in type_str:
            return obj
        
        # Check @graph
        if "@graph" in obj:
            for item in obj["@graph"]:
                result = self._find_product_in_jsonld(item)
                if result:
                    return result
        
        return None

    def _parse_product_jsonld(self, product: dict) -> dict | None:
        """Parse a schema.org Product object into our standard format."""
        offers = product.get("offers", {})
        
        # offers can be a list or a single object
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        
        selling_price = self._safe_float(offers.get("price"))
        
        # Try to get MRP from highPrice or from a separate field
        mrp = self._safe_float(offers.get("highPrice")) or selling_price
        
        # Stock status
        availability = str(offers.get("availability", "")).lower()
        in_stock = "outofstock" not in availability
        
        if selling_price:
            logger.info(f"JSON-LD extracted: selling={selling_price}, mrp={mrp}, in_stock={in_stock}")
            return {
                "selling_price": selling_price,
                "mrp": mrp,
                "in_stock": in_stock,
            }
        return None

    def _extract_next_data(self, page) -> dict | None:
        """
        Extract data from __NEXT_DATA__ script tag (used by Next.js sites like 1mg).
        """
        try:
            script = page.locator('script#__NEXT_DATA__')
            if script.count() > 0:
                raw = script.inner_text(timeout=3000)
                data = json.loads(raw)
                return data
        except Exception as e:
            logger.debug(f"__NEXT_DATA__ extraction failed: {e}")
        return None

    def _extract_prices_from_text(self, page) -> dict | None:
        """
        Fallback: Find all ₹-prefixed prices on the page using semantic text matching.
        Returns the best guess for selling_price and mrp.
        """
        try:
            body_text = page.inner_text("body", timeout=5000)
            # Match patterns like ₹185, ₹1,299.50, MRP ₹199 etc.
            price_matches = re.findall(r'₹\s*([\d,]+(?:\.\d{1,2})?)', body_text)
            prices = []
            for match in price_matches:
                val = self._safe_float(match.replace(",", ""))
                if val and 1 < val < 100000:  # Sane price range filter
                    prices.append(val)

            if not prices:
                return None

            # Heuristic: MRP is usually the higher price, selling price is the lower one
            # Remove duplicates and sort
            unique_prices = sorted(set(prices))
            
            if len(unique_prices) >= 2:
                selling_price = unique_prices[0]
                mrp = unique_prices[1]
            else:
                selling_price = unique_prices[0]
                mrp = selling_price

            logger.info(f"Text-based extraction: selling={selling_price}, mrp={mrp}")
            return {
                "selling_price": selling_price,
                "mrp": mrp,
                "in_stock": True,  # Can't determine from text alone
            }
        except Exception as e:
            logger.debug(f"Text-based extraction failed: {e}")
        return None

    def _clean_price(self, text: str) -> float | None:
        """Remove non-numeric chars (except dot) from a price string and return a float."""
        if not text:
            return None
        clean = re.sub(r'[^\d.]', '', text)
        try:
            return float(clean)
        except ValueError:
            return None

    def _safe_float(self, value) -> float | None:
        """Safely convert any value to float."""
        if value is None:
            return None
        try:
            if isinstance(value, str):
                value = value.replace(",", "")
            return float(value)
        except (ValueError, TypeError):
            return None

    def _check_stock_status(self, page) -> bool:
        """
        Check stock status using common text patterns.
        Returns True if in stock, False if out of stock.
        """
        try:
            body_text = page.inner_text("body", timeout=3000).lower()
            out_of_stock_phrases = [
                "out of stock",
                "currently unavailable",
                "not available",
                "sold out",
                "notify me",
            ]
            for phrase in out_of_stock_phrases:
                if phrase in body_text:
                    return False
        except Exception:
            pass
        return True
