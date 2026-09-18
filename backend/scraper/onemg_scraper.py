from .base_scraper import BaseScraper
import re
import json
import logging
from playwright.async_api import Page

logger = logging.getLogger(__name__)

class OneMgScraper(BaseScraper):
    def __init__(self, platform_id: int):
        super().__init__(platform_id=platform_id, platform_name="1mg")

    async def extract_data(self, page: Page):
        """
        Extracts price data from a Tata 1mg product page.
        
        1mg has moved to Vite SSR — __NEXT_DATA__ no longer exists.
        JSON-LD may or may not contain price data.
        Primary extraction is now DOM-based using 1mg's CSS module classes.
        """
        # ── Layer 1: JSON-LD ──
        result = await self._extract_json_ld(page)
        if result and result.get("selling_price"):
            logger.info(f"1mg: Extracted via JSON-LD: {result}")
            return result

        # ── Layer 2: 1mg-specific DOM selectors ──
        result = await self._extract_from_dom(page)
        if result and result.get("selling_price"):
            logger.info(f"1mg: Extracted via DOM selectors: {result}")
            return result

        # ── Layer 3: Text-based fallback ──
        result = await self._extract_prices_from_text(page)
        if result and result.get("selling_price"):
            logger.info(f"1mg: Extracted via text fallback: {result}")
            return result

        logger.error("1mg: All extraction methods failed.")
        return None

    async def _extract_from_dom(self, page: Page) -> dict | None:
        """
        Extract prices from 1mg's DOM using a careful, layered approach.
        
        KEY INSIGHT (from live page analysis):
        - 1mg's PriceWidget/Price-module containers ALSO contain a
          "BestPrice" coupon slider with promotional prices like:
          "Get for ₹24.4 on orders above ₹1200"
        - These coupon prices are WRONG for our purposes.
        - The REAL selling price is in a large bold font (displaySmallExtraBold)
        - The REAL MRP is in a strikethrough element near the selling price
        
        Strategy:
        1. First try to get MRP from strikethrough elements (most reliable)
        2. Then find the selling price from the largest-font visible ₹ element
           that is NOT inside a BestPrice/coupon/offer container
        3. Validate: selling_price <= MRP
        """
        selling_price = None
        mrp = None

        try:
            # ── Step 1: Extract MRP from strikethrough elements ──
            # The MRP is reliably shown in <s>, <del>, or strikethrough-styled
            # elements. We look for these OUTSIDE of coupon/offer areas.
            mrp = await self._find_mrp(page)
            
            # ── Step 2: Extract selling price ──
            # Find the largest-font visible ₹ price that is NOT inside
            # a BestPrice/coupon/offer container
            selling_price = await self._find_selling_price(page)
            
            if selling_price:
                # Validate: swap if selling > MRP (extraction error)
                if mrp and mrp < selling_price:
                    mrp, selling_price = selling_price, mrp
                
                # Validate: MRP shouldn't be absurdly higher than selling
                if mrp and mrp > selling_price * 5:
                    logger.warning(f"1mg: MRP ({mrp}) is >5x selling ({selling_price}), resetting MRP")
                    mrp = selling_price
                
                return {
                    "selling_price": selling_price,
                    "mrp": mrp or selling_price,
                    "in_stock": await self._check_stock_status(page),
                }
                
        except Exception as e:
            logger.debug(f"1mg DOM extraction failed: {e}")
        return None

    async def _find_mrp(self, page: Page) -> float | None:
        """
        Find the MRP (Maximum Retail Price) from the DOM.
        MRP is shown either:
        - In a strikethrough element (<s>, <del>, or line-through CSS)
        - With an explicit "MRP" label nearby
        """
        # Strategy 1: Strikethrough elements NOT inside coupon areas
        for selector in ['s', 'del', '[class*="strikethrough" i]']:
            try:
                elements = await page.locator(selector).all()
                for el in elements:
                    try:
                        if not await el.is_visible():
                            continue
                        
                        # Skip if inside a BestPrice/coupon/offer container
                        is_in_coupon = await el.evaluate("""el => {
                            const couponSelectors = [
                                '[class*="BestPrice"]', '[class*="bestPrice"]',
                                '[class*="coupon"]', '[class*="Coupon"]',
                                '[class*="offer-slider"]', '[class*="OfferSlider"]',
                                '[class*="promo"]', '[class*="Promo"]',
                            ];
                            for (const sel of couponSelectors) {
                                if (el.closest(sel)) return true;
                            }
                            return false;
                        }""")
                        if is_in_coupon:
                            continue
                        
                        text = await el.inner_text(timeout=2000)
                        price = self._clean_price(text)
                        if price and 1 < price < 100000:
                            logger.debug(f"1mg: Found MRP {price} from strikethrough")
                            return price
                    except Exception:
                        continue
            except Exception:
                continue
        
        # Strategy 2: Explicit "MRP" label in text
        try:
            body_text = await page.inner_text("body", timeout=5000)
            mrp_match = re.search(r'MRP\s*:?\s*₹\s*([\d,]+(?:\.\d{1,2})?)', body_text, re.IGNORECASE)
            if mrp_match:
                price = self._safe_float(mrp_match.group(1).replace(",", ""))
                if price and 1 < price < 100000:
                    return price
        except Exception:
            pass
        
        return None

    async def _find_selling_price(self, page: Page) -> float | None:
        """
        Find the actual selling price (not coupon price) from the DOM.
        
        The selling price on 1mg is the most prominent price on the page,
        displayed in a large bold font. We find the largest-font ₹ price
        that is NOT inside a coupon/BestPrice/offer container.
        """
        try:
            # Find all visible ₹ price elements
            price_elements = await page.locator('text=/₹\\s*\\d/').all()
            
            best_price = None
            best_font_size = 0
            
            for el in price_elements:
                try:
                    if not await el.is_visible():
                        continue
                    
                    # Skip if inside a BestPrice/coupon/offer container
                    is_in_coupon = await el.evaluate("""el => {
                        const couponSelectors = [
                            '[class*="BestPrice"]', '[class*="bestPrice"]',
                            '[class*="coupon"]', '[class*="Coupon"]',
                            '[class*="offer-slider"]', '[class*="OfferSlider"]',
                            '[class*="promo"]', '[class*="Promo"]',
                            '[class*="best-price"]',
                        ];
                        for (const sel of couponSelectors) {
                            if (el.closest(sel)) return true;
                        }
                        return false;
                    }""")
                    if is_in_coupon:
                        continue
                    
                    # Skip if inside a strikethrough (that's MRP, not selling)
                    is_struck = await el.evaluate("""el => {
                        const style = window.getComputedStyle(el);
                        if (style.textDecorationLine && style.textDecorationLine.includes('line-through')) return true;
                        if (el.closest('s') || el.closest('del')) return true;
                        if (el.closest('[class*="strikethrough" i]')) return true;
                        return false;
                    }""")
                    if is_struck:
                        continue
                    
                    # Get font size
                    size_str = await el.evaluate("el => window.getComputedStyle(el).fontSize")
                    size = float(size_str.replace('px', ''))
                    
                    # Extract the price
                    text = await el.inner_text(timeout=2000)
                    price = self._clean_price(text)
                    
                    if price and 1 < price < 100000 and size > best_font_size:
                        best_font_size = size
                        best_price = price
                        
                except Exception:
                    continue
            
            if best_price:
                logger.debug(f"1mg: Found selling price {best_price} (font-size: {best_font_size}px)")
            return best_price
            
        except Exception as e:
            logger.debug(f"1mg: _find_selling_price failed: {e}")
        return None
