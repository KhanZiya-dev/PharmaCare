"""
Quick test script to verify scraper accuracy on known medicines.
Tests each platform with a known product URL and validates the output.
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from scraper.onemg_scraper import OneMgScraper
from scraper.apollo_scraper import ApolloScraper
from scraper.pharmeasy_scraper import PharmEasyScraper

# Known test URLs with expected approximate prices
TEST_CASES = [
    {
        "name": "Dolo 650 - Apollo",
        "url": "https://www.apollopharmacy.in/otc/dolo-650mg-tablet-15-s",
        "scraper": ApolloScraper(platform_id=1),
        "expected_price_range": (25, 50),  # Approximate range
    },
    {
        "name": "Dolo 650 - 1mg",
        "url": "https://www.1mg.com/drugs/dolo-650-tablet-74467",
        "scraper": OneMgScraper(platform_id=2),
        "expected_price_range": (25, 50),
    },
    {
        "name": "Dolo 650 - PharmEasy",
        "url": "https://pharmeasy.in/online-medicine-order/dolo-650mg-strip-of-15-tablets-26498",
        "scraper": PharmEasyScraper(platform_id=3),
        "expected_price_range": (25, 50),
    },
]


async def test_scraper():
    print("=" * 70)
    print("SCRAPER ACCURACY TEST")
    print("=" * 70)
    
    import sys
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        
        results = []
        
        for test in TEST_CASES:
            print(f"\n{'-' * 50}")
            print(f"Testing: {test['name']}")
            print(f"URL: {test['url']}")
            print(f"{'-' * 50}")
            
            page = await context.new_page()
            await stealth_async(page)
            
            try:
                data = await test["scraper"].scrape_page(page, test["url"])
                
                if data:
                    sp = data.get("selling_price", 0)
                    mrp = data.get("mrp", 0)
                    in_stock = data.get("in_stock", "N/A")
                    is_restricted = data.get("is_restricted", False)
                    image = data.get("image_url", "N/A")
                    
                    min_p, max_p = test["expected_price_range"]
                    price_ok = min_p <= sp <= max_p if sp else False
                    mrp_ok = sp <= mrp if sp and mrp else False
                    restricted_ok = not is_restricted  # Dolo 650 should NOT be restricted
                    
                    status = "PASS" if (price_ok and mrp_ok and restricted_ok) else "WARN"
                    
                    print(f"  [{status}] Selling Price: Rs.{sp}")
                    print(f"  [{'OK' if mrp_ok else 'FAIL'}] MRP: Rs.{mrp}")
                    print(f"  [{'OK' if mrp_ok else 'FAIL'}] MRP >= Selling: {mrp_ok}")
                    print(f"  [{'OK' if price_ok else 'FAIL'}] Price in range [{min_p}-{max_p}]: {price_ok}")
                    print(f"  [Stock] In Stock: {in_stock}")
                    print(f"  [{'OK' if restricted_ok else 'FAIL'}] Not Restricted: {restricted_ok}")
                    print(f"  [Image] {image[:60]}..." if image and image != "N/A" else "  [Image] None")
                    
                    results.append({
                        "name": test["name"],
                        "success": price_ok and mrp_ok and restricted_ok,
                        "data": data,
                    })
                else:
                    print(f"  [FAIL] No data returned!")
                    results.append({"name": test["name"], "success": False, "data": None})
            except Exception as e:
                print(f"  [ERROR] {e}")
                results.append({"name": test["name"], "success": False, "data": None})
            finally:
                await page.close()
        
        await browser.close()
    
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    print(f"Passed: {passed}/{total}")
    for r in results:
        print(f"  [{'PASS' if r['success'] else 'FAIL'}] {r['name']}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(test_scraper())
