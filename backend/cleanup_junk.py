"""
PharmaCare DB Cleanup
=====================
Deletes junk data identified by audit_junk.py
Run: python backend/cleanup_junk.py
"""
import os
from collections import defaultdict
from supabase import create_client
from dotenv import load_dotenv

load_dotenv("d:/BSc.CS/Sem5/Pharmacare/backend/.env")
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

def fetch_all(table, select="*"):
    all_data = []
    offset = 0
    batch_size = 1000
    while True:
        res = supabase.table(table).select(select).range(offset, offset + batch_size - 1).execute()
        if not res.data:
            break
        all_data.extend(res.data)
        if len(res.data) < batch_size:
            break
        offset += batch_size
    return all_data

def main():
    total_deleted = 0

    # ── 1. Delete products with 0 platform links ──
    print("1. Finding products with 0 platform links...")
    products = fetch_all("products", "id, name")
    links = fetch_all("platform_product_links", "id, product_id")
    
    linked_ids = {l["product_id"] for l in links}
    product_ids = {p["id"] for p in products}
    unlinked_ids = list(product_ids - linked_ids)
    
    if unlinked_ids:
        # Show what we're deleting
        unlinked_names = [p["name"] for p in products if p["id"] in set(unlinked_ids)]
        print(f"   Deleting {len(unlinked_ids)} unlinked products:")
        for name in unlinked_names[:10]:
            print(f"      - {name}")
        if len(unlinked_names) > 10:
            print(f"      ... and {len(unlinked_names) - 10} more")
        
        # Delete in chunks
        chunk_size = 50
        for i in range(0, len(unlinked_ids), chunk_size):
            chunk = unlinked_ids[i:i+chunk_size]
            supabase.table("products").delete().in_("id", chunk).execute()
        print(f"   DELETED {len(unlinked_ids)} products")
        total_deleted += len(unlinked_ids)
    else:
        print("   No unlinked products found.")

    # ── 2. Delete duplicate platform_product_links (keep oldest) ──
    print("\n2. Finding duplicate scrape_urls in platform_product_links...")
    links = fetch_all("platform_product_links", "id, product_id, platform_id, scrape_url, last_scraped")
    
    # Group by (product_id, scrape_url) to find true duplicates
    groups = defaultdict(list)
    for l in links:
        key_tuple = (l.get("product_id"), l.get("scrape_url"))
        groups[key_tuple].append(l)
    
    dupe_ids_to_delete = []
    for key_tuple, group in groups.items():
        if len(group) > 1:
            # Keep the one with most recent last_scraped, delete rest
            group.sort(key=lambda x: x.get("last_scraped") or "", reverse=True)
            for dup in group[1:]:
                dupe_ids_to_delete.append(dup["id"])
    
    if dupe_ids_to_delete:
        print(f"   Found {len(dupe_ids_to_delete)} duplicate links to remove")
        
        # First delete their price_history (CASCADE should handle, but just in case)
        chunk_size = 50
        for i in range(0, len(dupe_ids_to_delete), chunk_size):
            chunk = dupe_ids_to_delete[i:i+chunk_size]
            supabase.table("price_history").delete().in_("mapping_id", chunk).execute()
            supabase.table("platform_product_links").delete().in_("id", chunk).execute()
        print(f"   DELETED {len(dupe_ids_to_delete)} duplicate links + their price history")
        total_deleted += len(dupe_ids_to_delete)
    else:
        print("   No duplicates found.")

    # ── 3. Delete zero/null selling_price records ──
    print("\n3. Finding zero/null selling_price in price_history...")
    zero_prices = supabase.table("price_history").select("id").eq("selling_price", 0).execute()
    null_prices = supabase.table("price_history").select("id").is_("selling_price", "null").execute()
    
    bad_price_ids = [p["id"] for p in (zero_prices.data or []) + (null_prices.data or [])]
    
    if bad_price_ids:
        for i in range(0, len(bad_price_ids), 50):
            chunk = bad_price_ids[i:i+50]
            supabase.table("price_history").delete().in_("id", chunk).execute()
        print(f"   DELETED {len(bad_price_ids)} zero/null price records")
        total_deleted += len(bad_price_ids)
    else:
        print("   No bad price records found.")

    # ── 4. Delete lab tests with 0 links ──
    print("\n4. Finding lab tests with 0 links...")
    lab_tests = fetch_all("lab_tests", "id, name")
    lab_links = fetch_all("platform_lab_test_links", "id, lab_test_id")
    
    linked_lab_ids = {l["lab_test_id"] for l in lab_links}
    lab_ids = {lt["id"] for lt in lab_tests}
    unlinked_lab_ids = list(lab_ids - linked_lab_ids)
    
    if unlinked_lab_ids:
        unlinked_lab_names = [lt["name"] for lt in lab_tests if lt["id"] in set(unlinked_lab_ids)]
        print(f"   Deleting {len(unlinked_lab_ids)} unlinked lab tests:")
        for name in unlinked_lab_names:
            print(f"      - {name}")
        
        supabase.table("lab_tests").delete().in_("id", unlinked_lab_ids).execute()
        print(f"   DELETED {len(unlinked_lab_ids)} lab tests")
        total_deleted += len(unlinked_lab_ids)
    else:
        print("   No unlinked lab tests found.")

    # ── DONE ──
    print("\n" + "=" * 50)
    print(f"CLEANUP COMPLETE - Total deleted: {total_deleted} rows")
    print("=" * 50)

if __name__ == "__main__":
    main()
