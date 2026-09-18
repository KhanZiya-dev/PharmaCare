from .base_scraper import BaseScraper
import re
import json
import logging
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class PharmEasyScraper(BaseScraper):
    def __init__(self, platform_id: int):
        super().__init__(platform_id=platform_id, platform_name="PharmEasy")

    async def extract_data(self, page: Page):
        """
        Extracts price data from a PharmEasy product page.
        
        PharmEasy has good JSON-LD support with Product schema.
        Also embeds data in __NEXT_DATA__ and __INITIAL_STATE__.
        """
        # ── Layer 1: JSON-LD (most reliable for PharmEasy) ──
        result = await self._extract_json_ld(page)
        if result and result.get("selling_price"):
            logger.info(f"PharmEasy: Extracted via JSON-LD: {result}")
            return result

        # ── Layer 2: Embedded JSON / script data ──
        result = await self._extract_from_embedded_data(page)
        if result and result.get("selling_price"):
            logger.info(f"PharmEasy: Extracted via embedded data: {result}")
            return result

        # ── Layer 3: Semantic selectors ──
        result = await self._extract_from_dom(page)
        if result and result.get("selling_price"):
            logger.info(f"PharmEasy: Extracted via DOM selectors: {result}")
            return result

        # ── Layer 4: Text-based fallback ──
        result = await self._extract_prices_from_text(page)
        if result and result.get("selling_price"):
            logger.info(f"PharmEasy: Extracted via text fallback: {result}")
            return result

        logger.error("PharmEasy: All extraction methods failed.")
        return None

    async def _extract_from_embedded_data(self, page: Page) -> dict | None:
        """
        PharmEasy sometimes embeds product data in __NEXT_DATA__ or
        window.__INITIAL_STATE__.
        """
        try:
            # Try __NEXT_DATA__ first
            data = await self._extract_next_data(page)
            if data:
                props = data.get("props", {}).get("pageProps", {})
                
                # PharmEasy nests product data under several possible keys
                product = None
                for key in ["productData", "product", "data", "productDetails"]:
                    candidate = props.get(key)
                    if isinstance(candidate, dict):
                        product = candidate
                        break
                
                if not product:
                    product = props
                
                selling_price = (
                    self._safe_float(product.get("price"))
                    or self._safe_float(product.get("selling_price"))
                    or self._safe_float(product.get("salePrice"))
                    or self._safe_float(product.get("sp"))
                )
                mrp = (
                    self._safe_float(product.get("mrp"))
                    or self._safe_float(product.get("maximumRetailPrice"))
                    or self._safe_float(product.get("maxRetailPrice"))
                    or selling_price
                )
                if selling_price:
                    in_stock = product.get("inStock",
                               product.get("is_in_stock",
                               product.get("isAvailable", True)))
                    
                    # Swap if MRP < selling price
                    if mrp and mrp < selling_price:
                        mrp, selling_price = selling_price, mrp
                    
                    return {
                        "selling_price": selling_price,
                        "mrp": mrp or selling_price,
                        "in_stock": bool(in_stock),
                    }

            # Try window.__INITIAL_STATE__ or similar embedded JSON
            scripts = await page.locator("script").all()
            for script in scripts:
                try:
                    text = await script.inner_text(timeout=2000)
                    if "__INITIAL_STATE__" not in text and "productData" not in text:
                        continue
                    
                    match = re.search(r'=\s*({.+})\s*;?\s*$', text, re.DOTALL)
                    if not match:
                        continue
                    
                    data = json.loads(match.group(1))
                    
                    # Navigate nested structures
                    price = self._safe_float(
                        data.get("price")
                        or data.get("productDetails", {}).get("price")
                        or data.get("productDetails", {}).get("salePrice")
                    )
                    if price:
                        mrp = self._safe_float(
                            data.get("mrp")
                            or data.get("productDetails", {}).get("mrp")
                        ) or price
                        
                        if mrp < price:
                            mrp, price = price, mrp
                        
                        return {
                            "selling_price": price,
                            "mrp": mrp,
                            "in_stock": await self._check_stock_status(page),
                        }
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f"PharmEasy embedded data extraction failed: {e}")
        return None

    async def _extract_from_dom(self, page: Page) -> dict | None:
        """
        Use PharmEasy-specific selectors to find prices in the DOM.
        """
        selling_price = None
        mrp = None

        try:
            # ── Strategy 1: Data attributes ──
            for selector in ['[data-price]', '[data-selling-price]', '[data-testid*="price"]']:
                try:
                    el = page.locator(selector).first
                    if await el.count() > 0:
                        val = await el.get_attribute("data-price") or await el.get_attribute("data-selling-price")
                        if val:
                            selling_price = self._safe_float(val)
                        else:
                            selling_price = self._clean_price(await el.inner_text(timeout=3000))
                        if selling_price:
                            break
                except Exception:
                    continue

            # ── Strategy 2: MRP from struck-through elements ──
            for selector in ['del', 's', '[class*="line-through"]', '[style*="line-through"]']:
                try:
                    el = page.locator(selector).first
                    if await el.count() > 0 and await el.is_visible():
                        text = await el.inner_text(timeout=3000)
                        candidate = self._clean_price(text)
                        if candidate and candidate > 0:
                            mrp = candidate
                            break
                except Exception:
                    continue

            # ── Strategy 3: Biggest visible ₹ price ──
            if not selling_price:
                try:
                    price_el = page.locator('text=/₹\\s*\\d/').first
                    if await price_el.count() > 0 and await price_el.is_visible():
                        text = await price_el.inner_text(timeout=3000)
                        selling_price = self._clean_price(text)
                except Exception:
                    pass

            if selling_price:
                # Ensure MRP >= selling price
                if mrp and mrp < selling_price:
                    mrp, selling_price = selling_price, mrp
                
                return {
                    "selling_price": selling_price,
                    "mrp": mrp or selling_price,
                    "in_stock": await self._check_stock_status(page),
                }
        except Exception as e:
            logger.debug(f"PharmEasy DOM extraction failed: {e}")
        return None
