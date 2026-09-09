from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    # Go to search page
    page.goto("https://www.1mg.com/search/all?name=Pan-D%20Capsule", wait_until="networkidle")
    time.sleep(3)
    
    # Try to extract the link to the first product
    try:
        first_product_link = page.locator("a[href*='/drugs/']").first
        url = first_product_link.get_attribute("href")
        print(f"FOUND URL: https://www.1mg.com{url}")
    except Exception as e:
        print(f"Error finding product link: {e}")
        
    browser.close()
