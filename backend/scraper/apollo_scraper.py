from .base_scraper import BaseScraper
import re
import json
import logging

logger = logging.getLogger(__name__)


class ApolloScraper(BaseScraper):
    def __init__(self, platform_id: int):
        super().__init__(platform_id=platform_id, platform_name="Apollo")

    def extract_data(self, page):
        """
        Extracts price data from an Apollo Pharmacy product page.

        Strategy (ordered by reliability):
        1. JSON-LD structured data (schema.org Product)
        2. __NEXT_DATA__ embedded JSON (Apollo uses Next.js)
        3. Semantic CSS selectors (stable attributes)
        4. Text-based ₹ pattern matching (last resort)
        """

        # ── Layer 1: JSON-LD ──
        result = self._extract_json_ld(page)
        if result and result.get("selling_price"):
            logger.info(f"Apollo: Extracted via JSON-LD: {result}")
            result["in_stock"] = self._check_stock_status(page)
            return result

        # ── Layer 2: __NEXT_DATA__ ──
        result = self._extract_from_next_data(page)
        if result and result.get("selling_price"):
            logger.info(f"Apollo: Extracted via __NEXT_DATA__: {result}")
            return result

        # ── Layer 3: Semantic selectors ──
        result = self._extract_from_dom(page)
        if result and result.get("selling_price"):
            logger.info(f"Apollo: Extracted via DOM selectors: {result}")
            return result

        # ── Layer 4: Text-based fallback ──
        result = self._extract_prices_from_text(page)
        if result and result.get("selling_price"):
            result["in_stock"] = self._check_stock_status(page)
            logger.info(f"Apollo: Extracted via text fallback: {result}")
            return result

        logger.error("Apollo: All extraction methods failed.")
        return None

    def _extract_from_next_data(self, page) -> dict | None:
        """Parse __NEXT_DATA__ for price info on Apollo."""
        try:
            data = self._extract_next_data(page)
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
                return {
                    "selling_price": selling_price,
                    "mrp": mrp or selling_price,
                    "in_stock": bool(in_stock),
                }
        except Exception as e:
            logger.debug(f"Apollo __NEXT_DATA__ parsing failed: {e}")
        return None

    def _extract_from_dom(self, page) -> dict | None:
        """
        Use stable, semantic selectors to find prices in the DOM.
        Apollo typically shows the MRP prominently and selling price may be
        the same or displayed as a discounted price.
        """
        selling_price = None
        mrp = None

        try:
            # Try data attributes
            for selector in ['[data-price]', '[data-selling-price]', '[data-testid*="price"]']:
                try:
                    el = page.locator(selector).first
                    if el.count() > 0:
                        val = el.get_attribute("data-price") or el.get_attribute("data-selling-price")
                        if val:
                            selling_price = self._safe_float(val)
                        else:
                            selling_price = self._clean_price(el.inner_text(timeout=3000))
                        if selling_price:
                            break
                except Exception:
                    continue

            # Find MRP in struck-through text
            for selector in ['del', 's', '.line-through', '[style*="line-through"]']:
                try:
                    el = page.locator(selector).first
                    if el.count() > 0:
                        text = el.inner_text(timeout=3000)
                        mrp = self._clean_price(text)
                        if mrp:
                            break
                except Exception:
                    continue

            # Apollo: the main displayed price text (₹261.5 style on the page)
            if not selling_price:
                try:
                    price_el = page.locator('text=/₹\\s*\\d/').first
                    if price_el.count() > 0:
                        text = price_el.inner_text(timeout=3000)
                        selling_price = self._clean_price(text)
                except Exception:
                    pass

            if selling_price:
                return {
                    "selling_price": selling_price,
                    "mrp": mrp or selling_price,
                    "in_stock": self._check_stock_status(page),
                }
        except Exception as e:
            logger.debug(f"Apollo DOM extraction failed: {e}")
        return None
