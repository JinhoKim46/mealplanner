# crawler/shared/db.py

import sqlite3
from datetime import datetime, date
from typing import Dict, List, Union
from logger import get_logger

logger = get_logger("crawler.shared.db")

DB_PATH = "database/main.sqlite"

def init_db():
    with open("database/schema.sql", "r", encoding="utf-8") as f:
        schema = f.read()

    conn = sqlite3.connect("database/main.sqlite")
    conn.executescript(schema)
    conn.commit()
    conn.close()
    
def get_connection():
    return sqlite3.connect(DB_PATH)


def insert_store(name:str, country:str="DE", region:str="global", website:str=""):
    """
    Insert a store into the database. If the store already exists, it will be ignored.
    The store_id is auto-incremented based on the maximum existing store_id.
    If the store already exists, it will return the existing store_id.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO stores (store_id, name, country, region, website)
        VALUES ((SELECT COALESCE(MAX(store_id), 0) + 1 FROM stores WHERE name = ?), ?, ?, ?, ?)
    """, (name, name, country, region, website))
    conn.commit()
    cur.execute("SELECT store_id FROM stores WHERE name = ?", (name,))
    store_id = cur.fetchone()[0]
    conn.close()
    return store_id


def insert_product(product_dict:Dict[str, Union[int, str]]):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO products (
            product_id, title, subtitle, unit_price,
            base_price, image_url, category
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        product_dict["product_id"], 
        product_dict["title"], 
        product_dict["subtitle"],
        product_dict["unit_price"], 
        product_dict["base_price"],
        product_dict["image_url"], 
        product_dict["category"]
    ))
    conn.commit()
    conn.close()


def insert_price(price_dict:Dict[str, Union[int, str]]):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO prices (
            product_id, store_id, price_type,
            price, original_price, discount, timestamp, category, valid_from, valid_until
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        price_dict["product_id"],
        price_dict["store_id"],
        price_dict["type"],
        price_dict["price"],
        price_dict["original_price"],
        price_dict["discount"],
        price_dict.get("timestamp") or datetime.now().isoformat(),
        price_dict["category"],
        price_dict.get("valid_from"),
        price_dict.get("valid_until")
    ))
    conn.commit()
    conn.close()


def delete_expired_prices():
    conn = get_connection()
    cur = conn.cursor()
    today = date.today().isoformat()

    # 1. Find all expired prices
    cur.execute("SELECT id, product_id, store_id, price, valid_until FROM prices WHERE valid_until < ?", (today,))
    expired_prices = cur.fetchall()
    deleted_price_count = len(expired_prices)

    if deleted_price_count == 0:
        logger.info("No expired prices to delete.")
        conn.close()
        return

    logger.info(f"Found {len(expired_prices)} expired prices to delete.")

    # 2. Log each one
    for row in expired_prices:
        price_id, product_id, store_id, price, valid_until = row
        logger.info(f"Deleting price ID={price_id} | product_id={product_id} | store={store_id} | price={price} | valid_until={valid_until}")

    # 3. Delete the expired prices
    cur.execute("DELETE FROM prices WHERE valid_until < ?", (today,))
    conn.commit()

    # 4. Check orphaned products (with no prices left)
    cur.execute("""
        DELETE FROM products
        WHERE product_id IN (
            SELECT p.product_id
            FROM products p
            LEFT JOIN prices pr ON pr.product_id = p.product_id
            WHERE pr.id IS NULL
        )
    """)
    orphan_products = cur.fetchall()
    deleted_product_count = len(orphan_products)

    if orphan_products:
        logger.info(f"Found {deleted_product_count} orphaned products to delete.")
        for product_id, title in orphan_products:
            logger.info(f"Deleting product: {product_id} | title: {title}")
        cur.executemany(
            "DELETE FROM products WHERE product_id = ?",
            [(pid,) for pid, _ in orphan_products]
        )
        conn.commit()
    else:
        logger.info("No orphaned products to delete.")

    conn.close()

    # 5. Summary
    logger.info(f"Summary: Deleted {deleted_price_count} expired prices, {deleted_product_count} orphaned products.")

