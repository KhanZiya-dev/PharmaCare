import os
import time
from dotenv import load_dotenv
from supabase import create_client, Client
from playwright.sync_api import sync_playwright
import urllib.parse

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Missing Supabase credentials")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Platform names based on what's in the DB
PLATFORMS = {
    "PharmEasy": "PharmEasy",
    "Tata 1mg": "Tata 1mg",
    "Apollo Pharmacy": "Apollo Pharmacy"
}

def get_platform_ids():
    response = supabase.table("platforms").select("id, name").execute()
    return {p["name"]: p["id"] for p in response.data}

def search_1mg(page, product_name):
    query = urllib.parse.quote(product_name)
    url = f"https://www.1mg.com/search/all?name={query}"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        time.sleep(2)
        # First drug link
        el = page.locator("a[href*='/drugs/']").first
        if el.count() > 0:
            href = el.get_attribute("href")
            return f"https://www.1mg.com{href}"
    except:
        pass
    return None

def search_pharmeasy(page, product_name):
    query = urllib.parse.quote(product_name)
    url = f"https://pharmeasy.in/search/all?name={query}"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        time.sleep(2)
        # PharmEasy product links usually contain /online-medicine-order/ or /otc/
        for pattern in ["a[href*='/online-medicine-order/']", "a[href*='/otc/']"]:
            el = page.locator(pattern).first
            if el.count() > 0:
                href = el.get_attribute("href")
                return f"https://pharmeasy.in{href}"
    except:
        pass
    return None

def search_apollo(page, product_name):
    query = urllib.parse.quote(product_name)
    url = f"https://www.apollopharmacy.in/search-medicines/{query}"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        time.sleep(2)
        # Apollo product links contain /medicine/ or /otc/
        for pattern in ["a[href*='/medicine/']", "a[href*='/otc/']"]:
            el = page.locator(pattern).first
            if el.count() > 0:
                href = el.get_attribute("href")
                return f"https://www.apollopharmacy.in{href}"
    except:
        pass
    return None

def main():
    platform_ids = get_platform_ids()
    print("Platform IDs:", platform_ids)
    
    # Get top 10 products that have missing links
    # (For simplicity, get products created recently, e.g., the ones we just added)
    res = supabase.table("products").select("id, name").order("created_at", desc=True).limit(10).execute()
    products = res.data
    
    print(f"Testing auto-linker on {len(products)} products...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        for product in products:
            prod_id = product["id"]
            prod_name = product["name"]
            print(f"\nProcessing: {prod_name}")
            
            # Check existing links
            links_res = supabase.table("platform_product_links").select("platform_id").eq("product_id", prod_id).execute()
            existing_platforms = [link["platform_id"] for link in links_res.data]
            
            for plat_name, func in [("Tata 1mg", search_1mg), ("PharmEasy", search_pharmeasy), ("Apollo Pharmacy", search_apollo)]:
                plat_id = platform_ids.get(plat_name)
                if plat_id in existing_platforms:
                    print(f"  [{plat_name}] Link exists.")
                    continue
                
                print(f"  [{plat_name}] Searching...")
                url = func(page, prod_name)
                
                if url:
                    print(f"    FOUND: {url}")
                    # Insert into DB
                    try:
                        supabase.table("platform_product_links").insert({
                            "product_id": prod_id,
                            "platform_id": plat_id,
                            "scrape_url": url,
                            "affiliate_url": url # Fallback
                        }).execute()
                        print("    -> Saved to DB")
                    except Exception as e:
                        print(f"    -> Error saving: {e}")
                else:
                    print("    NOT FOUND")
                    
                time.sleep(2) # Delay to avoid ban
                
        browser.close()
    print("\nAuto-linking complete for batch.")

if __name__ == "__main__":
    main()
