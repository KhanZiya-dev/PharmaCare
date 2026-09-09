from playwright.sync_api import sync_playwright
import time

url = "https://www.1mg.com/drugs/pan-d-capsule-66498"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    page = context.new_page()
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    time.sleep(5)
    
    with open("1mg_html.txt", "w", encoding="utf-8") as f:
        f.write(page.content())
    
    browser.close()
    print("Saved 1mg HTML to 1mg_html.txt")
