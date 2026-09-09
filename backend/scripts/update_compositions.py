import os
import pandas as pd
import kagglehub
from dotenv import load_dotenv
from supabase import create_client, Client
import re

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Missing Supabase credentials")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

def main():
    print("Downloading dataset...")
    path = kagglehub.dataset_download("shudhanshusingh/az-medicine-dataset-of-india")
    
    csv_files = [f for f in os.listdir(path) if f.endswith('.csv')]
    if not csv_files:
        print("CSV not found.")
        return
        
    csv_path = os.path.join(path, csv_files[0])
    df = pd.read_csv(csv_path)
    
    # Pre-process dataframe to create a mapping of slug to composition
    print("Building composition map...")
    comp_map = {}
    for _, row in df.iterrows():
        name = str(row['name']).strip()
        slug = slugify(name)
        comp1 = str(row['short_composition1']).strip() if pd.notna(row['short_composition1']) else ""
        comp2 = str(row['short_composition2']).strip() if pd.notna(row['short_composition2']) else ""
        
        full_comp = comp1
        if comp2 and comp2.lower() != 'nan':
            full_comp = f"{comp1} + {comp2}" if comp1 else comp2
            
        if full_comp and full_comp.lower() != 'nan':
            comp_map[slug] = full_comp

    print(f"Mapped {len(comp_map)} unique compositions from CSV.")
    
    # Fetch all products from Supabase
    print("Fetching products from DB...")
    res = supabase.table("products").select("id, slug, composition").execute()
    products = res.data
    
    updates = 0
    for p in products:
        slug = p["slug"]
        curr_comp = p.get("composition")
        
        # Only update if composition is empty and we have a mapping
        if not curr_comp and slug in comp_map:
            new_comp = comp_map[slug]
            try:
                supabase.table("products").update({"composition": new_comp}).eq("id", p["id"]).execute()
                updates += 1
                if updates % 50 == 0:
                    print(f"Updated {updates} products...")
            except Exception as e:
                print(f"Error updating {slug}: {e}")

    print(f"Finished updating {updates} products!")

if __name__ == "__main__":
    main()
