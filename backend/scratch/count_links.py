"""Count products and links in the database."""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

# Get all products
products_res = supabase.table("products").select("id, name, category").execute()
products = products_res.data
total_products = len(products)

medicines = [p for p in products if p.get("category") == "medicine" or not p.get("category")]
lab_tests = [p for p in products if p.get("category") == "lab_test"]

print(f"Total Products: {total_products}")
print(f"  - Medicines: {len(medicines)}")
print(f"  - Lab Tests: {len(lab_tests)}")

# Get all links
links_res = supabase.table("platform_product_links").select("product_id, platform_id").execute()
links = links_res.data

# Group links by product
from collections import defaultdict
product_links = defaultdict(set)
for link in links:
    product_links[link["product_id"]].add(link["platform_id"])

# Count products with at least 1 link
linked_products = len(product_links)
medicines_with_links = sum(1 for p in medicines if p["id"] in product_links)
lab_tests_with_links = sum(1 for p in lab_tests if p["id"] in product_links)

print("\n--- LINK STATISTICS ---")
print(f"Products with AT LEAST ONE link: {linked_products} / {total_products}")
print(f"Medicines with links: {medicines_with_links} / {len(medicines)}")
print(f"Lab tests with links: {lab_tests_with_links} / {len(lab_tests)}")

# Count platforms per product
perfect_medicines = sum(1 for p in medicines if len(product_links[p["id"]]) >= 3)
missing_one = sum(1 for p in medicines if len(product_links[p["id"]]) == 2)
missing_two = sum(1 for p in medicines if len(product_links[p["id"]]) == 1)
zero_links = len(medicines) - medicines_with_links

print("\n--- MEDICINE COMPLETENESS ---")
print(f"Medicines with 3+ links (Complete): {perfect_medicines}")
print(f"Medicines with 2 links: {missing_one}")
print(f"Medicines with 1 link: {missing_two}")
print(f"Medicines with 0 links: {zero_links}")

# Count links per platform
platforms_res = supabase.table("platforms").select("id, name").execute()
platform_map = {p["id"]: p["name"] for p in platforms_res.data}

platform_counts = defaultdict(int)
for link in links:
    platform_counts[link["platform_id"]] += 1

print("\n--- LINKS PER PLATFORM ---")
for pid, count in sorted(platform_counts.items(), key=lambda x: x[1], reverse=True):
    pname = platform_map.get(pid, f"Unknown ({pid})")
    print(f"{pname}: {count} links")
