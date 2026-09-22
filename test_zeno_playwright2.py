import asyncio
from playwright.async_api import async_playwright

async def test_url(page, url):
    print(f"\n--- Testing {url} ---")
    await page.goto(url, wait_until="networkidle")
    await page.wait_for_timeout(3000)
    title = await page.title()
    body_text = await page.evaluate('document.body.innerText')
    print("Final URL:", page.url)
    print("Title:", title)
    print("Body text excerpt (first 300 chars):", body_text.strip()[:300].replace('\n', ' '))
    if "unavailable" in body_text.lower():
        print("RESULT: Data Unavailable")
    elif "dologel" in body_text.lower():
        print("RESULT: Success, found product name")
    else:
        print("RESULT: Not found")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        urls_to_test = [
            "https://www.zeno.health/product/dologel-gel-15gm/58021",
            "https://www.zeno.health/product/58021",
            "https://www.zeno.health/productDetails/58021",
            "https://www.zeno.health/productDetails/dologel-gel-15gm/58021",
            "https://www.zeno.health/product-details/58021"
        ]
        
        for u in urls_to_test:
            await test_url(page, u)
            
        await browser.close()

asyncio.run(main())
