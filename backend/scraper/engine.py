import os
import logging
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime

# Import scrapers
from .onemg_scraper import OneMgScraper
from .pharmeasy_scraper import PharmEasyScraper
from .apollo_scraper import ApolloScraper

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load env variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

def get_supabase_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise ValueError("Missing Supabase credentials in .env file.")
    return create_client(url, key)

def get_scraper_for_platform(platform_name: str, platform_id: int):
    name = platform_name.lower()
    if "1mg" in name:
        return OneMgScraper(platform_id)
    elif "pharmeasy" in name:
        return PharmEasyScraper(platform_id)
    elif "apollo" in name:
        return ApolloScraper(platform_id)
    else:
        logger.warning(f"No specific scraper found for platform: {platform_name}")
        return None

def run_engine():
    logger.info("Initializing Scraper Engine...")
    try:
        supabase = get_supabase_client()
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {e}", exc_info=True)
        return

    logger.info("Fetching platform product links...")
    # Fetch links joined with platform details
    # We select link id, scrape_url, product_id, and platform name
    links_res = supabase.table("platform_product_links").select(
        "id, scrape_url, product_id, platforms(id, name)"
    ).execute()

    if not links_res.data:
        logger.warning("No active product links found to scrape.")
        return

    links = links_res.data
    logger.info(f"Found {len(links)} links to scrape.")

    for link in links:
        link_id = link.get("id")
        scrape_url = link.get("scrape_url")
        product_id = link.get("product_id")
        platform = link.get("platforms")
        
        if not scrape_url or not platform:
            logger.warning(f"Invalid link configuration for link_id {link_id}. Skipping.")
            continue
            
        platform_id = platform.get("id")
        platform_name = platform.get("name")

        logger.info(f"Processing product_id: {product_id} on platform: {platform_name}")
        
        scraper = get_scraper_for_platform(platform_name, platform_id)
        if not scraper:
            continue

        try:
            data = scraper.scrape(scrape_url)
            if data and data.get("selling_price"):
                logger.info(f"Scraped data for {platform_name}: {data}")
                
                # Push data to price_history
                history_record = {
                    "mapping_id": link_id,
                    "selling_price": data["selling_price"],
                    "mrp": data.get("mrp") or data["selling_price"],
                    "in_stock": data.get("in_stock", True)
                }
                
                # Insert into Supabase
                supabase.table("price_history").insert(history_record).execute()
                logger.info(f"Successfully recorded price for link_id: {link_id}")
            else:
                logger.warning(f"Failed to scrape meaningful data for {scrape_url}")
                
        except Exception as e:
            logger.error(f"Error during scraping or database insertion for link_id {link_id}: {e}")

if __name__ == "__main__":
    run_engine()
