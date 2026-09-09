from playwright.sync_api import sync_playwright

url = "https://www.apollopharmacy.in/medicine/pan-d-capsule"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    page.goto(url, wait_until="networkidle", timeout=60000)
    
    with open("apollo_html.txt", "w", encoding="utf-8") as f:
        f.write(page.content())
    
    browser.close()
    print("Saved Apollo HTML")
