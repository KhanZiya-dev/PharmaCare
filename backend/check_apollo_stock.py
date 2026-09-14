import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv("d:/BSc.CS/Sem5/Pharmacare/backend/.env")
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

def main():
    # 1. Get Apollo Platform ID
    platform_res = supabase.table("platforms").select("id").eq("name", "Apollo Pharmacy").execute()
    if not platform_res.data:
        print("Apollo Pharmacy platform not found.")
        return
    apollo_id = platform_res.data[0]["id"]
    
    # 2. Get all mappings for Apollo
    links_res = supabase.table("platform_product_links").select("id").eq("platform_id", apollo_id).execute()
    mapping_ids = [link["id"] for link in links_res.data]
    print(f"Total Apollo links in DB: {len(mapping_ids)}")
    
    if not mapping_ids:
        return

    # 3. Get latest price history for these mappings
    # For a quick check, just query price_history for these mapping IDs
    # and count in_stock == True vs False
    history_res = supabase.table("price_history").select("mapping_id, in_stock").in_("mapping_id", mapping_ids).execute()
    
    # Keep only the latest entry per mapping ID by assuming the list might have duplicates,
    # though in a real scenario we'd order by scraped_at. We just want a rough count of current status.
    # We can just look at the most recent scraped entries.
    latest_status = {}
    for h in history_res.data:
        latest_status[h["mapping_id"]] = h["in_stock"]
        
    in_stock_count = sum(1 for status in latest_status.values() if status is True)
    out_of_stock_count = sum(1 for status in latest_status.values() if status is False)
    
    print(f"Out of {len(latest_status)} scraped Apollo products:")
    print(f" - In Stock: {in_stock_count}")
    print(f" - Out of Stock: {out_of_stock_count}")

if __name__ == "__main__":
    main()
