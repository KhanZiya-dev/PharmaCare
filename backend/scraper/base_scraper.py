from playwright.async_api import Page
import logging
import random
import asyncio
import re
import json
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseScraper:
    def __init__(self, platform_id: int, platform_name: str):
        self.platform_id = platform_id
        self.platform_name = platform_name

    async def _random_delay(self, min_sec: float = 2.0, max_sec: float = 5.0):
        """Add a randomized delay between requests to avoid IP bans."""
        delay = random.uniform(min_sec, max_sec)
        logger.info(f"[{self.platform_name}] Waiting {delay:.1f}s before next action...")
        await asyncio.sleep(delay)

    async def scrape_page(self, page: Page, url: str):
        """
        Scrape a given URL using an already prepared Playwright Page.
        """
        logger.info(f"Starting scrape for {self.platform_name} at {url}")
        
        try:
            # We assume stealth is applied when creating the page/context in engine
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000) # Give SPAs time to render pricing
            data = await self.extract_data(page)
            if data and not data.get("image_url"):
                data["image_url"] = await self._extract_og_image(page)
            return data
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {str(e)}")
            return None

    async def extract_data(self, page: Page):
        """
        Override this method in specific platform scrapers (e.g., OneMgScraper, PharmEasyScraper)
        """
        raise NotImplementedError("Subclasses must implement extract_data")

    # ── Shared extraction utilities ──────────────────────────────────────

    async def _extract_json_ld(self, page: Page) -> dict | None:
        """
        Extract price data from JSON-LD (schema.org Product) structured data.
        """
        try:
            scripts = await page.locator('script[type="application/ld+json"]').all()
            for script in scripts:
                try:
                    raw = await script.inner_text(timeout=3000)
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
        
        # Image extraction
        image_url = None
        image_data = product.get("image")
        if isinstance(image_data, str):
            image_url = image_data
        elif isinstance(image_data, list) and len(image_data) > 0:
            if isinstance(image_data[0], str):
                image_url = image_data[0]
            elif isinstance(image_data[0], dict):
                image_url = image_data[0].get("url")
        elif isinstance(image_data, dict):
            image_url = image_data.get("url")
        
        if selling_price:
            logger.info(f"JSON-LD extracted: selling={selling_price}, mrp={mrp}, in_stock={in_stock}")
            return {
                "selling_price": selling_price,
                "mrp": mrp,
                "in_stock": in_stock,
                "image_url": image_url,
            }
        return None

    async def _extract_og_image(self, page: Page) -> str | None:
        """Extract main product image from meta og:image tag."""
        try:
            meta = page.locator('meta[property="og:image"]')
            if await meta.count() > 0:
                url = await meta.first.get_attribute("content")
                if url and url.startswith("http"):
                    return url
        except Exception as e:
            logger.debug(f"OG Image extraction failed: {e}")
        return None

    async def _extract_next_data(self, page: Page) -> dict | None:
        """
        Extract data from __NEXT_DATA__ script tag (used by Next.js sites like 1mg).
        """
        try:
            script = page.locator('script#__NEXT_DATA__')
            if await script.count() > 0:
                raw = await script.inner_text(timeout=3000)
                data = json.loads(raw)
                return data
        except Exception as e:
            logger.debug(f"__NEXT_DATA__ extraction failed: {e}")
        return None

    async def _extract_prices_from_text(self, page: Page) -> dict | None:
        """
        Fallback: Find all ₹-prefixed prices on the page using semantic text matching.
        """
        try:
            body_text = await page.inner_text("body", timeout=5000)
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

    async def _check_stock_status(self, page: Page) -> bool:
        """
        Check stock status using common text patterns.
        """
        try:
            body_text = await page.inner_text("body", timeout=3000)
            body_text = body_text.lower()
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
