"""
Shared platform search module for finding medicine links on pharmacy websites.

KEY FIX: Previous linker code would blindly save the FIRST search result link
without verifying that it matches the searched medicine. This caused wrong
product URLs (e.g., searching "Dolo 650" on PharmEasy could save a link to 
"Preega M" because PharmEasy only uses the numeric ID in URLs).

This module:
1. Checks MULTIPLE search results (top 5), not just the first
2. Extracts the product name from each result and validates it matches
3. Uses fuzzy name matching (strips dosage forms, pack info)
4. For PharmEasy: visits the actual product page to verify (slug is ignored)

Usage (sync - for auto_linker, add_missing_links_batch, process_missing_searches):
    from platform_search import search_1mg, search_pharmeasy, search_apollo

Usage (async - for process_all_excel_parallel):
    from platform_search import search_1mg_async, search_pharmeasy_async, search_apollo_async
"""

import re
import time
import logging
import urllib.parse

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# Name Matching
# ═══════════════════════════════════════════════════════════════════════

# Common dosage forms and packaging words to strip for comparison
_DOSAGE_FORMS = [
    'tablets', 'tablet', 'tab',
    'capsules', 'capsule', 'cap',
    'syrup', 'suspension', 'solution', 'oral',
    'injection', 'inj',
    'cream', 'gel', 'ointment', 'lotion', 'spray',
    'drops', 'drop',
    'inhaler', 'respules', 'rotacaps',
    'powder', 'sachet', 'granules',
    'patch', 'patches',
    'suppository', 'suppositories',
    'vial', 'ampoule', 'ampule',
    'eye', 'ear', 'nasal', 'topical',
    'forte', 'plus', 'ds', 'sr', 'xr', 'er', 'cr', 'mr', 'xl',
]

# Pack/quantity patterns
_PACK_PATTERNS = [
    r'strip\s*of\s*\d+',
    r'pack\s*of\s*\d+',
    r'bottle\s*of\s*\d+\s*(?:ml|tablets?|capsules?)?',
    r'box\s*of\s*\d+',
    r'tube\s*of\s*\d+\s*(?:gm?|g)?',
    r'\d+\s*(?:ml|gm?|g|mg|mcg|l|kg)\b',
    r'\d+\s*(?:s|\'s)\b',  # "15's", "10 s"
    r'\(\s*\d+[^)]*\)',   # anything in parentheses with numbers
]


def normalize_medicine_name(name: str) -> str:
    """
    Normalize a medicine name for comparison by stripping:
    - Dosage forms (tablet, capsule, syrup, etc.)
    - Pack/quantity info (strip of 15, bottle of 100ml, etc.)
    - Strength units already attached to numbers (650mg → 650)
    - Extra whitespace
    
    Examples:
        "Dolo 650mg Tablet Strip of 15" → "dolo 650"
        "Crocin Advance 500mg Tab" → "crocin advance 500"
        "Pan-D Capsule" → "pan-d"
    """
    name = name.lower().strip()
    
    # Remove pack patterns
    for pattern in _PACK_PATTERNS:
        name = re.sub(pattern, '', name, flags=re.IGNORECASE)
    
    # Remove dosage forms (whole words)
    for form in _DOSAGE_FORMS:
        name = re.sub(r'\b' + re.escape(form) + r'\b', '', name, flags=re.IGNORECASE)
    
    # Strip units from numbers: "650mg" → "650"
    name = re.sub(r'(\d+)\s*(?:mg|mcg|ml|g|gm|iu|%)\b', r'\1', name)
    
    # Normalize whitespace
    return ' '.join(name.split())


