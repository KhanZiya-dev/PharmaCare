from playwright.sync_api import sync_playwright
import json

url = "https://www.apollopharmacy.in/medicine/pan-d-capsule"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    page.goto(url, wait_until="networkidle", timeout=60000)
    
    scripts = page.locator('script[type="application/ld+json"]').all()
    for s in scripts:
        try:
            data = json.loads(s.inner_text())
            if isinstance(data, dict):
                data = [data]
            for item in data:
                print(f"JSON-LD Type: {item.get('@type')}")
                if item.get('@type') == 'Product' or item.get('@type') == 'Drug':
                    print("Found Product data:")
                    print(json.dumps(item, indent=2)[:500])
        except Exception as e:
            print(f"Error parsing JSON-LD: {e}")
            
    browser.close()
