import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        # Navigate to a known product
        await page.goto("https://www.zeno.health/product/dologel-gel-15gm/58021")
        await page.wait_for_timeout(3000)
        await page.screenshot(path="zeno_product_test.png")
        print("Final URL:", page.url)
        
        # Test just the ID?
        await page.goto("https://www.zeno.health/product/58021")
        await page.wait_for_timeout(3000)
        await page.screenshot(path="zeno_product_test2.png")
        print("Final URL 2:", page.url)
        
        await browser.close()

asyncio.run(main())
