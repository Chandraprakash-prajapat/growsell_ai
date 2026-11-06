"""SQLite database: products aur orders (sample data ke saath).

Ye SAMPLE (nakli) data hai, sirf demo ke liye. Asli business ka data nahi.
Run:  uv run python db.py
"""
import os
import random
import sqlite3
import sys
from datetime import date, timedelta

from src.exception import CustomException
from src.logger import get_logger

logger = get_logger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "growsell.db")

# (naam, bikri price, banane ka kharcha, packaging, custom hai?, RTO rate, customer return rate, damage rate)
SAMPLE_PRODUCTS = [
    ("6x8 Wooden Frame", 399, 150, 20, 0, 0.05, 0.04, 0.25),
    ("8x10 Wooden Frame", 549, 210, 25, 0, 0.06, 0.06, 0.30),
    ("A4 Frame with Glass", 699, 290, 35, 0, 0.05, 0.10, 0.60),
    ("Collage Frame (5 photos)", 899, 380, 45, 0, 0.05, 0.08, 0.40),
    ("Custom Name Frame", 799, 320, 30, 1, 0.10, 0.07, 0.35),
]


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Tables banata hai (pehle se hon to kuch nahi karta)."""
    try:
        conn = connect()
        conn.execute("""CREATE TABLE IF NOT EXISTS products (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT,
                            selling_price REAL,
                            manufacturing_cost REAL,
                            packaging_cost REAL,
                            is_custom INTEGER)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS orders (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            product_id INTEGER,
                            order_date TEXT,
                            status TEXT,
                            shipping_cost REAL,
                            return_charge REAL,
                            resalable INTEGER)""")
        conn.commit()
        conn.close()
        logger.info("Database tables ready")
    except Exception as e:
        raise CustomException(e, sys)


def seed_sample_data(num_orders=200):
    """Khali database me sample products aur orders daalta hai.

    status: delivered / rto / customer_return
    rto             : order delivery se pehle cancel (return charge nahi, par bana hua maal)
    customer_return : customer ne delivery ke baad return kiya (lagbhag Rs 200 charge)
    """
    try:
        conn = connect()
        if conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] > 0:
            conn.close()
            logger.info("Sample data pehle se hai")
            return

        for name, price, mfg, pack, is_custom, _, _, _ in SAMPLE_PRODUCTS:
            conn.execute("INSERT INTO products (name, selling_price, manufacturing_cost, packaging_cost, is_custom) "
                         "VALUES (?, ?, ?, ?, ?)", (name, price, mfg, pack, is_custom))

        product_ids = [r["id"] for r in conn.execute("SELECT id FROM products ORDER BY id")]
        rng = random.Random(42)                      # har baar wahi sample data
        start = date(2026, 9, 1)
        for _ in range(num_orders):
            i = rng.randrange(len(SAMPLE_PRODUCTS))
            is_custom, rto_rate, return_rate, damage_rate = SAMPLE_PRODUCTS[i][4:8]
            order_date = (start + timedelta(days=rng.randrange(60))).isoformat()
            chance = rng.random()
            if chance < rto_rate:                                    # RTO
                status, shipping, return_charge = "rto", 0, 0
                resalable = 0 if is_custom else 1                    # custom frame dobara nahi bik sakta
            elif chance < rto_rate + return_rate:                    # customer return
                status, shipping, return_charge = "customer_return", 0, rng.randint(180, 220)
                damaged = rng.random() < damage_rate
                resalable = 0 if (is_custom or damaged) else 1
            else:                                                    # delivered
                status, shipping, return_charge, resalable = "delivered", rng.randint(40, 60), 0, None
            conn.execute("INSERT INTO orders (product_id, order_date, status, shipping_cost, return_charge, resalable) "
                         "VALUES (?, ?, ?, ?, ?, ?)",
                         (product_ids[i], order_date, status, shipping, return_charge, resalable))
        conn.commit()
        conn.close()
        logger.info(f"Sample data added: {len(SAMPLE_PRODUCTS)} products, {num_orders} orders")
    except Exception as e:
        raise CustomException(e, sys)


if __name__ == "__main__":
    init_db()
    seed_sample_data()
    conn = connect()
    print("products:", conn.execute("SELECT COUNT(*) FROM products").fetchone()[0])
    print("orders  :", conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0])
    print()
    for r in conn.execute("""SELECT p.name,
                                    COUNT(*) AS orders,
                                    SUM(o.status = 'rto') AS rto,
                                    SUM(o.status = 'customer_return') AS cust_return
                             FROM orders o JOIN products p ON p.id = o.product_id
                             GROUP BY p.id ORDER BY p.id"""):
        print(f"{r['name']:<26} orders={r['orders']:<3} rto={r['rto']:<2} customer_return={r['cust_return']}")
    conn.close()