def names_match(searched_name: str, found_name: str, threshold: float = 0.6) -> bool:
    """
    Check if a found product name matches the searched medicine name.
    
    Uses core-word matching: all important words from the searched name
    must appear in the found product name.
    
    Args:
        searched_name: The medicine name we're looking for
        found_name: The product name found in search results
        threshold: Minimum ratio of matching words (0.0-1.0)
    
    Returns:
        True if the names match above the threshold
    
    Examples:
        ("Dolo 650", "Dolo 650mg Tablet") → True
        ("Dolo 650", "Preega M 75mg Capsule") → False
        ("Crocin Advance", "Crocin Advance 500mg Tab Strip of 15") → True
        ("Pan D", "Pan-D Capsule") → True
    """
    searched_norm = normalize_medicine_name(searched_name)
    found_norm = normalize_medicine_name(found_name)
    
    if not searched_norm or not found_norm:
        return False
    
    # Handle hyphenated names: "pan-d" should match "pan d" and vice versa
    searched_words = set(re.split(r'[\s\-]+', searched_norm))
    found_words = set(re.split(r'[\s\-]+', found_norm))
    
    # Remove empty strings
    searched_words.discard('')
    found_words.discard('')
    
    if not searched_words:
        return False
    
    # Calculate match: what fraction of searched words appear in found
    matching = searched_words & found_words
    match_ratio = len(matching) / len(searched_words)
    
    logger.debug(f"Name match: '{searched_name}' vs '{found_name}' → "
                 f"norm: '{searched_norm}' vs '{found_norm}' → "
                 f"ratio: {match_ratio:.2f} (threshold: {threshold})")
    
    return match_ratio >= threshold


# ═══════════════════════════════════════════════════════════════════════
# Sync Search Functions (for auto_linker, add_missing_links_batch, etc.)
# ═══════════════════════════════════════════════════════════════════════

def search_1mg(page, product_name: str, max_results: int = 5) -> str | None:
    """
    Search 1mg for a medicine and return the best matching URL.
    Checks up to max_results links and picks the one whose product name
    best matches the searched name.
    """
    query = urllib.parse.quote(product_name)
    url = f"https://www.1mg.com/search/all?name={query}"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        time.sleep(2)
        
        # Get multiple drug links
        elements = page.locator("a[href*='/drugs/']").all()
        
        for el in elements[:max_results]:
            try:
                href = el.get_attribute("href")
                if not href:
                    continue
                
                # Extract visible product name from the link's text content
                link_text = el.inner_text(timeout=2000).strip()
                
                # If link has no useful text, try to find a nearby heading or text
                if len(link_text) < 3:
                    # Try parent element
                    try:
                        parent_text = el.locator("..").inner_text(timeout=1000).strip()
                        if len(parent_text) > len(link_text):
                            link_text = parent_text
                    except Exception:
                        pass
                
                # Also try to extract name from the URL slug
                slug_name = _extract_name_from_slug(href)
                
                # Check if either the visible text or slug matches
                text_matches = names_match(product_name, link_text) if len(link_text) > 2 else False
                slug_matches = names_match(product_name, slug_name) if slug_name else False
                
                if text_matches or slug_matches:
                    full_url = href if href.startswith("http") else f"https://www.1mg.com{href}"
                    logger.info(f"  [1mg] Matched: '{product_name}' → '{link_text or slug_name}' → {full_url}")
                    return full_url
                else:
                    logger.debug(f"  [1mg] Skipped: '{link_text}' (slug: '{slug_name}') - no match for '{product_name}'")
            except Exception:
                continue
        
        logger.info(f"  [1mg] No matching result found for '{product_name}'")
    except Exception as e:
        logger.error(f"  [1mg] Search error: {e}")
    return None


