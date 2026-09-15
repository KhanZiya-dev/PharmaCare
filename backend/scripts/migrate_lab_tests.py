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

def migrate_lab_tests():
    # 1. Fetch lab tests from products table
    logger.info("Fetching lab tests from products table...")
    res = supabase.table("products").select("*").eq("category", "lab_test").execute()
    lab_tests = res.data
    
    if not lab_tests:
        logger.info("No lab tests found in products table. Migration might be complete.")
        return

    logger.info(f"Found {len(lab_tests)} lab tests to migrate.")
    
    # 2. Insert into lab_tests table
    new_tests = []
    for test in lab_tests:
        new_tests.append({
            "id": test["id"],  # Keep the same UUID so links work
            "name": test["name"],
            "slug": test["slug"]
        })
    
    # Use upsert to handle if they already exist
    supabase.table("lab_tests").upsert(new_tests).execute()
    logger.info("Inserted/Upserted lab tests into new table.")
    
    # 3. Migrate platform links
    logger.info("Migrating platform links...")
    test_ids = [t["id"] for t in lab_tests]
    
    # Fetch links
    links_res = supabase.table("platform_product_links").select("*").in_("product_id", test_ids).execute()
    links = links_res.data
    
    if links:
        new_links = []
        for link in links:
            new_links.append({
                "id": link["id"],
                "lab_test_id": link["product_id"],
                "platform_id": link["platform_id"],
                "scrape_url": link["scrape_url"],
                "affiliate_url": link["affiliate_url"],
                "last_scraped": link["last_scraped"]
            })
        
        supabase.table("platform_lab_test_links").upsert(new_links).execute()
        logger.info(f"Migrated {len(links)} links to platform_lab_test_links.")
    
    # 4. Delete old records from products
    # Due to ON DELETE CASCADE on platform_product_links, deleting products will delete the old links
    logger.info("Deleting old records from products table...")
    for tid in test_ids:
        supabase.table("products").delete().eq("id", tid).execute()
        
    logger.info("Migration complete!")

if __name__ == "__main__":
    migrate_lab_tests()
