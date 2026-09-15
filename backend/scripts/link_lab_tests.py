import os
import time
import logging
from dotenv import load_dotenv
from supabase import create_client
from googlesearch import search

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load env
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(env_path)

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(supabase_url, supabase_key)

PLATFORM_DOMAINS = {
    "Agilus Diagnostics": "agilusdiagnostics.com",
    "Metropolis": "metropolisindia.com",
    "General Diagnostics": "generaldiagnostics.in",
    "Thyrocare": "thyrocare.com",
    "Lal PathLabs": "lalpathlabs.com"
}

def link_lab_tests():
    # 1. Get platforms
    platforms_res = supabase.table("platforms").select("id, name").execute()
    platform_map = {p["name"]: p["id"] for p in platforms_res.data if p["name"] in PLATFORM_DOMAINS}
    
    # 2. Get lab tests
    products_res = supabase.table("products").select("id, name").eq("category", "lab_test").execute()
    lab_tests = products_res.data
    
    logger.info(f"Found {len(lab_tests)} lab tests and {len(platform_map)} platforms.")
    
    for test in lab_tests:
        prod_id = test["id"]
        prod_name = test["name"]
        logger.info(f"\nProcessing Test: {prod_name}")
        
        # Check existing links
        links_res = supabase.table("platform_product_links").select("platform_id").eq("product_id", prod_id).execute()
        existing_plat_ids = [l["platform_id"] for l in links_res.data]
        
        for plat_name, plat_domain in PLATFORM_DOMAINS.items():
            plat_id = platform_map.get(plat_name)
            if not plat_id:
                continue
                
            if plat_id in existing_plat_ids:
                logger.info(f"  [{plat_name}] Link already exists.")
                continue
                
            # Perform Google Search to bypass bot protection
            query = f"site:{plat_domain} {prod_name} test"
            logger.info(f"  [{plat_name}] Searching Google: {query}")
            
            try:
                # Return the first search result
                results = list(search(query, num_results=1, sleep_interval=2))
                found_url = None
                
                # Filter out obvious non-product links if needed
                for url in results:
                    if plat_domain in url:
                        found_url = url
                        break
                
                if found_url:
                    logger.info(f"    FOUND: {found_url}")
                    supabase.table("platform_product_links").insert({
                        "product_id": prod_id,
                        "platform_id": plat_id,
                        "scrape_url": found_url,
                        "affiliate_url": found_url
                    }).execute()
                    logger.info("    -> Saved to DB")
                else:
                    logger.info("    -> No matching URL found.")
                
            except Exception as e:
                logger.error(f"    -> Search failed: {e}")
                
            time.sleep(3) # To prevent Google IP ban

if __name__ == "__main__":
    link_lab_tests()
