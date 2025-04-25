from crawler.crawler_runner import run_crawler
from logger import get_logger

logger = get_logger("main")

def main():
    """
    Main function to run the crawler.
    """
    logger.info("Starting the crawler...")
    run_crawler()
    logger.info("Crawler finished successfully.")

if __name__ == "__main__":
    main()