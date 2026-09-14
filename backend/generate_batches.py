import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv("d:/BSc.CS/Sem5/Pharmacare/backend/.env")
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

def main():
    products_res = supabase.table("products").select("id, name").execute()
    links_res = supabase.table("platform_product_links").select("product_id, platform_id").execute()
    
    products = {p["id"]: p["name"] for p in products_res.data}
    
    from collections import defaultdict
    product_links = defaultdict(set)
    for link in links_res.data:
        product_links[link["product_id"]].add(link["platform_id"])
        
    missing_medicines = []
    
    for pid, name in products.items():
        links = product_links.get(pid, set())
        if len(links) < 3:
            missing_medicines.append(name.strip())
            
    # Sort for consistency
    missing_medicines.sort()
    
    report_lines = []
    report_lines.append("# Remaining Medicines (Batches of 15)")
    report_lines.append("")
    report_lines.append(f"Total remaining medicines: {len(missing_medicines)}")
    report_lines.append("")
    
    for i in range(0, len(missing_medicines), 15):
        batch = missing_medicines[i:i+15]
        report_lines.append(f"### Batch { (i//15) + 1 }")
        for med in batch:
            report_lines.append(f"- {med}")
        report_lines.append("")
        
    with open("remaining_medicines_batches.md", "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
        
    print(f"Generated batches for {len(missing_medicines)} medicines.")

if __name__ == "__main__":
    main()
