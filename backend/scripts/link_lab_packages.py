import asyncio
import os
import sys
import urllib.parse
from playwright.async_api import async_playwright
from dotenv import load_dotenv
from supabase import create_client
from playwright_stealth import stealth_async

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv('d:/BSc.CS/Sem5/Pharmacare/backend/.env')
supabase = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_ROLE_KEY'])

import difflib

def names_match(search_query, found_name, threshold=0.7):
    # Same robust matching logic we use for medicines
    q = search_query.lower().strip()
    f = found_name.lower().strip()
    ratio = difflib.SequenceMatcher(None, q, f).ratio()
    # If the word count is very different, or it's a completely different test
    return ratio >= threshold

async def search_1mg_lab(page, query):
    try:
        await page.goto("https://www.1mg.com/labs", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_selector("input[placeholder*='Search tests']", timeout=10000)
        
        await page.fill("input[placeholder*='Search tests']", query)
        await asyncio.sleep(2)
        
        items = await page.locator("a[href*='/labs/test/']").all()
        for item in items:
            text = await item.inner_text()
            # Split text by newline (often title is first line)
            title = text.split('\n')[0]
            if names_match(query, title):
                href = await item.get_attribute('href')
                if href:
                    return f"https://www.1mg.com{href}"
    except Exception as e:
        print(f"1mg error: {e}")
    return None

async def search_pharmeasy_lab(page, query):
    try:
        await page.goto("https://pharmeasy.in/diagnostics", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_selector("input.diagnostics-search-input", timeout=10000)
        
        await page.click("input.diagnostics-search-input")
        await page.fill("input.diagnostics-search-input", query)
        await asyncio.sleep(2)
        
        items = await page.locator("a[href*='/diagnostics/packages/'], a[href*='/diagnostics/tests/']").all()
        for item in items:
            text = await item.inner_text()
            title = text.split('\n')[0]
            if names_match(query, title):
                href = await item.get_attribute('href')
                if href:
                    return f"https://pharmeasy.in{href}"
    except Exception as e:
        print(f"PharmEasy error: {e}")
    return None

async def search_agilus_lab(page, query):
    try:
        await page.goto("https://agilusdiagnostics.com", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_selector("input[placeholder*='Search for lab tests']", timeout=10000)
        
        await page.click("input[placeholder*='Search for lab tests']")
        await page.fill("input[placeholder*='Search for lab tests']", query)
        await asyncio.sleep(2)
        
        items = await page.locator("div.overflow-y-auto a[href*='/package/']").all()
        for item in items:
            text = await item.inner_text()
            title = text.split('\n')[0]
            if names_match(query, title, threshold=0.6): # slightly lower threshold for agilus
                href = await item.get_attribute('href')
                if href:
                    return f"https://agilusdiagnostics.com{href}"
    except Exception as e:
        print(f"Agilus error: {e}")
    return None

def save_link(test_id, plat_id, link):
    try:
        existing = supabase.table('platform_lab_test_links').select('id').eq('lab_test_id', test_id).eq('platform_id', plat_id).execute()
        if existing.data:
            supabase.table('platform_lab_test_links').update({'scrape_url': link}).eq('id', existing.data[0]['id']).execute()
        else:
            import uuid
            supabase.table('platform_lab_test_links').insert({
                'id': str(uuid.uuid4()),
                'lab_test_id': test_id,
                'platform_id': plat_id,
                'scrape_url': link
            }).execute()
    except Exception as e:
        print(f"DB Error: {e}")

async def main():
    print("Fetching lab packages from DB...")
    tests_res = supabase.table('lab_tests').select('id, name').execute()
    tests = tests_res.data
    
    platforms_res = supabase.table('platforms').select('id, name').execute()
    plat_map = {p['name']: p['id'] for p in platforms_res.data}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        await stealth_async(page)
        
        for test in tests:
            name = test['name']
            test_id = test['id']
            print(f"\nSearching for: {name}")
            
            # Tata 1mg
            if 'Tata 1mg' in plat_map:
                print("  Searching 1mg...")
                link = await search_1mg_lab(page, name)
                if link:
                    print(f"  [1mg] Found: {link}")
                    save_link(test_id, plat_map['Tata 1mg'], link)
                else:
                    print("  [1mg] Not found")
                    
            # PharmEasy
            if 'PharmEasy' in plat_map:
                print("  Searching PharmEasy...")
                link = await search_pharmeasy_lab(page, name)
                if link:
                    print(f"  [PharmEasy] Found: {link}")
                    save_link(test_id, plat_map['PharmEasy'], link)
                else:
                    print("  [PharmEasy] Not found")
                    
            # Agilus Diagnostics
            if 'Agilus Diagnostics' in plat_map:
                print("  Searching Agilus...")
                link = await search_agilus_lab(page, name)
                if link:
                    print(f"  [Agilus] Found: {link}")
                    save_link(test_id, plat_map['Agilus Diagnostics'], link)
                else:
                    print("  [Agilus] Not found")
                    
        await browser.close()
    
    print("\nLinking complete!")

if __name__ == '__main__':
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
