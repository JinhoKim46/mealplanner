CREATE TABLE IF NOT EXISTS stores (
    store_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    country TEXT,
    region TEXT,
    website TEXT
);

CREATE TABLE IF NOT EXISTS products (
    product_id TEXT PRIMARY KEY,
    title TEXT,
    subtitle TEXT,
    unit_price TEXT,
    base_price TEXT,
    image_url TEXT,
    category TEXT
);

CREATE TABLE IF NOT EXISTS prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT NOT NULL,
    store_id INTEGER NOT NULL,
    price_type TEXT,
    price TEXT,
    original_price TEXT,
    discount TEXT,
    timestamp TEXT,
    category TEXT,
    valid_from TEXT,
    valid_until TEXT,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (store_id) REFERENCES stores(store_id)
);

CREATE TABLE IF NOT EXISTS crawl_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id INTEGER,
    status TEXT,
    runtime TEXT,
    products_found INTEGER,
    crawled_at TEXT,
    FOREIGN KEY (store_id) REFERENCES stores(store_id)
);
