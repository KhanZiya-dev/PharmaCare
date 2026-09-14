import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv("d:/BSc.CS/Sem5/Pharmacare/backend/.env")
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

def main():
    products_res = supabase.table("products").select("id, name").execute()
    platforms_res = supabase.table("platforms").select("id, name").execute()
    links_res = supabase.table("platform_product_links").select("product_id, platform_id").execute()
    
    products = {p["id"]: p["name"] for p in products_res.data}
    platforms = {p["id"]: p["name"] for p in platforms_res.data}
    
    from collections import defaultdict
    product_links = defaultdict(set)
    for link in links_res.data:
        product_links[link["product_id"]].add(link["platform_id"])
        
    perfect_count = 0
    missing_1_count = 0
    missing_2_count = 0
    zero_links = 0
    
    report_lines = []
    report_lines.append("# Missing Links Report")
    report_lines.append("")
    report_lines.append("This report outlines which medicines are missing links for specific platforms.")
    report_lines.append("")
    
    missing_data = defaultdict(list)
    
    for pid, name in products.items():
        links = product_links.get(pid, set())
        if len(links) == 3:
            perfect_count += 1
        elif len(links) == 2:
            missing_1_count += 1
            missing = [platforms[pid] for pid in platforms if pid not in links]
            for m in missing:
                missing_data[m].append(name)
        elif len(links) == 1:
            missing_2_count += 1
            missing = [platforms[pid] for pid in platforms if pid not in links]
            for m in missing:
                missing_data[m].append(name)
        else:
            zero_links += 1
            for plat in platforms.values():
                missing_data[plat].append(name)
                
    report_lines.append(f"**Total Products:** {len(products)}")
    report_lines.append(f"**Products with all 3 links:** {perfect_count}")
    report_lines.append(f"**Products missing 1 link:** {missing_1_count}")
    report_lines.append(f"**Products missing 2 links:** {missing_2_count}")
    report_lines.append(f"**Products with 0 links:** {zero_links}")
    report_lines.append("")
    
    for platform_name in sorted(missing_data.keys()):
        report_lines.append(f"## Missing on {platform_name}")
        report_lines.append(f"Total: {len(missing_data[platform_name])}")
        report_lines.append("")
        for name in sorted(missing_data[platform_name]):
            report_lines.append(f"- {name}")
        report_lines.append("")
        
    with open("missing_links_report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
        
    print(f"Report generated! Perfect: {perfect_count}/{len(products)}")
    
if __name__ == "__main__":
    main()
