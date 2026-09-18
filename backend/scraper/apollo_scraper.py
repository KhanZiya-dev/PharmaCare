from .base_scraper import BaseScraper
import re
import json
import logging
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class ApolloScraper(BaseScraper):
    def __init__(self, platform_id: int):
        super().__init__(platform_id=platform_id, platform_name="Apollo")

    async def extract_data(self, page: Page):
        """
        Extracts price data from an Apollo Pharmacy product page.
        
        Apollo uses Next.js with JSON-LD (@type: Drug, not Product).
        The base scraper's _extract_json_ld now supports @type Drug.
        """
        # ── Layer 1: JSON-LD (now supports @type Drug) ──
        result = await self._extract_json_ld(page)
        if result and result.get("selling_price"):
            logger.info(f"Apollo: Extracted via JSON-LD: {result}")
            # Apollo JSON-LD has 'offers.price' as selling price but no separate MRP.
            # Try to get MRP from the DOM to supplement.
            dom_mrp = await self._extract_mrp_from_dom(page)
            if dom_mrp and dom_mrp > result["selling_price"]:
                result["mrp"] = dom_mrp
            return result

        # ── Layer 2: Apollo-specific DOM selectors ──
        result = await self._extract_from_dom(page)
        if result and result.get("selling_price"):
            logger.info(f"Apollo: Extracted via DOM selectors: {result}")
            return result

        # ── Layer 3: __NEXT_DATA__ ──
        result = await self._extract_from_next_data(page)
        if result and result.get("selling_price"):
            logger.info(f"Apollo: Extracted via __NEXT_DATA__: {result}")
            return result

        # ── Layer 4: Text-based fallback ──
        result = await self._extract_prices_from_text(page)
        if result and result.get("selling_price"):
            logger.info(f"Apollo: Extracted via text fallback: {result}")
            return result

        logger.error("Apollo: All extraction methods failed.")
        return None

    async def _extract_mrp_from_dom(self, page: Page) -> float | None:
        """Extract MRP from struck-through or labeled text on Apollo."""
        try:
            # Look for MRP in struck-through elements
            for selector in ['s', 'del', '[class*="line-through"]', '[style*="line-through"]']:
                try:
                    el = page.locator(selector).first
                    if await el.count() > 0 and await el.is_visible():
                        text = await el.inner_text(timeout=2000)
                        mrp = self._clean_price(text)
                        if mrp and mrp > 0:
                            return mrp
                except Exception:
                    continue
            
            # Look for explicit MRP label
            body_text = await page.inner_text("body", timeout=5000)
            mrp_match = re.search(r'MRP\s*:?\s*₹?\s*([\d,]+(?:\.\d{1,2})?)', body_text, re.IGNORECASE)
            if mrp_match:
                mrp = self._safe_float(mrp_match.group(1).replace(",", ""))
                if mrp and mrp > 0:
                    return mrp
        except Exception:
            pass
        return None

    async def _extract_from_next_data(self, page: Page) -> dict | None:
        """Parse __NEXT_DATA__ for price info on Apollo."""
        try:
            data = await super()._extract_next_data(page)
            if not data:
                return None
            
            props = data.get("props", {}).get("pageProps", {})
            
            # Apollo may nest product data under different keys
            product = (
                props.get("productData")
                or props.get("product")
                or props.get("medicineData")
                or props.get("data", {}).get("product")
                or props
            )
            
            selling_price = (
                self._safe_float(product.get("price"))
                or self._safe_float(product.get("selling_price"))
                or self._safe_float(product.get("salePrice"))
                or self._safe_float(product.get("sp"))
            )
            mrp = (
                self._safe_float(product.get("mrp"))
                or self._safe_float(product.get("maximumRetailPrice"))
                or selling_price
            )
            
            if selling_price:
                in_stock = product.get("is_in_stock", product.get("inStock", True))
                
                # Swap if MRP < selling price (data error)
                if mrp and mrp < selling_price:
                    mrp, selling_price = selling_price, mrp
                
                return {
                    "selling_price": selling_price,
                    "mrp": mrp or selling_price,
                    "in_stock": bool(in_stock),
                }
        except Exception as e:
            logger.debug(f"Apollo __NEXT_DATA__ parsing failed: {e}")
        return None

    async def _extract_from_dom(self, page: Page) -> dict | None:
        """
        Use Apollo-specific selectors to find prices in the DOM.
        
        Apollo's React-based layout uses specific patterns:
        - Product price section near the "Add to Cart" button
        - MRP shown with strikethrough
        - Price displayed with ₹ prefix
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

            # ── Strategy 2: MRP from struck-through text ──
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

            # ── Strategy 3: Find the price with the largest visible font size ──
            if not selling_price:
                try:
                    price_elements = await page.locator('text=/₹\\s*\\d/').all()
                    max_size = 0
                    for el in price_elements:
                        try:
                            if not await el.is_visible():
                                continue
                            # Get font size to identify the main price
                            size_str = await el.evaluate("el => window.getComputedStyle(el).fontSize")
                            size = float(size_str.replace('px', ''))
                            if size > max_size:
                                max_size = size
                                text = await el.inner_text(timeout=3000)
                                candidate = self._clean_price(text)
                                if candidate and candidate > 0:
                                    selling_price = candidate
                        except Exception:
                            continue
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
            logger.debug(f"Apollo DOM extraction failed: {e}")
        return None
