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

# (name, selling price, manufacturing cost, packaging cost, is custom,
#  RTO rate, customer return rate, damage rate)
SAMPLE_PRODUCTS = [
    ("6x8 Wooden Frame", 399, 150, 20, 0, 0.05, 0.04, 0.25),
    ("8x10 Wooden Frame", 549, 210, 25, 0, 0.06, 0.06, 0.30),
    ("A4 Frame with Glass", 699, 290, 35, 0, 0.05, 0.10, 0.60),
    ("Collage Frame (5 photos)", 899, 380, 45, 0, 0.05, 0.08, 0.40),
    ("Custom Name Frame", 799, 320, 30, 1, 0.10, 0.07, 0.35),
]


def connect():
    """Open a connection to the SQLite file."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the tables if they do not exist yet."""
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
        conn.execute("""CREATE TABLE IF NOT EXISTS action_items (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            created_at TEXT,
                            title TEXT,
                            expected_saving REAL,
                            status TEXT DEFAULT 'open')""")
        conn.commit()
        conn.close()
        logger.debug("Database tables ready")
    except Exception as e:
        raise CustomException(e, sys)


def seed_sample_data(num_orders=200):
    """Insert sample products and orders if the database is empty.

    Order status values:
      delivered       - the customer received the order
      rto             - cancelled before delivery (no return charge, but the product is already made)
      customer_return - returned by the customer after delivery (about Rs 200 charge)
    """
    try:
        conn = connect()
        if conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] > 0:
            conn.close()
            logger.debug("Sample data already exists")
            return

        for name, price, mfg, pack, is_custom, _, _, _ in SAMPLE_PRODUCTS:
            conn.execute("INSERT INTO products (name, selling_price, manufacturing_cost, packaging_cost, is_custom) "
                         "VALUES (?, ?, ?, ?, ?)", (name, price, mfg, pack, is_custom))

        product_ids = [r["id"] for r in conn.execute("SELECT id FROM products ORDER BY id")]
        rng = random.Random(42)                      # fixed seed: same sample data every time
        start = date(2026, 9, 1)
        for _ in range(num_orders):
            i = rng.randrange(len(SAMPLE_PRODUCTS))
            is_custom, rto_rate, return_rate, damage_rate = SAMPLE_PRODUCTS[i][4:8]
            order_date = (start + timedelta(days=rng.randrange(60))).isoformat()
            chance = rng.random()
            if chance < rto_rate:                                    # RTO
                status, shipping, return_charge = "rto", 0, 0
                resalable = 0 if is_custom else 1                    # a custom frame cannot be resold
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


def setup_database():
    """Create the tables and add sample data. Safe to call many times."""
    init_db()
    seed_sample_data()


def add_action_item(title, expected_saving=0):
    """Save a to-do item suggested by the agent. Skips it if the same title already exists."""
    try:
        conn = connect()
        exists = conn.execute("SELECT 1 FROM action_items WHERE title = ?", (title,)).fetchone()
        if not exists:
            conn.execute("INSERT INTO action_items (created_at, title, expected_saving) VALUES (?, ?, ?)",
                         (date.today().isoformat(), title, expected_saving))
            conn.commit()
            logger.info(f"Action item saved: {title}")
        conn.close()
        return not exists
    except Exception as e:
        raise CustomException(e, sys)


def get_action_items():
    """Return all saved action items, newest first."""
    conn = connect()
    rows = conn.execute("SELECT * FROM action_items ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]




if __name__ == "__main__":
    setup_database()
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


    # Run:  uv run python db.py
