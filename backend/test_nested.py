from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

response = supabase.table("products").select("id, name, slug, platform_product_links(id, price_history(id))").limit(50).execute()

for p in response.data[:5]:
    links = p.get("platform_product_links", [])
    has_prices = any(len(link.get("price_history", [])) > 0 for link in links)
    print(f"{p['name']}: links={len(links)}, has_prices={has_prices}")
