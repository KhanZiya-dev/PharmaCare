import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv("d:/BSc.CS/Sem5/Pharmacare/backend/.env")
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

def main():
    try:
        # Fetch latest missing searches
        res = supabase.table("missing_searches").select("*").order("created_at", desc=True).limit(10).execute()
        
        if not res.data:
            print("No missing searches found in the table.")
        else:
            print(f"Found {len(res.data)} recent missing searches:")
            for item in res.data:
                print(f"- Query: '{item['search_query']}', Type: {item.get('search_type', 'N/A')}, At: {item.get('created_at')}")
    except Exception as e:
        print(f"Error querying table: {e}")

if __name__ == "__main__":
    main()
