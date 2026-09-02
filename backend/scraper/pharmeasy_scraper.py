from .base_scraper import BaseScraper
import re
import logging

logger = logging.getLogger(__name__)

class PharmEasyScraper(BaseScraper):
    def __init__(self, platform_id: int):
        super().__init__(platform_id=platform_id, platform_name="PharmEasy")

    def extract_data(self, page):
        """
        Extracts data from PharmEasy product page.
        """
        try:
            # PharmEasy specific selectors
            selling_price_text = page.locator(".PriceDetails_discountedPrice__A2kE9").first.inner_text(timeout=10000)
            mrp_text = page.locator(".PriceDetails_mrpPrice__4Z-0_").first.inner_text(timeout=10000)
        except Exception as e:
            logger.warning(f"Could not find primary price elements on PharmEasy: {e}")
            try:
                # Basic fallback
                selling_price_text = page.locator("text=₹").first.inner_text()
                mrp_text = selling_price_text
            except:
                selling_price_text = None
                mrp_text = None

        selling_price = self._clean_price(selling_price_text) if selling_price_text else None
        mrp = self._clean_price(mrp_text) if mrp_text else None
        if not mrp and selling_price:
            mrp = selling_price

        in_stock = True
        try:
            # PharmEasy usually displays "Out of Stock" or disables the add to cart button
            if page.locator("text=Out of Stock").count() > 0:
                in_stock = False
        except:
            pass

        return {
            "mrp": mrp,
            "selling_price": selling_price,
            "in_stock": in_stock
        }

    def _clean_price(self, text: str) -> float:
        if not text:
            return None
        clean = re.sub(r'[^\d.]', '', text)
        try:
            return float(clean)
        except ValueError:
            return None
