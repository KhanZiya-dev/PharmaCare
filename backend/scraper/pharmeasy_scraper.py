from .base_scraper import BaseScraper
import re
import json
import logging

logger = logging.getLogger(__name__)


class PharmEasyScraper(BaseScraper):
    def __init__(self, platform_id: int):
        super().__init__(platform_id=platform_id, platform_name="PharmEasy")

    def extract_data(self, page):
        """
        Extracts price data from a PharmEasy product page.

        Strategy (ordered by reliability):
        1. JSON-LD structured data (schema.org Product)
        2. Intercept internal API data embedded in page HTML
        3. Semantic CSS selectors (stable attributes)
        4. Text-based ₹ pattern matching (last resort)
        """

        # ── Layer 1: JSON-LD ──
        result = self._extract_json_ld(page)
        if result and result.get("selling_price"):
            logger.info(f"PharmEasy: Extracted via JSON-LD: {result}")
            result["in_stock"] = self._check_stock_status(page)
            return result

        # ── Layer 2: Embedded JSON / script data ──
        result = self._extract_from_embedded_data(page)
        if result and result.get("selling_price"):
            logger.info(f"PharmEasy: Extracted via embedded data: {result}")
            return result

        # ── Layer 3: Semantic selectors ──
        result = self._extract_from_dom(page)
        if result and result.get("selling_price"):
            logger.info(f"PharmEasy: Extracted via DOM selectors: {result}")
            return result

        # ── Layer 4: Text-based fallback ──
        result = self._extract_prices_from_text(page)
        if result and result.get("selling_price"):
            result["in_stock"] = self._check_stock_status(page)
            logger.info(f"PharmEasy: Extracted via text fallback: {result}")
            return result

        logger.error("PharmEasy: All extraction methods failed.")
        return None

    def _extract_from_embedded_data(self, page) -> dict | None:
        """
        PharmEasy sometimes embeds product data in script tags or window.__INITIAL_STATE__.
        Also check __NEXT_DATA__ in case they've migrated to Next.js.
        """
        try:
            # Try __NEXT_DATA__ first
            data = self._extract_next_data(page)
            if data:
                props = data.get("props", {}).get("pageProps", {})
                product = (
                    props.get("productData")
                    or props.get("product")
                    or props.get("data", {})
                    or props
                )
                selling_price = (
                    self._safe_float(product.get("price"))
                    or self._safe_float(product.get("selling_price"))
                    or self._safe_float(product.get("salePrice"))
                )
                mrp = (
                    self._safe_float(product.get("mrp"))
                    or self._safe_float(product.get("maximumRetailPrice"))
                    or selling_price
                )
                if selling_price:
                    in_stock = product.get("inStock", product.get("is_in_stock", True))
                    return {
                        "selling_price": selling_price,
                        "mrp": mrp or selling_price,
                        "in_stock": bool(in_stock),
                    }

            # Try window.__INITIAL_STATE__ or similar
            scripts = page.locator("script").all()
            for script in scripts:
                try:
                    text = script.inner_text(timeout=2000)
                    if "__INITIAL_STATE__" in text or "productData" in text:
                        # Extract JSON from assignment
                        match = re.search(r'=\s*({.+})\s*;?\s*$', text, re.DOTALL)
                        if match:
                            data = json.loads(match.group(1))
                            # Navigate to price info
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
                                return {
                                    "selling_price": price,
                                    "mrp": mrp,
                                    "in_stock": True,
                                }
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f"PharmEasy embedded data extraction failed: {e}")
        return None

    def _extract_from_dom(self, page) -> dict | None:
        """
        Use stable, semantic selectors to find prices in the DOM.
        PharmEasy typically shows selling price prominently and MRP struck-through.
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

            # If no selling price yet, look for ₹ near product info area
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
            logger.debug(f"PharmEasy DOM extraction failed: {e}")
        return None
