import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Intercept and print API responses
        page.on("response", lambda response: asyncio.create_task(handle_response(response)))

        print("Navigating to Zeno Health...")
        try:
            await page.goto("https://www.zeno.health/", timeout=60000)
            await page.wait_for_timeout(10000) # wait 10 seconds to let Flutter load and fetch data
        except Exception as e:
            print(f"Error: {e}")
            
        await browser.close()

async def handle_response(response):
    url = response.url
    if "api" in url.lower() or "search" in url.lower() or "graphql" in url.lower() or "product" in url.lower() or ".json" in url.lower() or "backend" in url.lower():
        print(f"Found potential API: {url}")
        try:
            if "application/json" in response.headers.get("content-type", ""):
                body = await response.json()
                print(f"Response snippet from {url}: {str(body)[:200]}")
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main())
