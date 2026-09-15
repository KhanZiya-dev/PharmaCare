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

COMMON_LAB_TESTS = [
    {"name": "Complete Blood Count (CBC)", "category": "lab_test", "image_url": "https://cdn01.pharmeasy.in/dam/diagnostics/test/169/d0a0b81c4e9531bfac2ff8eb2d1e07cb.jpg"},
    {"name": "Lipid Profile", "category": "lab_test", "image_url": "https://cdn01.pharmeasy.in/dam/diagnostics/test/155/3dfaeb9d59ed3f48a7fa950666a7b1b5.jpg"},
    {"name": "Thyroid Profile (T3, T4, TSH)", "category": "lab_test", "image_url": "https://cdn01.pharmeasy.in/dam/diagnostics/test/59/2f8b5062c3e13d1ea1d07c08a90ec4c6.jpg"},
    {"name": "HbA1c (Glycosylated Hemoglobin)", "category": "lab_test", "image_url": "https://cdn01.pharmeasy.in/dam/diagnostics/test/222/684c3ea4e7c73ffcb6a4dc0e05ba476a.jpg"},
    {"name": "Vitamin D (25-OH)", "category": "lab_test", "image_url": "https://cdn01.pharmeasy.in/dam/diagnostics/test/113/376378e9f2913bf2b6cd5bcbc14234ea.jpg"},
    {"name": "Vitamin B12", "category": "lab_test"},
    {"name": "Liver Function Test (LFT)", "category": "lab_test"},
    {"name": "Kidney Function Test (KFT)", "category": "lab_test"},
    {"name": "Urine Routine & Microscopy", "category": "lab_test"},
    {"name": "Fasting Blood Sugar (FBS)", "category": "lab_test"}
]

PLATFORMS = [
    {"name": "Thyrocare", "domain": "thyrocare.com", "logo_url": "https://www.thyrocare.com/wellness/assets/images/logo.png"},
    {"name": "Metropolis", "domain": "metropolisindia.com", "logo_url": "https://www.metropolisindia.com/assets/images/logo.svg"}
]

def seed():
    # 1. Seed Platforms
    logger.info("Seeding platforms...")
    for plat in PLATFORMS:
        existing = supabase.table("platforms").select("id").eq("name", plat["name"]).execute()
        if not existing.data:
            supabase.table("platforms").insert(plat).execute()
    
    # 2. Seed Lab Tests into products
    logger.info("Fetching existing lab tests in products...")
    existing_tests = supabase.table("products").select("name").eq("category", "lab_test").execute()
    existing_names = {p["name"].lower() for p in existing_tests.data}
    
    new_tests = []
    for test in COMMON_LAB_TESTS:
        slug = test["name"].lower().replace(" ", "-").replace("(", "").replace(")", "").replace(",", "")
        if test["name"].lower() not in existing_names:
            new_tests.append({
                "name": test["name"],
                "slug": slug,
                "category": test["category"],
                "image_url": test.get("image_url")
            })
            
    if new_tests:
        logger.info(f"Adding {len(new_tests)} new lab tests to products table...")
        supabase.table("products").insert(new_tests).execute()
        logger.info("Successfully added lab tests.")
    else:
        logger.info("All common lab tests are already seeded.")

    # 3. Dummy Mappings for CBC
    cbc_res = supabase.table("products").select("id").eq("slug", "complete-blood-count-cbc").execute()
    if cbc_res.data:
        cbc_id = cbc_res.data[0]["id"]
        thyrocare_res = supabase.table("platforms").select("id").eq("name", "Thyrocare").execute()
        if thyrocare_res.data:
            thyro_id = thyrocare_res.data[0]["id"]
            link_res = supabase.table("platform_product_links").select("id").eq("product_id", cbc_id).eq("platform_id", thyro_id).execute()
            if not link_res.data:
                supabase.table("platform_product_links").insert({
                    "product_id": cbc_id,
                    "platform_id": thyro_id,
                    "scrape_url": "https://www.thyrocare.com/wellness/tests/complete-blood-count",
                    "affiliate_url": "https://www.thyrocare.com/wellness/tests/complete-blood-count"
                }).execute()
                logger.info("Added mapping for CBC -> Thyrocare")

if __name__ == "__main__":
    seed()
