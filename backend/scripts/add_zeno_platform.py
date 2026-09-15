from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

def add_zeno():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, key)
    
    # Check if Zeno Health exists
    res = supabase.table("platforms").select("*").eq("name", "Zeno Health").execute()
    if not res.data:
        print("Inserting Zeno Health...")
        supabase.table("platforms").insert({
            "name": "Zeno Health",
            "domain": "zeno.health",
            "logo_url": "https://d3pmeofo468e0p.cloudfront.net/zeno-app-v1/images/other/user_stats.svg",
            "is_active": True
        }).execute()
        print("Done.")
    else:
        print("Zeno Health already exists.")

if __name__ == "__main__":
    add_zeno()
