import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Print all requests
        page.on("request", lambda request: print(f"REQ: {request.method} {request.url} BODY: {request.post_data[:100] if request.post_data else ''}"))

        print("Navigating to Zeno Health...")
        try:
            await page.goto("https://www.zeno.health/", timeout=60000)
            await page.wait_for_timeout(10000)
        except Exception as e:
            print(f"Error: {e}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
