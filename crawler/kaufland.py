# crawler/kaufland_selenium.py

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
import time

def crawl_kaufland():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get("https://filiale.kaufland.de/angebote/aktuelle-woche.html")

    time.sleep(5)  # JS 렌더링 기다림

    soup = BeautifulSoup(driver.page_source, "lxml")

    products = []

    for item in soup.select(".product-tile-wrapper"):
        title_tag = item.select_one(".product-title__text")
        price_tag = item.select_one(".product-price__price")
        image_tag = item.select_one("img.product-image__image")

        title = title_tag.get_text(strip=True) if title_tag else "N/A"
        price = price_tag.get_text(strip=True) if price_tag else "N/A"
        image = image_tag.get("data-src", "N/A") if image_tag else "N/A"

        products.append({
            "title": title,
            "price": price,
            "image": image
        })

    driver.quit()
    return products


if __name__ == "__main__":
    items = crawl_kaufland()
    for item in items[:10]:
        print(item)
