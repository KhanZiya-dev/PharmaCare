import os
import sys
import uuid
import re
from dotenv import load_dotenv
from supabase import create_client

# Ensure we run from backend root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv('d:/BSc.CS/Sem5/Pharmacare/backend/.env')

supabase = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_ROLE_KEY'])

PACKAGES = [
    {
        "name": "Comprehensive Full Body Checkup",
        "description": "A complete body checkup including liver, kidney, thyroid, heart, and blood profiles.",
        "sample_type": "Blood & Urine",
        "fasting_required": True
    },
    {
        "name": "Basic Kidney Function Test (KFT)",
        "description": "A package of tests to evaluate how well your kidneys are working (Urea, Creatinine, Uric Acid, etc).",
        "sample_type": "Blood",
        "fasting_required": False
    },
    {
        "name": "Basic Liver Function Test (LFT)",
        "description": "Measures proteins, liver enzymes, and bilirubin in your blood.",
        "sample_type": "Blood",
        "fasting_required": False
    },
    {
        "name": "Comprehensive Diabetes Profile",
        "description": "Includes Fasting Blood Sugar, HbA1c, and basic lipid parameters.",
        "sample_type": "Blood & Urine",
        "fasting_required": True
    },
    {
        "name": "Women's Health Checkup",
        "description": "Comprehensive screening for women, including thyroid, iron, bone health, and vitamins.",
        "sample_type": "Blood & Urine",
        "fasting_required": True
    }
]

def generate_slug(name):
    # Remove non-alphanumeric, replace spaces with hyphens
    s = re.sub(r'[^a-zA-Z0-9\s]', '', name).lower()
    return re.sub(r'\s+', '-', s)

def main():
    print("Adding lab packages to database...")
    
    # Check existing tests to avoid duplicates
    existing = supabase.table('lab_tests').select('name').execute()
    existing_names = [e['name'].lower() for e in existing.data] if existing.data else []
    
    added_count = 0
    for pkg in PACKAGES:
        if pkg['name'].lower() in existing_names:
            print(f"  [SKIP] '{pkg['name']}' already exists.")
            continue
            
        slug = generate_slug(pkg['name'])
        
        try:
            res = supabase.table('lab_tests').insert({
                "id": str(uuid.uuid4()),
                "name": pkg['name'],
                "slug": slug,
                "description": pkg['description'],
                "sample_type": pkg['sample_type'],
                "fasting_required": pkg['fasting_required']
            }).execute()
            print(f"  [OK] Added: {pkg['name']}")
            added_count += 1
        except Exception as e:
            print(f"  [ERROR] Failed to add {pkg['name']}: {e}")
            
    print(f"\nTotal packages added: {added_count}")

if __name__ == '__main__':
    main()
