import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await stealth_async(page)
        
        try:
            print("Navigating to Metropolis...")
            await page.goto("https://www.metropolisindia.com/lab-tests", timeout=60000, wait_until="domcontentloaded")
            await page.wait_for_timeout(5000)
            await page.screenshot(path="metropolis_debug.png", full_page=True)
            print("Saved metropolis_debug.png")
        except Exception as e:
            print(f"Metropolis error: {e}")
            
        try:
            print("Navigating to Thyrocare...")
            await page.goto("https://www.thyrocare.com/wellness/tests", timeout=60000, wait_until="domcontentloaded")
            await page.wait_for_timeout(5000)
            await page.screenshot(path="thyrocare_debug.png", full_page=True)
            print("Saved thyrocare_debug.png")
        except Exception as e:
            print(f"Thyrocare error: {e}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
