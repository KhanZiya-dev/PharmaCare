import httpx
import urllib.parse
from typing import Dict, Any, Optional

ZENO_SEARCH_API = "https://zeno-search.zeno.health/api/search"

async def fetch_zeno_price(query: str, client: Optional[httpx.AsyncClient] = None) -> Dict[str, Any]:
    """
    Searches Zeno Health API for a medicine name.
    Returns standard price dictionary and extracts any generic substitutes.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }
    
    encoded_query = urllib.parse.quote(query)
    
    # store_group_id=1 corresponds to a standard region (e.g. Mumbai)
    url = f"{ZENO_SEARCH_API}?term={encoded_query}&term_field=drug_name&search_type=drug_name&response_fields=composition%2Ctype%2Ccompany%2Cpack_value%2Cpack_uom&store_group_id=1&page_number=1&results_size=5&drug_status=Active%2CBanned%2CDiscontinued&source=zeno-app"
    
    should_close_client = False
    if not client:
        client = httpx.AsyncClient()
        should_close_client = True
        
    try:
        response = await client.get(url, headers=headers, timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            if data.get("meta", {}).get("is_error") is False and data.get("data"):
                # Get best match
                results = data["data"]
                
                def names_match(searched_name: str, found_name: str, threshold: float = 0.6) -> bool:
                    import re
                    # Dosage forms and pack patterns to strip
                    dosage_forms = [
                        'tablets', 'tablet', 'tab', 'capsules', 'capsule', 'cap',
                        'syrup', 'suspension', 'solution', 'oral', 'injection', 'inj',
                        'cream', 'gel', 'ointment', 'lotion', 'spray', 'drops', 'drop',
                        'inhaler', 'respules', 'rotacaps', 'powder', 'sachet', 'granules',
                        'patch', 'patches', 'suppository', 'suppositories',
                        'vial', 'ampoule', 'ampule', 'eye', 'ear', 'nasal', 'topical',
                        'forte', 'plus', 'ds', 'sr', 'xr', 'er', 'cr', 'mr', 'xl',
                    ]
                    pack_patterns = [
                        r'strip\s*of\s*\d+', r'pack\s*of\s*\d+', r'bottle\s*of\s*\d+\s*(?:ml|tablets?|capsules?)?',
                        r'box\s*of\s*\d+', r'tube\s*of\s*\d+\s*(?:gm?|g)?', r'\d+\s*(?:ml|gm?|g|mg|mcg|l|kg)\b',
                        r'\d+\s*(?:s|\'s)\b', r'\(\s*\d+[^)]*\)'
                    ]
                    def normalize(n):
                        n = n.lower().strip()
                        for p in pack_patterns: n = re.sub(p, '', n, flags=re.IGNORECASE)
                        for f in dosage_forms: n = re.sub(r'\b' + re.escape(f) + r'\b', '', n, flags=re.IGNORECASE)
                        n = re.sub(r'(\d+)\s*(?:mg|mcg|ml|g|gm|iu|%)\b', r'\1', n)
                        return ' '.join(n.split())
                    
                    s_norm = normalize(searched_name)
                    f_norm = normalize(found_name)
                    if not s_norm or not f_norm: return False
                    
                    s_words = set(re.split(r'[\s\-]+', s_norm))
                    f_words = set(re.split(r'[\s\-]+', f_norm))
                    s_words.discard(''); f_words.discard('')
                    if not s_words: return False
                    
                    return (len(s_words & f_words) / len(s_words)) >= threshold

                match = None
                for r in results:
                    if names_match(query, r.get("drug_name", "")):
                        match = r
                        break
                
                # If no reasonable match is found, treat as unavailable
                if not match:
                    return {"platform": "Zeno Health", "price": 0.0, "in_stock": False, "url": "https://www.zeno.health"}
                
                price_details = match.get("price_details", [])
                selling_price = None
                mrp = None
                if price_details:
                    selling_price = price_details[0].get("selling_rate")
                    mrp = price_details[0].get("mrp")
                
                if not selling_price:
                    return {"platform": "Zeno Health", "price": 0.0, "in_stock": False, "url": "https://www.zeno.health"}
                
                # Construct main product URL
                # Zeno Health's web app currently fails on /product/:slug/:id deep links and redirects to home or shows blank.
                # So we link directly to their search page with the exact drug name.
                main_name = match.get("drug_name", query)
                main_url = f"https://www.zeno.health/search?query={urllib.parse.quote(main_name)}"
                
                # Check for Generic Alternatives
                generics = []
                for alt in match.get("alternate_drugs", []):
                    if alt.get("type", "") == "generic" or alt.get("business_category", {}).get("alias") == "generic":
                        alt_price_details = alt.get("price_details", [])
                        if alt_price_details:
                            alt_price = alt_price_details[0].get("selling_rate")
                            alt_mrp = alt_price_details[0].get("mrp")
                            alt_name = alt.get("drug_name", "")
                            alt_url = f"https://www.zeno.health/search?query={urllib.parse.quote(alt_name)}"
                            
                            generics.append({
                                "name": alt_name,
                                "price": alt_price,
                                "mrp": alt_mrp,
                                "company": alt.get("company_name"),
                                "image_url": alt.get("front_img_url"),
                                "pack": alt.get("pack"),
                                "url": alt_url
                            })
                
                # Sort generics by cheapest price
                generics.sort(key=lambda x: x["price"])
                
                return {
                    "platform": "Zeno Health",
                    "price": round(selling_price, 2),
                    "mrp": round(mrp, 2) if mrp else None,
                    "in_stock": True,
                    "url": main_url,
                    "generics": generics
                }
                
    except Exception as e:
        print(f"[Zeno Scraper] Error fetching {query}: {e}")
    finally:
        if should_close_client:
            await client.aclose()
            
    return {"platform": "Zeno Health", "price": 0.0, "in_stock": False, "url": "https://www.zeno.health"}
