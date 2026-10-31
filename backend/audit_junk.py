"""
PharmaCare DB Junk Audit
========================
Checks all tables for junk data and reports findings.
Run: python backend/audit_junk.py
"""
import os
from collections import Counter
from supabase import create_client
from dotenv import load_dotenv

load_dotenv("d:/BSc.CS/Sem5/Pharmacare/backend/.env")
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

def fetch_all(table, select="*"):
    """Fetch all rows from a table, handling pagination."""
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
    print("=" * 60)
    print("PharmaCare DB Junk Audit")
    print("=" * 60)

    # ── 1. Products Table ──
    print("\n📦 PRODUCTS TABLE")
    products = fetch_all("products", "id, name, slug, composition, image_url, category")
    print(f"  Total products: {len(products)}")

    # Products with no name or empty name
    no_name = [p for p in products if not p.get("name") or p["name"].strip() == ""]
    print(f"  ❌ No name / empty name: {len(no_name)}")

    # Products with no slug
    no_slug = [p for p in products if not p.get("slug") or p["slug"].strip() == ""]
    print(f"  ❌ No slug / empty slug: {len(no_slug)}")

    # Products with no composition
    no_comp = [p for p in products if not p.get("composition") or p["composition"].strip() == ""]
    print(f"  ⚠️  No composition: {len(no_comp)}")

    # Products with no image
    no_image = [p for p in products if not p.get("image_url")]
    print(f"  ⚠️  No image_url: {len(no_image)}")

    # Duplicate names
    name_counts = Counter(p["name"].strip().lower() for p in products if p.get("name"))
    dupes = {name: count for name, count in name_counts.items() if count > 1}
    print(f"  ⚠️  Duplicate names: {len(dupes)} names ({sum(dupes.values())} total rows)")
    if dupes:
        for name, count in sorted(dupes.items(), key=lambda x: -x[1])[:10]:
            print(f"      '{name}' → {count} copies")

    # Junk names (too short, numeric-only, special chars only)
    junk_names = [p for p in products if p.get("name") and (
        len(p["name"].strip()) < 3 or
        p["name"].strip().isdigit() or
        all(c in "!@#$%^&*()-_=+[]{}|;:',.<>?/" for c in p["name"].strip())
    )]
    print(f"  ❌ Junk names (< 3 chars / numeric / symbols): {len(junk_names)}")
    for p in junk_names[:10]:
        print(f"      '{p['name']}' (id: {p['id'][:8]}...)")

    # ── 2. Platform Product Links ──
    print("\n🔗 PLATFORM PRODUCT LINKS")
    links = fetch_all("platform_product_links", "id, product_id, platform_id, scrape_url")
    print(f"  Total links: {len(links)}")

    product_ids = {p["id"] for p in products}

    # Orphan links (product doesn't exist)
    orphan_links = [l for l in links if l.get("product_id") not in product_ids]
    print(f"  ❌ Orphan links (product deleted): {len(orphan_links)}")

    # Products with zero links (no price data possible)
    linked_product_ids = {l["product_id"] for l in links}
    unlinked = product_ids - linked_product_ids
    print(f"  ❌ Products with 0 links: {len(unlinked)}")

    # Duplicate scrape URLs
    url_counts = Counter(l.get("scrape_url", "") for l in links)
    dupe_urls = {url: count for url, count in url_counts.items() if count > 1 and url}
    print(f"  ⚠️  Duplicate scrape_urls: {len(dupe_urls)}")
    for url_str, count in sorted(dupe_urls.items(), key=lambda x: -x[1])[:5]:
        print(f"      {url_str[:80]}... → {count} copies")

    # Empty scrape URLs
    empty_urls = [l for l in links if not l.get("scrape_url") or l["scrape_url"].strip() == ""]
    print(f"  ❌ Empty scrape_url: {len(empty_urls)}")

    # ── 3. Price History ──
    print("\n💰 PRICE HISTORY")
    # Just get counts and check for junk prices
    price_data = fetch_all("price_history", "id, mapping_id, mrp, selling_price, discount_pct, in_stock, scraped_at")
    print(f"  Total records: {len(price_data)}")

    mapping_ids = {l["id"] for l in links}

    # Orphan price records (link doesn't exist)
    orphan_prices = [p for p in price_data if p.get("mapping_id") not in mapping_ids]
    print(f"  ❌ Orphan price records (link deleted): {len(orphan_prices)}")

    # Zero or null selling price
    zero_price = [p for p in price_data if not p.get("selling_price") or p["selling_price"] == 0]
    print(f"  ❌ Zero/null selling_price: {len(zero_price)}")

    # Selling price > MRP (data error)
    bad_prices = [p for p in price_data if p.get("selling_price") and p.get("mrp") and p["selling_price"] > p["mrp"]]
    print(f"  ⚠️  selling_price > MRP: {len(bad_prices)}")

    # Negative discount
    neg_disc = [p for p in price_data if p.get("discount_pct") and p["discount_pct"] < 0]
    print(f"  ⚠️  Negative discount: {len(neg_disc)}")

    # ── 4. Lab Tests ──
    print("\n🧪 LAB TESTS")
    lab_tests = fetch_all("lab_tests", "id, name, slug")
    print(f"  Total lab tests: {len(lab_tests)}")

    lab_links = fetch_all("platform_lab_test_links", "id, lab_test_id, scrape_url")
    print(f"  Total lab test links: {len(lab_links)}")

    lab_ids = {lt["id"] for lt in lab_tests}
    linked_lab_ids = {l["lab_test_id"] for l in lab_links}
    unlinked_labs = lab_ids - linked_lab_ids
    print(f"  ❌ Lab tests with 0 links: {len(unlinked_labs)}")

    # Duplicate lab test names
    lab_name_counts = Counter(lt["name"].strip().lower() for lt in lab_tests if lt.get("name"))
    lab_dupes = {name: count for name, count in lab_name_counts.items() if count > 1}
    print(f"  ⚠️  Duplicate lab test names: {len(lab_dupes)}")
    for name, count in sorted(lab_dupes.items(), key=lambda x: -x[1])[:5]:
        print(f"      '{name}' → {count} copies")

    # Lab test price history
    lab_prices = fetch_all("lab_test_price_history", "id, mapping_id, selling_price")
    print(f"  Total lab price records: {len(lab_prices)}")
    lab_zero = [p for p in lab_prices if not p.get("selling_price") or p["selling_price"] == 0]
    print(f"  ❌ Zero/null lab selling_price: {len(lab_zero)}")

    # ── 5. Missing Searches ──
    print("\n🔍 MISSING SEARCHES")
    missing = fetch_all("missing_searches", "id, search_query, status, search_type")
    print(f"  Total: {len(missing)}")

    status_counts = Counter(m.get("status", "unknown") for m in missing)
    for status, count in status_counts.items():
        print(f"  Status '{status}': {count}")

    # Already processed searches still sitting in table
    processed = [m for m in missing if m.get("status") in ("processed", "completed", "found", "done")]
    print(f"  ⚠️  Processed but not cleaned up: {len(processed)}")

    # Junk search queries
    junk_searches = [m for m in missing if m.get("search_query") and (
        len(m["search_query"].strip()) < 2 or
        m["search_query"].strip().isdigit()
    )]
    print(f"  ❌ Junk search queries (< 2 chars / numeric): {len(junk_searches)}")
    for m in junk_searches[:10]:
        print(f"      '{m['search_query']}' (status: {m.get('status')})")

    # ── SUMMARY ──
    print("\n" + "=" * 60)
    print("JUNK SUMMARY — Safe to Delete")
    print("=" * 60)
    
    total_junk = 0
    
    if junk_names:
        print(f"  🗑️  {len(junk_names)} junk-named products")
        total_junk += len(junk_names)
    if unlinked:
        print(f"  🗑️  {len(unlinked)} products with 0 platform links")
        total_junk += len(unlinked)
    if orphan_links:
        print(f"  🗑️  {len(orphan_links)} orphan platform_product_links")
        total_junk += len(orphan_links)
    if empty_urls:
        print(f"  🗑️  {len(empty_urls)} links with empty scrape_url")
        total_junk += len(empty_urls)
    if orphan_prices:
        print(f"  🗑️  {len(orphan_prices)} orphan price_history records")
        total_junk += len(orphan_prices)
    if zero_price:
        print(f"  🗑️  {len(zero_price)} price records with zero/null selling_price")
        total_junk += len(zero_price)
    if processed:
        print(f"  🗑️  {len(processed)} processed missing_searches")
        total_junk += len(processed)
    if junk_searches:
        print(f"  🗑️  {len(junk_searches)} junk missing_searches")
        total_junk += len(junk_searches)
    if unlinked_labs:
        print(f"  🗑️  {len(unlinked_labs)} lab tests with 0 links")
        total_junk += len(unlinked_labs)
    if lab_zero:
        print(f"  🗑️  {len(lab_zero)} lab price records with zero/null price")
        total_junk += len(lab_zero)
    if dupes:
        print(f"  🗑️  {sum(dupes.values()) - len(dupes)} duplicate product rows (keeping 1 each)")
        total_junk += sum(dupes.values()) - len(dupes)
    if dupe_urls:
        print(f"  🗑️  {sum(dupe_urls.values()) - len(dupe_urls)} duplicate link rows (keeping 1 each)")
        total_junk += sum(dupe_urls.values()) - len(dupe_urls)

    if total_junk == 0:
        print("  ✅ No junk found! Database is clean.")
    else:
        print(f"\n  Total junk rows: ~{total_junk}")
        print("  Run the cleanup script to delete them.")

if __name__ == "__main__":
    main()
