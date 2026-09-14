import os
import time
from dotenv import load_dotenv
from supabase import create_client, Client
from playwright.sync_api import sync_playwright
import urllib.parse
from collections import Counter
import json

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Missing Supabase credentials")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
        el = page.locator("a[href*='/drugs/']").first
        if el.count() > 0:
            href = el.get_attribute("href")
            return f"https://www.1mg.com{href}"
    except Exception as e:
        pass
    return None

def search_pharmeasy(page, product_name):
    query = urllib.parse.quote(product_name)
    url = f"https://pharmeasy.in/search/all?name={query}"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        time.sleep(2)
        for pattern in ["a[href*='/online-medicine-order/']", "a[href*='/otc/']"]:
            el = page.locator(pattern).first
            if el.count() > 0:
                href = el.get_attribute("href")
                return f"https://pharmeasy.in{href}"
    except Exception as e:
        pass
    return None

def search_apollo(page, product_name):
    query = urllib.parse.quote(product_name)
    url = f"https://www.apollopharmacy.in/search-medicines/{query}"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        time.sleep(2)
        for pattern in ["a[href*='/medicine/']", "a[href*='/otc/']"]:
            el = page.locator(pattern).first
            if el.count() > 0:
                href = el.get_attribute("href")
                return f"https://www.apollopharmacy.in{href}"
    except Exception as e:
        pass
    return None

def main(batch_size=5):
    platform_ids = get_platform_ids()
    print("Platform IDs:", platform_ids)
    
    processed_file = "processed_products.json"
    processed_ids = []
    if os.path.exists(processed_file):
        with open(processed_file, "r") as f:
            processed_ids = json.load(f)
    
    # Fetch all links to find products with less than 3 links
    res = supabase.table("platform_product_links").select("product_id").execute()
    counts = Counter(r["product_id"] for r in res.data)
    
    # Products with 1 or 2 links that haven't been processed yet
    incomplete_product_ids = [pid for pid, c in counts.items() if c < 3 and pid not in processed_ids]
    
    if not incomplete_product_ids:
        print("All products have 3 links!")
        return

    # Take a batch
    batch_ids = incomplete_product_ids[:batch_size]
    
    # Fetch product details for the batch
    products_res = supabase.table("products").select("id, name").in_("id", batch_ids).execute()
    products = products_res.data
    
    print(f"Processing a batch of {len(products)} products...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        for product in products:
            prod_id = product["id"]
            prod_name = product["name"]
            print(f"\nProcessing: {prod_name}")
            
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
                    try:
                        supabase.table("platform_product_links").insert({
                            "product_id": prod_id,
                            "platform_id": plat_id,
                            "scrape_url": url,
                            "affiliate_url": url
                        }).execute()
                        print("    -> Saved to DB")
                    except Exception as e:
                        print(f"    -> Error saving: {e}")
                else:
                    print("    NOT FOUND")
                    
                time.sleep(2) # Delay to avoid ban
            
            # Mark as processed
            processed_ids.append(prod_id)
            with open(processed_file, "w") as f:
                json.dump(processed_ids, f)
                
        browser.close()
    print("\nBatch linking complete!")

if __name__ == "__main__":
    import sys
    batch = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    main(batch)
