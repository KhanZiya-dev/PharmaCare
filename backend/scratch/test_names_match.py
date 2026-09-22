import sys
import os

# Add scripts directory to path to import platform_search
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from platform_search import names_match, normalize_medicine_name, _extract_name_from_slug

test_cases = [
    ("Atorva 40 Tablet", "/online-medicine-order/atorva-40mg-strip-of-10-tablets-35862"),
    ("Complete Blood Count (CBC)", "/health-care/cbc-test-1234"),
    ("Acivir 500 Infusion", "/online-medicine-order/acivir-500mg-infusion-123"),
    ("Acitrom 2 Tablet", "/online-medicine-order/acitrom-2mg-tablet-123"),
]

for searched_name, href in test_cases:
    slug_name = _extract_name_from_slug(href)
    print(f"Searched: {searched_name}")
    print(f"Slug text: {slug_name}")
    
    searched_norm = normalize_medicine_name(searched_name)
    found_norm = normalize_medicine_name(slug_name)
    print(f"Searched norm: '{searched_norm}'")
    print(f"Found norm: '{found_norm}'")
    
    match = names_match(searched_name, slug_name)
    print(f"Match: {match}")
    print("-" * 40)
