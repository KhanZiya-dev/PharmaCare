from .base_scraper import BaseScraper
import logging
from playwright.async_api import Page

logger = logging.getLogger(__name__)

class GenericLabTestScraper(BaseScraper):
    def __init__(self, platform_id: int, platform_name: str):
        super().__init__(platform_id=platform_id, platform_name=platform_name)

    async def extract_data(self, page: Page):
        """
        Generic extractor for lab tests using BaseScraper's built-in heuristics.
        """
        # ── Layer 1: JSON-LD ──
        result = await self._extract_json_ld(page)
        if result and result.get("selling_price"):
            logger.info(f"{self.platform_name}: Extracted via JSON-LD: {result}")
            return result

        # ── Layer 2: __NEXT_DATA__ ──
        result = await self._extract_next_data(page)
        if result and result.get("selling_price"):
            logger.info(f"{self.platform_name}: Extracted via __NEXT_DATA__: {result}")
            return result

        # ── Layer 3: Text-based fallback ──
        result = await self._extract_prices_from_text(page)
        if result and result.get("selling_price"):
            if "in_stock" not in result:
                result["in_stock"] = await self._check_stock_status(page)
            logger.info(f"{self.platform_name}: Extracted via text fallback: {result}")
            return result

        logger.error(f"{self.platform_name}: All extraction methods failed.")
        return None