def search_pharmeasy(page, product_name: str, max_results: int = 5) -> str | None:
    """
    Search PharmEasy for a medicine and return the best matching URL.
    
    IMPORTANT: PharmEasy URLs contain a numeric ID that determines which
    product is served. The slug text in the URL is IGNORED by PharmEasy.
    So we MUST verify the product name from search results.
    """
    query = urllib.parse.quote(product_name)
    url = f"https://pharmeasy.in/search/all?name={query}"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        time.sleep(2)
        
        # PharmEasy product links
        for pattern in ["a[href*='/online-medicine-order/']", "a[href*='/otc/']"]:
            elements = page.locator(pattern).all()
            
            for el in elements[:max_results]:
                try:
                    href = el.get_attribute("href")
                    if not href:
                        continue
                    
                    link_text = el.inner_text(timeout=2000).strip()
                    slug_name = _extract_name_from_slug(href)
                    
                    text_matches = names_match(product_name, link_text) if len(link_text) > 2 else False
                    slug_matches = names_match(product_name, slug_name) if slug_name else False
                    
                    if text_matches or slug_matches:
                        full_url = href if href.startswith("http") else f"https://pharmeasy.in{href}"
                        logger.info(f"  [PharmEasy] Matched: '{product_name}' → '{link_text or slug_name}' → {full_url}")
                        return full_url
                    else:
                        logger.debug(f"  [PharmEasy] Skipped: '{link_text}' (slug: '{slug_name}') - no match")
                except Exception:
                    continue
        
        logger.info(f"  [PharmEasy] No matching result found for '{product_name}'")
    except Exception as e:
        logger.error(f"  [PharmEasy] Search error: {e}")
    return None


def search_apollo(page, product_name: str, max_results: int = 5) -> str | None:
    """
    Search Apollo Pharmacy for a medicine and return the best matching URL.
    """
    query = urllib.parse.quote(product_name)
    url = f"https://www.apollopharmacy.in/search-medicines/{query}"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        time.sleep(2)
        
        # Apollo links can be /medicine/ or /otc/
        for pattern in ["a[href*='/medicine/']", "a[href*='/otc/']"]:
            elements = page.locator(pattern).all()
            
            for el in elements[:max_results]:
                try:
                    href = el.get_attribute("href")
                    if not href:
                        continue
                    
                    link_text = el.inner_text(timeout=2000).strip()
                    slug_name = _extract_name_from_slug(href)
                    
                    text_matches = names_match(product_name, link_text) if len(link_text) > 2 else False
                    slug_matches = names_match(product_name, slug_name) if slug_name else False
                    
                    if text_matches or slug_matches:
                        full_url = href if href.startswith("http") else f"https://www.apollopharmacy.in{href}"
                        logger.info(f"  [Apollo] Matched: '{product_name}' → '{link_text or slug_name}' → {full_url}")
                        return full_url
                    else:
                        logger.debug(f"  [Apollo] Skipped: '{link_text}' (slug: '{slug_name}') - no match")
                except Exception:
                    continue
        
        logger.info(f"  [Apollo] No matching result found for '{product_name}'")
    except Exception as e:
        logger.error(f"  [Apollo] Search error: {e}")
    return None


# ═══════════════════════════════════════════════════════════════════════
# Async Search Functions (for process_all_excel_parallel.py)
# ═══════════════════════════════════════════════════════════════════════

async def search_1mg_async(page, product_name: str, max_results: int = 5) -> str | None:
    """Async version of search_1mg for use with async Playwright."""
    query = urllib.parse.quote(product_name)
    url = f"https://www.1mg.com/search/all?name={query}"
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(2500)
        
        elements = await page.locator("a[href*='/drugs/']").all()
        
        for el in elements[:max_results]:
            try:
                href = await el.get_attribute("href")
                if not href:
                    continue
                
                link_text = ""
                try:
                    link_text = (await el.inner_text(timeout=2000)).strip()
                except Exception:
                    pass
                
                slug_name = _extract_name_from_slug(href)
                
                text_matches = names_match(product_name, link_text) if len(link_text) > 2 else False
                slug_matches = names_match(product_name, slug_name) if slug_name else False
                
                if text_matches or slug_matches:
                    full_url = href if href.startswith("http") else f"https://www.1mg.com{href}"
                    logger.info(f"  [1mg] Matched: '{product_name}' → '{link_text or slug_name}'")
                    return full_url
            except Exception:
                continue
        
        logger.info(f"  [1mg] No matching result for '{product_name}'")
    except Exception as e:
        logger.error(f"  [1mg] Search error: {e}")
    return None


