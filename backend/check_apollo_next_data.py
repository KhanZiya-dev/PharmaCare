from playwright.sync_api import sync_playwright
import json
from bs4 import BeautifulSoup

url = "https://www.apollopharmacy.in/medicine/pan-d-capsule"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    page.goto(url, wait_until="networkidle", timeout=60000)
    
    html = page.content()
    soup = BeautifulSoup(html, "html.parser")
    
    script_tag = soup.find("script", id="__NEXT_DATA__")
    if script_tag:
        data = json.loads(script_tag.string)
        props = data.get("props", {}).get("pageProps", {})
        product = props.get("productData") or props.get("product") or props.get("medicineData") or props.get("data", {}).get("product")
        if product:
            print(f"Product data found! Keys: {product.keys()}")
            print(f"Price: {product.get('price')}")
            print(f"Selling Price: {product.get('sellingPrice')}")
            print(f"MRP: {product.get('mrp')}")
            print(f"Special Price: {product.get('specialPrice')}")
            print(f"Name: {product.get('name')}")
        else:
            print(f"Product object not found in props. Available keys in pageProps: {props.keys()}")
            
            # Let's explore deep
            print("Trying to find medicine details in nested objects...")
            for k, v in props.items():
                if isinstance(v, dict):
                    print(f"Key {k} is dict with keys: {v.keys()}")
                    if "price" in v:
                        print(f"Found price in {k}: {v['price']}")
    else:
        print("No __NEXT_DATA__ found")
        
    browser.close()
