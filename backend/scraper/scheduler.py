import schedule
import time
import logging
from runner import run_scrapers

# Set up logging for the scheduler
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def job():
    logger.info("Starting scheduled scraper job...")
    run_scrapers()
    logger.info("Scheduled scraper job finished.")

def start_scheduler():
    logger.info("Initializing PharmaCare Scraper Scheduler...")
    
    # Schedule the job every day at 02:00 AM
    schedule.every().day.at("02:00").do(job)
    
    # Alternatively, for testing, you could run it every 5 minutes:
    # schedule.every(5).minutes.do(job)

    logger.info("Scheduler is running. Waiting for next job execution.")
    
    while True:
        schedule.run_pending()
        time.sleep(60) # Wait one minute before checking again to save CPU

if __name__ == "__main__":
    start_scheduler()
