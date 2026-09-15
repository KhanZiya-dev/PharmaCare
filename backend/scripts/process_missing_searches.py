import os
import time
import urllib.parse
from dotenv import load_dotenv
from supabase import create_client, Client
from playwright.sync_api import sync_playwright

load_dotenv("d:/BSc.CS/Sem5/Pharmacare/backend/.env")

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
        for pattern in ["a[href*='/medicine/']", "a[href*='/otc/']"]:
            el = page.locator(pattern).first
            if el.count() > 0:
                href = el.get_attribute("href")
                return f"https://www.apollopharmacy.in{href}"
    except:
        pass
    return None

def generate_slug(name: str):
    import re
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    return slug.strip('-')

def main():
    platform_ids = get_platform_ids()
    
    res = supabase.table("missing_searches").select("*").eq("status", "pending").execute()
    missing_items = res.data
    
    if not missing_items:
        print("No pending missing searches found.")
        return
        
    print(f"Found {len(missing_items)} pending missing searches.")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        for item in missing_items:
            search_query = item["search_query"]
            item_id = item["id"]
            print(f"\nProcessing: {search_query}")
            
            found_links = {}
            
            for plat_name, func in [("Tata 1mg", search_1mg), ("PharmEasy", search_pharmeasy), ("Apollo Pharmacy", search_apollo)]:
                plat_id = platform_ids.get(plat_name)
                print(f"  [{plat_name}] Searching...")
                url = func(page, search_query)
                
                if url:
                    print(f"    FOUND: {url}")
                    found_links[plat_id] = url
                else:
                    print("    NOT FOUND")
                    
                time.sleep(2) # Delay to avoid ban
                
            if found_links:
                print(f"  => Found {len(found_links)} links. Adding to products table...")
                slug = generate_slug(search_query)
                
                # Check if product already exists by slug (just in case)
                check_res = supabase.table("products").select("id").eq("slug", slug).execute()
                
                if check_res.data:
                    prod_id = check_res.data[0]["id"]
                    print("     (Product already exists in DB, using existing ID)")
                else:
                    try:
                        # Create new product
                        prod_res = supabase.table("products").insert({
                            "name": search_query.title(),
                            "slug": slug,
                            "category": "Prescription" if item.get("search_type") == "vision" else "General"
                        }).execute()
                        prod_id = prod_res.data[0]["id"]
                    except Exception as e:
                        print(f"     Error creating product: {e}")
                        continue
                        
                # Add links
                for p_id, p_url in found_links.items():
                    try:
                        # Check if link exists
                        link_check = supabase.table("platform_product_links").select("id").eq("product_id", prod_id).eq("platform_id", p_id).execute()
                        if not link_check.data:
                            supabase.table("platform_product_links").insert({
                                "product_id": prod_id,
                                "platform_id": p_id,
                                "scrape_url": p_url,
                                "affiliate_url": p_url
                            }).execute()
                    except Exception as e:
                        print(f"     Error adding link: {e}")
                
                # Update missing_searches status
                supabase.table("missing_searches").update({"status": "added"}).eq("id", item_id).execute()
                print("  => Status updated to 'added'")
            else:
                print("  => NO links found at all. Marking as 'not_available_online'")
                supabase.table("missing_searches").update({"status": "not_available_online"}).eq("id", item_id).execute()
                
        browser.close()
    print("\nProcessing complete.")

if __name__ == "__main__":
    main()
