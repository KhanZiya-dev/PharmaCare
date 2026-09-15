import os
import sys
import logging
from dotenv import load_dotenv
from supabase import create_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load env
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(env_path)

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not supabase_url or not supabase_key:
    logger.error("Missing Supabase credentials.")
    sys.exit(1)

supabase = create_client(supabase_url, supabase_key)

platforms_to_add = [
    {"name": "Agilus Diagnostics", "base_url": "https://agilusdiagnostics.com"},
    {"name": "Metropolis", "base_url": "https://www.metropolisindia.com"},
    {"name": "General Diagnostics", "base_url": "https://generaldiagnostics.in"},
    {"name": "Thyrocare", "base_url": "https://www.thyrocare.com"},
    {"name": "Lal PathLabs", "base_url": "https://www.lalpathlabs.com"}
]

def add_platforms():
    logger.info("Fetching existing platforms...")
    existing = supabase.table("platforms").select("id, name").execute()
    existing_names = [p["name"] for p in existing.data]
    
    max_id = max([p["id"] for p in existing.data]) if existing.data else 0
    
    new_platforms = []
    for p in platforms_to_add:
        if p["name"] not in existing_names:
            max_id += 1
            p["id"] = max_id
            new_platforms.append(p)
    
    if new_platforms:
        logger.info(f"Adding {len(new_platforms)} new platforms...")
        res = supabase.table("platforms").insert(new_platforms).execute()
        logger.info(f"Added successfully: {res.data}")
    else:
        logger.info("All diagnostic platforms already exist in the database.")

if __name__ == "__main__":
    add_platforms()
