import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv('d:/BSc.CS/Sem5/Pharmacare/backend/.env')
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

# Check distinct categories
res = supabase.table('products').select('category').execute()
cats = set(r['category'] for r in res.data)
print("Current categories:", cats)
print(f"Total products: {len(res.data)}")

# Sample some product names to see format
res2 = supabase.table('products').select('name, category, composition').limit(15).execute()
for r in res2.data:
    print(f"  [{r['category']}] {r['name']}  |  {r.get('composition','')}")
