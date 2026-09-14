import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv("d:/BSc.CS/Sem5/Pharmacare/backend/.env")
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

def main():
    products_res = supabase.table("products").select("id").execute()
    links_res = supabase.table("platform_product_links").select("product_id").execute()
    
    product_ids = {p["id"] for p in products_res.data}
    linked_product_ids = {link["product_id"] for link in links_res.data}
    
    empty_products = product_ids - linked_product_ids
    
    print(f"Total products in DB: {len(product_ids)}")
    print(f"Total linked products: {len(linked_product_ids)}")
    print(f"Total empty products (0 links): {len(empty_products)}")
    
if __name__ == "__main__":
    main()
