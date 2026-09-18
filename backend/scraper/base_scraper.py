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
            if data:
                if not data.get("image_url"):
                    data["image_url"] = await self._extract_og_image(page)
                    
                # ── Accurate restricted detection ──
                # Check for "Not for Online Sale" ONLY in the product section area,
                # NOT the full page HTML. The full page contains FAQ, footer, related
                # medicines, etc. that can trigger false positives.
                # IMPORTANT: "prescription required" is completely normal for Rx
                # medicines and MUST NOT be marked restricted!
                data["is_restricted"] = await self._check_restricted_status(page)

                # ── Robust stock status verification ──
                # Use multi-signal detection: OOS classes, buttons, cart state
                is_dom_stock = await self._check_stock_status(page)
                if not is_dom_stock:
                    data["in_stock"] = False
                elif "in_stock" not in data:
                    data["in_stock"] = is_dom_stock
                
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
        Extract price data from JSON-LD (schema.org Product OR Drug) structured data.
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
        """Recursively search for a Product or Drug schema object."""
        if not isinstance(obj, dict):
            return None
        
        obj_type = obj.get("@type", "")
        if isinstance(obj_type, list):
            type_str = " ".join(obj_type).lower()
        else:
            type_str = obj_type.lower()

        # Match both Product and Drug schema types — both have "offers"
        if any(t in type_str for t in ["product", "drug"]):
            return obj
        
        # Check @graph
        if "@graph" in obj:
            for item in obj["@graph"]:
                result = self._find_product_in_jsonld(item)
                if result:
                    return result
        
        # Check mainEntity (used by Apollo's MedicalWebPage)
        if "mainEntity" in obj:
            result = self._find_product_in_jsonld(obj["mainEntity"])
            if result:
                return result
        
        return None

    def _parse_product_jsonld(self, product: dict) -> dict | None:
        """Parse a schema.org Product/Drug object into our standard format."""
        offers = product.get("offers", {})
        
        # offers can be a list or a single object
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        
        selling_price = self._safe_float(offers.get("price"))
        
        # Try to get MRP from highPrice or from a separate field
        mrp = self._safe_float(offers.get("highPrice")) or selling_price
        
        # Stock status from JSON-LD
        availability = str(offers.get("availability", "")).lower()
        in_stock = "outofstock" not in availability and "discontinued" not in availability
        
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
            if image_url and "logo" in image_url.lower():
                image_url = None
                
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
                    if "logo" in url.lower():
                        return None
                    return url
        except Exception as e:
            logger.debug(f"OG Image extraction failed: {e}")
        return None

    async def _extract_next_data(self, page: Page) -> dict | None:
        """
        Extract data from __NEXT_DATA__ script tag (used by Next.js sites like Apollo).
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
        Fallback: Context-aware price extraction from visible page text.
        Instead of blindly picking smallest/largest prices, we look for:
        1. Prices near "MRP" labels → that's the MRP
        2. Prices with strikethrough styling → that's the MRP
        3. The prominent (non-struck) price → that's the selling price
        """
        try:
            # Strategy 1: Look for MRP-labeled prices
            mrp = None
            selling_price = None
            
            # Try to find MRP explicitly labeled
            mrp_patterns = [
                r'MRP\s*:?\s*₹\s*([\d,]+(?:\.\d{1,2})?)',
                r'M\.R\.P\.?\s*:?\s*₹\s*([\d,]+(?:\.\d{1,2})?)',
                r'mrp\s*:?\s*₹\s*([\d,]+(?:\.\d{1,2})?)',
            ]
            
            body_text = await page.inner_text("body", timeout=5000)
            
            for pattern in mrp_patterns:
                match = re.search(pattern, body_text, re.IGNORECASE)
                if match:
                    mrp = self._safe_float(match.group(1).replace(",", ""))
                    if mrp and 1 < mrp < 100000:
                        break
                    mrp = None
            
            # Strategy 2: Find all ₹-prefixed prices on the page
            price_matches = re.findall(r'₹\s*([\d,]+(?:\.\d{1,2})?)', body_text)
            prices = []
            for match in price_matches:
                val = self._safe_float(match.replace(",", ""))
                if val and 5 < val < 50000:  # Stricter range to filter junk
                    prices.append(val)

            if not prices:
                return None

            # Remove duplicates and sort
            unique_prices = sorted(set(prices))
            
            if mrp:
                # MRP was found explicitly — selling price is the price that's
                # less than or equal to MRP and closest to it
                candidates = [p for p in unique_prices if p <= mrp]
                if candidates:
                    selling_price = candidates[0]  # Smallest price ≤ MRP
                else:
                    selling_price = mrp
            elif len(unique_prices) >= 2:
                # Heuristic: if exactly 2 distinct prices near each other,
                # the smaller is selling, larger is MRP
                selling_price = unique_prices[0]
                mrp = unique_prices[-1]
                # Sanity check: MRP shouldn't be more than 5x the selling price
                if mrp > selling_price * 5:
                    mrp = selling_price
            else:
                selling_price = unique_prices[0]
                mrp = selling_price

            logger.info(f"Text-based extraction: selling={selling_price}, mrp={mrp}")
            return {
                "selling_price": selling_price,
                "mrp": mrp,
                # Can't reliably determine stock from text alone — let
                # _check_stock_status handle it
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

    # ── Restricted Status Detection ──────────────────────────────────────

    async def _check_restricted_status(self, page: Page) -> bool:
        """
        Accurately detect if a medicine is marked 'Not for Online Sale'.
        
        KEY FIX: Instead of searching the FULL page HTML (which contains
        FAQ, footer, related products, other medicine info that causes
        false positives), we:
        1. Only check VISIBLE elements for restricted phrases
        2. Exclude footer/FAQ/description sections  
        3. Require the absence of a working "Add to Cart" button as
           a secondary signal for ambiguous cases
        
        IMPORTANT: "prescription required" is NORMAL for Rx medicines
        and must NOT trigger this.
        """
        restricted_phrases = [
            "not for online sale",
            "we do not facilitate sale",
            "not available for online purchase",
            "cannot be sold online",
            "available in store only",
            "available in stores only",
            "store pickup only",
        ]
        
        store_finder_phrases = [
            "find at your nearest store",
            "find at nearest store",
            "check at nearest store",
        ]
        
        # 1. Check for visible restricted banners — scoped to product area
        for phrase in restricted_phrases:
            try:
                # Use get_by_text for more reliable text matching
                matches = page.get_by_text(phrase, exact=False)
                count = await matches.count()
                for i in range(count):
                    el = matches.nth(i)
                    try:
                        if not await el.is_visible(timeout=1000):
                            continue
                    except Exception:
                        continue
                    
                    # Verify it's NOT inside a footer, FAQ, or long-form
                    # content section (these frequently mention "not for
                    # online sale" about OTHER medicines or in general info)
                    is_in_excluded = await el.evaluate("""el => {
                        const excludeSelectors = [
                            'footer', '[class*="footer" i]', '[id*="footer" i]',
                            '[class*="faq" i]', '[id*="faq" i]',
                            '[class*="description" i]', '[id*="description" i]',
                            '[class*="content-section" i]',
                            '[class*="drug-info" i]', '[class*="drugInfo" i]',
                            '[class*="about-section" i]',
                            '[class*="information" i]', '[id*="information" i]',
                            'article',
                        ];
                        for (const sel of excludeSelectors) {
                            if (el.closest(sel)) return true;
                        }
                        return false;
                    }""")
                    
                    if not is_in_excluded:
                        logger.info(f"[{self.platform_name}] Restricted: visible '{phrase}' found in product area")
                        return True
            except Exception:
                continue
        
        # 2. Store-finder phrases are only meaningful if there's NO cart button
        has_cart = await self._has_visible_cart_button(page)
        if not has_cart:
            for phrase in store_finder_phrases:
                try:
                    matches = page.get_by_text(phrase, exact=False)
                    count = await matches.count()
                    for i in range(count):
                        el = matches.nth(i)
                        try:
                            if await el.is_visible(timeout=1000):
                                logger.info(f"[{self.platform_name}] Restricted: '{phrase}' found + no cart button")
                                return True
                        except Exception:
                            continue
                except Exception:
                    continue
        
        return False

    # ── Stock Status Detection ───────────────────────────────────────────

    async def _check_stock_status(self, page: Page) -> bool:
        """
        Robust, multi-signal stock validation:
        1. Explicit Out-of-Stock CSS classes (without broken 'i' flag)
        2. Visible Out-of-Stock text badges
        3. Notify Me / Sold Out action buttons
        4. Enabled Add to Cart / Buy Now buttons (positive signal)
        """
        try:
            # 1. Check for dedicated Out-of-Stock elements via classes
            # Note: Playwright attribute selectors do NOT support the CSS 'i' flag
            # So we check multiple casing variants explicitly
            oos_selectors = [
                '[class*="outOfStock"]',
                '[class*="out-of-stock"]',
                '[class*="outofstock"]',
                '[class*="OutOfStock"]',
                '[data-testid*="out-of-stock"]',
                '[data-testid*="oos"]',
                '[aria-label*="out of stock"]',
            ]
            for sel in oos_selectors:
                try:
                    elements = page.locator(sel)
                    count = await elements.count()
                    for i in range(count):
                        el = elements.nth(i)
                        try:
                            if not await el.is_visible(timeout=1000):
                                continue
                            
                            # Exclude OOS elements from related/similar products,
                            # sidebar, footer, etc. — these cause false positives
                            is_in_excluded = await el.evaluate("""el => {
                                const excludeSelectors = [
                                    '[class*="similar" i]', '[class*="related" i]',
                                    '[class*="recommend" i]', '[class*="alternate" i]',
                                    '[class*="substitute" i]',
                                    '[class*="sidebar" i]', '[class*="side-bar" i]',
                                    'footer', '[class*="footer" i]',
                                    '[class*="carousel" i]', '[class*="slider" i]',
                                ];
                                for (const s of excludeSelectors) {
                                    if (el.closest(s)) return true;
                                }
                                return false;
                            }""")
                            if is_in_excluded:
                                continue
                            
                            logger.info(f"[{self.platform_name}] OOS class element found: {sel}")
                            return False
                        except Exception:
                            continue
                except Exception:
                    continue

            # 2. Check for exact visible Out of Stock text using get_by_text
            # This is more reliable than regex-based text locators
            oos_phrases = [
                "out of stock",
                "currently unavailable",
                "sold out",
                "temporarily unavailable",
            ]
            for phrase in oos_phrases:
                try:
                    matched = page.get_by_text(phrase, exact=True)
                    count = await matched.count()
                    for i in range(count):
                        el = matched.nth(i)
                        try:
                            if not await el.is_visible(timeout=1000):
                                continue
                        except Exception:
                            continue
                        
                        # Make sure it's not inside a FAQ or description
                        is_in_content = await el.evaluate("""el => {
                            const p = el.closest('[class*="faq" i], [class*="description" i], article, footer');
                            return !!p;
                        }""")
                        if not is_in_content:
                            logger.info(f"[{self.platform_name}] OOS text found: '{phrase}'")
                            return False
                except Exception:
                    continue

            # 3. Check interactive button states
            notify_phrases = ["notify me", "get notified", "sold out", "currently unavailable"]
            for phrase in notify_phrases:
                try:
                    btn = page.get_by_role("button", name=re.compile(phrase, re.IGNORECASE))
                    if await btn.count() > 0:
                        if await btn.first.is_visible():
                            logger.info(f"[{self.platform_name}] OOS button found: '{phrase}'")
                            return False
                except Exception:
                    continue

            # 4. Check if Add to Cart is present AND disabled
            cart_phrases = ["Add to Cart", "Add to Bag", "Buy Now", "ADD TO CART"]
            for phrase in cart_phrases:
                try:
                    cart_btn = page.get_by_role("button", name=re.compile(phrase, re.IGNORECASE)).first
                    if await cart_btn.count() > 0 and await cart_btn.is_visible():
                        is_disabled = await cart_btn.is_disabled()
                        aria_disabled = await cart_btn.get_attribute("aria-disabled")
                        if is_disabled or aria_disabled == "true":
                            logger.info(f"[{self.platform_name}] Cart button is disabled → OOS")
                            return False
                except Exception:
                    continue

        except Exception as e:
            logger.debug(f"[{self.platform_name}] _check_stock_status exception: {e}")
            
        return True

    # ── Helper: Cart Button Detection ────────────────────────────────────

    async def _has_visible_cart_button(self, page: Page) -> bool:
        """Check if there's an enabled, visible Add to Cart / Buy Now button."""
        cart_labels = ["Add to Cart", "Add to Bag", "Buy Now", "ADD TO CART", "Add To Cart"]
        for label in cart_labels:
            try:
                btn = page.get_by_role("button", name=re.compile(label, re.IGNORECASE)).first
                if await btn.count() > 0:
                    if await btn.is_visible():
                        if not await btn.is_disabled():
                            return True
            except Exception:
                continue
        return False
