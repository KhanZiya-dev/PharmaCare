import os
import csv
from dotenv import load_dotenv
from supabase import create_client
from collections import defaultdict

# Load environment variables
load_dotenv("d:/BSc.CS/Sem5/Pharmacare/backend/.env")
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

def main():
    # Fetch all products (medicines)
    print("Fetching products...")
    products_res = supabase.table("products").select("id, name, category").execute()
    
    # Filter out lab tests
    medicines = [p for p in products_res.data if p.get("category") != "lab_test"]
    print(f"Total medicines found: {len(medicines)}")

    # Fetch all links
    print("Fetching links...")
    links_res = supabase.table("platform_product_links").select(
        "product_id, platform_id, scrape_url"
    ).execute()

    # Map platform IDs
    platforms_res = supabase.table("platforms").select("id, name").execute()
    platform_map = {p["id"]: p["name"] for p in platforms_res.data}

    # Group links by product
    # Structure: product_id -> { 'Tata 1mg': 'url', 'PharmEasy': 'url', 'Apollo Pharmacy': 'url' }
    product_links = defaultdict(dict)
    for link in links_res.data:
        platform_name = platform_map.get(link["platform_id"], "Unknown")
        product_links[link["product_id"]][platform_name] = link["scrape_url"]

    # Sort medicines alphabetically
    medicines = sorted(medicines, key=lambda x: x["name"].lower())

    # Create output directory
    out_dir = "d:/BSc.CS/Sem5/Pharmacare/testing_batches"
    os.makedirs(out_dir, exist_ok=True)
    
    # Write batches of 30
    batch_size = 30
    total_batches = (len(medicines) + batch_size - 1) // batch_size
    
    headers = [
        "S.No", "Medicine Name", 
        "Tata 1mg Link", "1mg Link Correct? (Y/N)",
        "PharmEasy Link", "PharmEasy Link Correct? (Y/N)",
        "Apollo Link", "Apollo Link Correct? (Y/N)",
        "Notes/Comments"
    ]

    for i in range(total_batches):
        batch = medicines[i*batch_size : (i+1)*batch_size]
        filename = os.path.join(out_dir, f"Batch_{i+1}.csv")
        
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            
            for j, med in enumerate(batch):
                sno = (i * batch_size) + j + 1
                links = product_links.get(med["id"], {})
                
                writer.writerow([
                    sno,
                    med["name"],
                    links.get("Tata 1mg", "N/A"), "",
                    links.get("PharmEasy", "N/A"), "",
                    links.get("Apollo Pharmacy", "N/A"), "",
                    ""
                ])
                
    print(f"\nSuccessfully generated {total_batches} batch CSV files in: {out_dir}")

if __name__ == "__main__":
    main()
