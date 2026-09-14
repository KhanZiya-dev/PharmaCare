import os
import asyncio
from supabase import create_client
from dotenv import load_dotenv
from scraper.apollo_scraper import ApolloScraper
from playwright.async_api import async_playwright
from fake_useragent import UserAgent

load_dotenv("d:/BSc.CS/Sem5/Pharmacare/backend/.env")
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

async def test_apollo():
    # Get a link that is marked as out of stock
    platform_res = supabase.table("platforms").select("id").eq("name", "Apollo Pharmacy").execute()
    apollo_id = platform_res.data[0]["id"]
    
    links_res = supabase.table("platform_product_links").select("id, scrape_url").eq("platform_id", apollo_id).execute()
    mapping_ids = {link["id"]: link["scrape_url"] for link in links_res.data}
    
    history_res = supabase.table("price_history").select("mapping_id, in_stock").in_("mapping_id", list(mapping_ids.keys())).eq("in_stock", False).limit(1).execute()
    
    if not history_res.data:
        print("No out of stock apollo links found.")
        return
        
    test_id = history_res.data[0]["mapping_id"]
    test_url = mapping_ids[test_id]
    
    print(f"Testing URL: {test_url}")
    
    ua = UserAgent(browsers=['chrome'])
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=ua.random)
        page = await context.new_page()
        
        scraper = ApolloScraper(platform_id=apollo_id)
        data = await scraper.scrape_page(page, test_url)
        
        print(f"Scraped Data: {data}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_apollo())
