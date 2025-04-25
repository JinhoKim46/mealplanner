import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import re
import time
from datetime import datetime

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from crawler.shared.db import insert_price, insert_product, insert_store, delete_expired_prices
from crawler.shared.utils import get_product_id
from logger import get_logger
logger = get_logger("crawler.kaufland")

HEADERS = [
    "Obst, Gemüse, Pflanzen",
    "Fleisch, Geflügel, Wurst",
    "Fisch",
    "Molkereiprodukte, Fette",
    "Tiefkühlkost",
    "Feinkost, Konserven",
    "Grundnahrungsmittel",
    "Kaffee, Tee, Süßwaren, Knabberartikel",
    "Getränke, Spirituosen",
]


def click_category_more_buttons(driver: webdriver.Chrome):
    """Click 'Mehr anzeigen' buttons in each product section"""
    sections = driver.find_elements(By.CLASS_NAME, "k-product-section")

    logger.info(f"Found {len(sections)} product sections")
    for i, section in enumerate(sections):
        try:
            # get headline (title of the section)
            header_el = section.find_element(By.CLASS_NAME, "k-product-section__headline")
            header_text = header_el.text.strip().replace("\n", "")
            logger.info(f"Section {i + 1}: '{header_text}'", level=1)

          # match only if in HEADERS
            if header_text in HEADERS:
                try:
                    button = section.find_element(By.CLASS_NAME, "k-product-grid__show-more-wrapper")
                    driver.execute_script("arguments[0].scrollIntoView(true);", button)
                    driver.execute_script("arguments[0].click();", button)
                    logger.info(f"Clicked 'Mehr anzeigen' in: {header_text}", level=2)
                    time.sleep(1.0)
                except Exception:
                    logger.warning(f"No button in: {header_text}", level=2)
            else:
                logger.warning(f"Skipped: {header_text}", level=1)
        except Exception:
            logger.warning(f"Section {i + 1}: Header missing or broken")


def extract_price_block(block: BeautifulSoup):
    """Extract price, original_price, discount from one block"""
    return {
        "price": (
            block.select_one(".k-price-tag__price").get_text(strip=True)
            if block.select_one(".k-price-tag__price")
            else None
        ),
        "original_price": (
            block.select_one(".k-price-tag__old-price").get_text(strip=True)
            if block.select_one(".k-price-tag__old-price")
            else None
        ),
        "discount": (
            block.select_one(".k-price-tag__discount").get_text(strip=True)
            if block.select_one(".k-price-tag__discount")
            else None
        ),
    }


def extract_valid_dates(text):
    match = re.search(r"Gültig vom (\d{2}\.\d{2})\. bis (\d{2}\.\d{2})\.", text)
    if match:
        this_year = datetime.now().year
        start = datetime.strptime(f"{match[1]}.{this_year}", "%d.%m.%Y").date()
        end = datetime.strptime(f"{match[2]}.{this_year}", "%d.%m.%Y").date()
        return start.isoformat(), end.isoformat()
    return None, None


def crawl_kaufland():
    options = Options()
    options.binary_location = "/usr/bin/chromium"
    options.add_argument("--headless=new")  # ✅ New-style headless mode for Chromium ≥ 109
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)

    driver.get("https://filiale.kaufland.de/angebote/aktuelle-woche.html")
    click_category_more_buttons(driver)

    # ✅ 상품 카드 렌더링 대기
    WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "k-product-tile__main")))

    soup = BeautifulSoup(driver.page_source, "lxml")

    products = []
    prices = []

    for section in soup.select(".k-product-section"):
        header = section.select_one(".k-product-section__headline")
        discount_period = section.select_one(".k-product-section__subheadline")

        category = header.get_text(strip=True) if header else "Unknown"

        discount_period = discount_period.get_text(strip=True) if discount_period else ""
        valid_from, valid_until = extract_valid_dates(discount_period)

        if category not in HEADERS:
            continue

        for tile in section.select(".k-product-tile"):
            title = tile.select_one(".k-product-tile__title")
            subtitle = tile.select_one(".k-product-tile__subtitle")
            unit_price = tile.select_one(".k-product-tile__unit-price")
            base_price = tile.select_one(".k-product-tile__base-price")
            image = tile.select_one("img.k-product-tile__main-image")

            product = {
                "title": title.get_text(strip=True) if title else "N/A",
                "subtitle": subtitle.get_text(strip=True) if subtitle else "N/A",
                "unit_price": unit_price.get_text(strip=True) if unit_price else "N/A",
                "base_price": base_price.get_text(strip=True) if base_price else "N/A",
                "image_url": image["src"] if image and image.has_attr("src") else "N/A",
                "category": category,
            }
            product["product_id"] = get_product_id(product, ["title", "subtitle", "unit_price"])
            products.append(product)

            price_blocks = tile.select(".k-price-tag")
            for block in price_blocks:
                tag_classes = block.get("class", [])
                price_type = "k-card" if "k-price-tag--k-card" in tag_classes else "normal"

                price = block.select_one(".k-price-tag__price")
                original_price = block.select_one(".k-price-tag__old-price")
                discount = block.select_one(".k-price-tag__discount")

                prices.append(
                    {
                        "product_id": product["product_id"],
                        "store": "kaufland",
                        "type": price_type,
                        "price": price.get_text(strip=True).replace("*", "") if price else "N/A",
                        "original_price": original_price.get_text(strip=True) if original_price else "N/A",
                        "discount": discount.get_text(strip=True) if discount else "N/A",
                        "category": category,
                        "valid_from": valid_from,
                        "valid_until": valid_until,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

    driver.quit()
    return products, prices

def run_kaufland():
    logger.info("Starting Kaufland crawler...")
    products, prices = crawl_kaufland()

    logger.info("Crawling completed successfully.")
    logger.info(f"Found {len(products)} products and {len(prices)} prices.")

    # Save items to DB
    logger.info("Inserting items into the database...")
    store_id = insert_store("Kaufland", website="https://kaufland.de")

    logger.info("Inserting products and prices into the database...")
    for product in products:
        insert_product(product)

    for price_record in prices:
        price_record["store_id"] = store_id
        insert_price(price_record)

    # Delete expired prices
    delete_expired_prices()
    logger.info("Expired prices deleted successfully.")
    logger.info("Kaufland crawler finished.")
    
    
if __name__ == "__main__":
    run_kaufland()