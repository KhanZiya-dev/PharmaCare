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
                
                # Try to find a reasonable match
                match = None
                query_lower = query.lower()
                for r in results:
                    drug_name = r.get("drug_name", "").lower()
                    if query_lower in drug_name or drug_name in query_lower:
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
                main_slug = match.get("drug_name", "").replace(" ", "-").replace("/", "-")
                main_id = match.get("id")
                main_url = f"https://www.zeno.health/product/{main_slug}/{main_id}" if main_slug and main_id else f"https://www.zeno.health/search?query={urllib.parse.quote(query)}"
                
                # Check for Generic Alternatives
                generics = []
                for alt in match.get("alternate_drugs", []):
                    if alt.get("type", "") == "generic" or alt.get("business_category", {}).get("alias") == "generic":
                        alt_price_details = alt.get("price_details", [])
                        if alt_price_details:
                            alt_price = alt_price_details[0].get("selling_rate")
                            alt_mrp = alt_price_details[0].get("mrp")
                            alt_slug = alt.get("drug_name", "").replace(" ", "-").replace("/", "-")
                            alt_id = alt.get("id")
                            alt_url = f"https://www.zeno.health/product/{alt_slug}/{alt_id}" if alt_slug and alt_id else f"https://www.zeno.health/search?query={urllib.parse.quote(alt.get('drug_name', ''))}"
                            
                            generics.append({
                                "name": alt.get("drug_name"),
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
