from playwright.sync_api import sync_playwright

url = "https://www.apollopharmacy.in/medicine/pan-d-capsule"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    page.goto(url, wait_until="networkidle", timeout=60000)
    
    print("Page Title:", page.title())
    
    # Let's try to extract price using different selectors
    try:
        h1 = page.locator('h1').first
        if h1.count() > 0:
            print(f"H1 text: {h1.inner_text()}")
            # Find the parent container that contains both h1 and price
            # Let's just find the closest ancestor that also contains a 'text=/₹\\s*\\d/'
            # A simple way in playwright is to find a container with a specific class, or just get all prices and find the one with the largest font-size.
            price_elements = page.locator('text=/₹\\s*\\d/').all()
            max_size = 0
            best_price = None
            for i, el in enumerate(price_elements):
                text = el.inner_text().encode('ascii', 'ignore').decode()
                try:
                    size_str = el.evaluate("el => window.getComputedStyle(el).fontSize")
                    size = float(size_str.replace('px', ''))
                    print(f"[{i}] {text} - size: {size}px")
                    if size > max_size:
                        max_size = size
                        best_price = text
                except Exception as e:
                    pass
            print(f"Best Price based on font size: {best_price}")
        
    except Exception as e:
        print(f"Error: {e}")
        
    browser.close()
