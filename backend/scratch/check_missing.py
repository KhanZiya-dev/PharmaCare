import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv('d:/BSc.CS/Sem5/Pharmacare/backend/.env')
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

res = supabase.table('missing_searches').select('*').order('created_at', desc=True).limit(50).execute()
data = res.data

if not data:
    print("Table is empty!")
else:
    print(f"Total entries found (showing up to 50): {len(data)}")
    for row in data:
        print(f"- '{row['search_query']}' (Status: {row.get('status')}, Type: {row.get('search_type')})")
