from .base_scraper import BaseScraper
import re
import logging

logger = logging.getLogger(__name__)

class OneMgScraper(BaseScraper):
    def __init__(self, platform_id: int):
        super().__init__(platform_id=platform_id, platform_name="1mg")

    def extract_data(self, page):
        """
        Extracts data from 1mg product page.
        Note: These CSS selectors are best-effort placeholders and will likely need tuning
        when tested against live 1mg structure.
        """
        try:
            # 1mg often has price in spans with specific classes or data attributes
            # E.g. selling price is often the large text, MRP is struck through
            selling_price_text = page.locator(".PriceBoxPlanOption__offer-price-cp___2QPU_").first.inner_text(timeout=5000)
            mrp_text = page.locator(".PriceDetails__discount-div___3k55z").first.inner_text(timeout=2000)
        except Exception as e:
            # Fallback or general approach
            logger.warning(f"Could not find primary price elements on 1mg: {e}")
            try:
                # Basic fallback to look for text with ₹ or Rs.
                selling_price_text = page.locator("text=₹").first.inner_text()
                mrp_text = selling_price_text # fallback if MRP not found separately
            except:
                selling_price_text = None
                mrp_text = None

        # Clean strings to extract floats
        selling_price = self._clean_price(selling_price_text) if selling_price_text else None
        mrp = self._clean_price(mrp_text) if mrp_text else None
        if not mrp and selling_price:
            mrp = selling_price

        # Check stock status - look for "Out of stock" text
        in_stock = True
        try:
            if page.locator("text=Out of stock").count() > 0:
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
        # Remove non-numeric chars except dot
        clean = re.sub(r'[^\d.]', '', text)
        try:
            return float(clean)
        except ValueError:
            return None
