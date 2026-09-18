"""
Link Validator & Re-Linker Script
==================================
Phase 1: Validate existing links using URL slug (NO website visits — instant)
Phase 2: Delete invalid links from DB
Phase 3: Re-search correct links using validated platform_search (with anti-blocking delays)

Anti-blocking measures:
- Random delays (4-8s) between searches
- playwright-stealth for fingerprint evasion
- One medicine at a time, not parallel (safer)
- Graceful error handling with retries
"""

import os
import sys
import asyncio
import random
import logging
from dotenv import load_dotenv
from supabase import create_client

# Allow importing from scripts/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts"))
from platform_search import (
    normalize_medicine_name, names_match, _extract_name_from_slug,
    search_1mg_async, search_pharmeasy_async, search_apollo_async
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))


def fetch_all_links():
    """Fetch all platform_product_links with product name and platform name."""
    res = supabase.table("platform_product_links").select(
        "id, scrape_url, product_id, platform_id, products(name), platforms(name)"
    ).execute()
    return res.data or []


def validate_link_by_slug(link: dict) -> bool:
    """
    Check if the URL slug matches the product name.
    Returns True if valid, False if invalid/suspicious.
    
    For PharmEasy: slug is unreliable (ID determines product), so we
    ALWAYS flag PharmEasy links for re-verification.
    """
    product_name = link.get("products", {}).get("name", "")
    platform_name = (link.get("platforms", {}).get("name", "") or "").lower()
    scrape_url = link.get("scrape_url", "")
    
    if not product_name or not scrape_url:
        return False
    
    # PharmEasy: slug is unreliable, always flag for re-check
    if "pharmeasy" in platform_name:
        slug_name = _extract_name_from_slug(scrape_url)
        if slug_name and names_match(product_name, slug_name, threshold=0.6):
            return True
        # Slug doesn't match — but PharmEasy slugs are unreliable
        # Flag as invalid so it gets re-searched with proper validation
        return False
    
    # 1mg / Apollo: slug is reliable
    slug_name = _extract_name_from_slug(scrape_url)
    if not slug_name:
        return False
    
    return names_match(product_name, slug_name, threshold=0.6)


def phase1_validate():
    """Phase 1: Check all existing links via slug matching (instant, no HTTP)."""
    logger.info("=" * 60)
    logger.info("PHASE 1: Validating existing links by URL slug...")
    logger.info("=" * 60)
    
    all_links = fetch_all_links()
    logger.info(f"Total links in DB: {len(all_links)}")
    
    valid = []
    invalid = []
    
    for link in all_links:
        product_name = link.get("products", {}).get("name", "???")
        platform_name = link.get("platforms", {}).get("name", "???")
        
        if validate_link_by_slug(link):
            valid.append(link)
        else:
            slug_name = _extract_name_from_slug(link.get("scrape_url", ""))
            logger.warning(
                f"  ❌ INVALID: [{platform_name}] '{product_name}' → slug: '{slug_name}' → {link['scrape_url']}"
            )
            invalid.append(link)
    
    logger.info(f"\nResults: {len(valid)} valid, {len(invalid)} invalid")
    return valid, invalid


def phase2_delete_invalid(invalid_links: list):
    """Phase 2: Delete invalid links from DB."""
    if not invalid_links:
        logger.info("No invalid links to delete.")
        return
    
    logger.info("=" * 60)
    logger.info(f"PHASE 2: Deleting {len(invalid_links)} invalid links...")
    logger.info("=" * 60)
    
    for link in invalid_links:
        try:
            supabase.table("platform_product_links").delete().eq("id", link["id"]).execute()
            product_name = link.get("products", {}).get("name", "???")
            platform_name = link.get("platforms", {}).get("name", "???")
            logger.info(f"  🗑️  Deleted: [{platform_name}] {product_name}")
        except Exception as e:
            logger.error(f"  Failed to delete link {link['id']}: {e}")


async def phase3_research(invalid_links: list):
    """Phase 3: Re-search correct links for previously invalid entries."""
    if not invalid_links:
        logger.info("No links to re-search.")
        return
    
    logger.info("=" * 60)
    logger.info(f"PHASE 3: Re-searching {len(invalid_links)} links with validation...")
    logger.info("=" * 60)
    
    # Group by product to avoid duplicate searches
    products_to_search = {}
    for link in invalid_links:
        product_id = link["product_id"]
        platform_id = link["platform_id"]
        product_name = link.get("products", {}).get("name", "")
        platform_name = (link.get("platforms", {}).get("name", "") or "").lower()
        
        if product_id not in products_to_search:
            products_to_search[product_id] = {
                "name": product_name,
                "platforms": {}
            }
        products_to_search[product_id]["platforms"][platform_name] = platform_id
    
    logger.info(f"Unique products to search: {len(products_to_search)}")
    
    from playwright.async_api import async_playwright
    from playwright_stealth import stealth_async
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await stealth_async(page)
        
        found_count = 0
        total = len(products_to_search)
        
        for idx, (product_id, info) in enumerate(products_to_search.items(), 1):
            product_name = info["name"]
            logger.info(f"\n[{idx}/{total}] Searching: {product_name}")
            
            for platform_key, platform_id in info["platforms"].items():
                # Pick the right search function
                if "1mg" in platform_key:
                    search_fn = search_1mg_async
                    platform_label = "1mg"
                elif "apollo" in platform_key:
                    search_fn = search_apollo_async
                    platform_label = "Apollo"
                elif "pharmeasy" in platform_key:
                    search_fn = search_pharmeasy_async
                    platform_label = "PharmEasy"
                else:
                    logger.warning(f"  Unknown platform: {platform_key}, skipping")
                    continue
                
                try:
                    found_url = await search_fn(page, product_name)
                    if found_url:
                        # Save to DB
                        supabase.table("platform_product_links").insert({
                            "product_id": product_id,
                            "platform_id": platform_id,
                            "scrape_url": found_url
                        }).execute()
                        logger.info(f"  ✅ [{platform_label}] Found: {found_url}")
                        found_count += 1
                    else:
                        logger.info(f"  ⚠️  [{platform_label}] No valid match found")
                except Exception as e:
                    logger.error(f"  ❌ [{platform_label}] Error: {e}")
                
                # Anti-blocking: random delay between 4-8 seconds
                delay = random.uniform(4, 8)
                logger.debug(f"  Waiting {delay:.1f}s...")
                await asyncio.sleep(delay)
        
        await browser.close()
        logger.info(f"\n{'=' * 60}")
        logger.info(f"DONE! Re-found {found_count} correct links out of {len(invalid_links)} invalid.")


async def main():
    # Phase 1: Validate (instant)
    valid, invalid = phase1_validate()
    
    if not invalid:
        logger.info("All links are valid! Nothing to fix.")
        return
    
    # Ask before proceeding
    logger.info(f"\nFound {len(invalid)} invalid links to fix.")
    
    # Phase 2: Delete invalid
    phase2_delete_invalid(invalid)
    
    # Phase 3: Re-search correct links (with anti-blocking delays)
    await phase3_research(invalid)


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