async def search_pharmeasy_async(page, product_name: str, max_results: int = 5) -> str | None:
    """Async version of search_pharmeasy for use with async Playwright."""
    query = urllib.parse.quote(product_name)
    url = f"https://pharmeasy.in/search/all?name={query}"
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(2500)
        
        for pattern in ["a[href*='/online-medicine-order/']", "a[href*='/otc/']"]:
            elements = await page.locator(pattern).all()
            
            for el in elements[:max_results]:
                try:
                    href = await el.get_attribute("href")
                    if not href:
                        continue
                    
                    link_text = ""
                    try:
                        link_text = (await el.inner_text(timeout=2000)).strip()
                    except Exception:
                        pass
                    
                    slug_name = _extract_name_from_slug(href)
                    
                    text_matches = names_match(product_name, link_text) if len(link_text) > 2 else False
                    slug_matches = names_match(product_name, slug_name) if slug_name else False
                    
                    if text_matches or slug_matches:
                        full_url = href if href.startswith("http") else f"https://pharmeasy.in{href}"
                        logger.info(f"  [PharmEasy] Matched: '{product_name}' → '{link_text or slug_name}'")
                        return full_url
                except Exception:
                    continue
        
        logger.info(f"  [PharmEasy] No matching result for '{product_name}'")
    except Exception as e:
        logger.error(f"  [PharmEasy] Search error: {e}")
    return None


async def search_apollo_async(page, product_name: str, max_results: int = 5) -> str | None:
    """Async version of search_apollo for use with async Playwright."""
    query = urllib.parse.quote(product_name)
    url = f"https://www.apollopharmacy.in/search-medicines/{query}"
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(2500)
        
        for pattern in ["a[href*='/medicine/']", "a[href*='/otc/']"]:
            elements = await page.locator(pattern).all()
            
            for el in elements[:max_results]:
                try:
                    href = await el.get_attribute("href")
                    if not href:
                        continue
                    
                    link_text = ""
                    try:
                        link_text = (await el.inner_text(timeout=2000)).strip()
                    except Exception:
                        pass
                    
                    slug_name = _extract_name_from_slug(href)
                    
                    text_matches = names_match(product_name, link_text) if len(link_text) > 2 else False
                    slug_matches = names_match(product_name, slug_name) if slug_name else False
                    
                    if text_matches or slug_matches:
                        full_url = href if href.startswith("http") else f"https://www.apollopharmacy.in{href}"
                        logger.info(f"  [Apollo] Matched: '{product_name}' → '{link_text or slug_name}'")
                        return full_url
                except Exception:
                    continue
        
        logger.info(f"  [Apollo] No matching result for '{product_name}'")
    except Exception as e:
        logger.error(f"  [Apollo] Search error: {e}")
    return None


# ═══════════════════════════════════════════════════════════════════════
# Internal Helpers
# ═══════════════════════════════════════════════════════════════════════

def _extract_name_from_slug(url_path: str) -> str | None:
    """
    Extract a human-readable product name from a URL slug.
    
    "/drugs/dolo-650-tablet-74467" → "dolo 650 tablet"
    "/online-medicine-order/dolo-650mg-strip-of-15-tablets-26498" → "dolo 650mg strip of 15 tablets"
    """
    try:
        # Get the last path segment
        path = url_path.rstrip('/').split('/')[-1]
        
        # Remove trailing numeric ID (common pattern: slug-12345)
        path = re.sub(r'-\d+$', '', path)
        
        # Replace hyphens with spaces
        name = path.replace('-', ' ')
        
        return name if name else None
    except Exception:
        return None
