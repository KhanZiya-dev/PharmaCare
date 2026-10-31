import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv("d:/BSc.CS/Sem5/Pharmacare/backend/.env")
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

# Get Dolo 650 product and its 1mg link
dolo_id = "26e46e5a-fec5-4b5a-954f-6d981c95571d"

links = supabase.table("platform_product_links").select(
    "id, scrape_url, last_scraped, platforms(id, name)"
).eq("product_id", dolo_id).execute()

for l in links.data:
    pname = l["platforms"]["name"]
    link_id = l["id"]
    print(f"Platform: {pname}")
    print(f"  Link ID: {link_id}")
    print(f"  URL: {l['scrape_url']}")
    print(f"  Last scraped: {l.get('last_scraped', 'Never')}")
    
    # Get latest price history
    prices = supabase.table("price_history").select(
        "selling_price, mrp, in_stock, is_restricted, scraped_at"
    ).eq("mapping_id", link_id).order("scraped_at", desc=True).limit(3).execute()
    
    if prices.data:
        print(f"  Recent prices ({len(prices.data)}):")
        for p in prices.data:
            print(f"    {p['scraped_at']} | SP: {p['selling_price']} | MRP: {p['mrp']} | Stock: {p['in_stock']} | Restricted: {p['is_restricted']}")
    else:
        print("  NO PRICE HISTORY!")
    print()
