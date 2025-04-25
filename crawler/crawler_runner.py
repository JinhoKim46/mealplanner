import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from crawler.kaufland import run_kaufland
from logger import get_logger
from crawler.shared.db import init_db
logger = get_logger("crawler.run_all")

def run_crawler():
    """
    Run all crawlers.
    """
    # Initialize the database
    logger.info("Initializing the database...")
    init_db()

    # Run the Kaufland crawler
    logger.info("Running the Kaufland crawler...")
    run_kaufland()