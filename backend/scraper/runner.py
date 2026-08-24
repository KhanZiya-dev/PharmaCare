import os
import sys
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client, Client

# Ensure we can import from the parent directory if run standalone
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.onemg_scraper import OneMgScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load from .env in backend directory
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def get_supabase() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Supabase credentials not configured in .env")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def run_scrapers():
    supabase = get_supabase()
    
    # 1. Fetch active URLs
    try:
        response = supabase.table("platform_product_links").select(
            "id, scrape_url, platform_id, platforms(name)"
        ).execute()
        links = response.data
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {e}")
        return
    logger.info(f"Found {len(links)} links to scrape.")
    
    scrapers = {}
    
    for link in links:
        mapping_id = link["id"]
        url = link["scrape_url"]
        platform_id = link["platform_id"]
        platform_name = link["platforms"]["name"]
        
        logger.info(f"Scraping {platform_name} for mapping {mapping_id}")
        
        scraper = scrapers.get(platform_id)
        if not scraper:
            if "1mg" in platform_name.lower():
                scraper = OneMgScraper(platform_id=platform_id)
                scrapers[platform_id] = scraper
            else:
                logger.warning(f"No scraper implemented for platform: {platform_name}")
                continue
                
        # 2. Run the scraper
        result = scraper.scrape(url)
        
        if result:
            logger.info(f"Result for mapping {mapping_id}: {result}")
            # 3. Insert into price_history
            history_data = {
                "mapping_id": mapping_id,
                "mrp": result.get("mrp"),
                "selling_price": result.get("selling_price") or result.get("mrp") or 0.0,
                "in_stock": result.get("in_stock", True),
                "scraped_at": datetime.now(timezone.utc).isoformat()
            }
            
            try:
                # Calculate discount
                if history_data["mrp"] and history_data["selling_price"] and history_data["mrp"] > 0:
                    discount_pct = ((history_data["mrp"] - history_data["selling_price"]) / history_data["mrp"]) * 100
                    history_data["discount_pct"] = round(discount_pct, 2)
                    
                supabase.table("price_history").insert(history_data).execute()
                
                # 4. Update last_scraped
                supabase.table("platform_product_links").update({
                    "last_scraped": datetime.now(timezone.utc).isoformat()
                }).eq("id", mapping_id).execute()
                
            except Exception as e:
                logger.error(f"Error saving to DB for mapping {mapping_id}: {e}")
        else:
            logger.error(f"Failed to extract data for {url}")

if __name__ == "__main__":
    run_scrapers()
