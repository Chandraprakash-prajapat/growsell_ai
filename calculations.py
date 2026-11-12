"""Business calculations: profit and return losses. Plain Python math, no AI.

Run:  uv run python calculations.py
"""
import sys

from db import connect
import data_store
import meesho_payments
from src.exception import CustomException
from src.logger import get_logger

logger = get_logger(__name__)


def get_orders():
    """Return all orders together with their product details.

    Uses the seller's uploaded Meesho data when there is any, otherwise the demo data.
    """
    if data_store.has_real():
        return meesho_payments.real_orders()
    conn = connect()
    rows = conn.execute("""SELECT o.id, o.status, o.shipping_cost, o.return_charge, o.resalable,
                                  p.id AS product_id, p.name, p.selling_price,
                                  p.manufacturing_cost, p.packaging_cost, p.is_custom
                           FROM orders o JOIN products p ON p.id = o.product_id""").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def order_result(order):
    """Calculate one order: sales, profit and loss.

    delivered       -> profit = price - manufacturing - packaging - shipping
    rto             -> loss = product cost, only if the frame cannot be resold (custom frames)
    customer_return -> loss = return charge (+ product cost if damaged or custom)
    """
    made_cost = order["manufacturing_cost"] + order["packaging_cost"]
    if order["status"] == "delivered":
        profit = order["selling_price"] - made_cost - order["shipping_cost"]
        return {"sales": order["selling_price"], "profit": profit, "loss": 0}
    if order["status"] == "rto":
        loss = 0 if order["resalable"] else made_cost
    else:                                                         # customer_return
        loss = order["return_charge"] + (0 if order["resalable"] else made_cost)
    return {"sales": 0, "profit": -loss, "loss": loss}


def profit_summary():
    """Return the overall numbers for the whole business."""
    try:
        orders = get_orders()
        s = {"total_orders": len(orders), "delivered": 0, "rto": 0, "customer_return": 0,
             "dashboard_sales": 0, "sales": 0, "delivered_profit": 0, "return_loss": 0,
             "ads_cost": 0, "adjustments": 0}
        for order in orders:
            result = order_result(order)
            s[order["status"]] += 1
            s["dashboard_sales"] += order.get("dashboard_price", order["selling_price"])   # sales as the dashboard shows them
            s["sales"] += result["sales"]                        # actual sales (delivered orders only)
            s["return_loss"] += result["loss"]
            if order["status"] == "delivered":
                s["delivered_profit"] += result["profit"]
        if data_store.has_real():                                 # costs that are not tied to one order
            s["ads_cost"] = data_store.get_state()["ads_cost"]
            s["adjustments"] = meesho_payments.adjustments()      # claims, compensation, recoveries
        s["net_profit"] = round(s["delivered_profit"] - s["return_loss"] - s["ads_cost"] + s["adjustments"], 2)
        s["margin_pct"] = round(s["net_profit"] / s["sales"] * 100, 1) if s["sales"] else 0
        logger.info(f"profit_summary: net_profit={s['net_profit']} margin={s['margin_pct']}%")
        return s
    except Exception as e:
        raise CustomException(e, sys)


def profit_by_product():
    """Return the numbers for each product, most profitable first."""
    try:
        products = {}
        for order in get_orders():
            p = products.setdefault(order.get("sku", order["name"]), {"name": order["name"], "orders": 0, "delivered": 0,
                                                    "rto": 0, "customer_return": 0, "sales": 0, "net_profit": 0})
            result = order_result(order)
            p["orders"] += 1
            p[order["status"]] += 1
            p["sales"] += result["sales"]
            p["net_profit"] += result["profit"]
        rows = list(products.values())
        for p in rows:
            p["margin_pct"] = round(p["net_profit"] / p["sales"] * 100, 1) if p["sales"] else 0
        return sorted(rows, key=lambda p: p["net_profit"], reverse=True)
    except Exception as e:
        raise CustomException(e, sys)


def return_loss_by_product():
    """Return the return losses for each product, biggest loss first.

    Loss is split into three parts:
      rto_loss      - product cost lost on RTO orders that cannot be resold
      charge_loss   - return charges paid to the platform on customer returns
      damage_loss   - product cost lost on customer returns that cannot be resold
    """
    try:
        products = {}
        for order in get_orders():
            p = products.setdefault(order.get("sku", order["name"]), {"name": order["name"], "orders": 0, "rto": 0,
                                                    "customer_return": 0, "rto_loss": 0,
                                                    "charge_loss": 0, "damage_loss": 0})
            p["orders"] += 1
            if order["status"] == "delivered":
                continue
            made_cost = order["manufacturing_cost"] + order["packaging_cost"]
            lost_product = 0 if order["resalable"] else made_cost
            p[order["status"]] += 1
            if order["status"] == "rto":
                p["rto_loss"] += lost_product
            else:
                p["charge_loss"] += order["return_charge"]
                p["damage_loss"] += lost_product
        rows = list(products.values())
        for p in rows:
            p["total_loss"] = p["rto_loss"] + p["charge_loss"] + p["damage_loss"]
            p["return_rate_pct"] = round((p["rto"] + p["customer_return"]) / p["orders"] * 100, 1)
        return sorted(rows, key=lambda p: p["total_loss"], reverse=True)
    except Exception as e:
        raise CustomException(e, sys)


if __name__ == "__main__":
    s = profit_summary()
    print("Dashboard Sales:", s["dashboard_sales"])
    print("Actual Sales (Delivered):", s["sales"])
    print("Delivered Profit:", s["delivered_profit"])
    print("Return Loss:", s["return_loss"])
    print("Net Profit:", s["net_profit"], f"({s['margin_pct']}%)")
    print(f"Orders: {s['total_orders']} | Delivered {s['delivered']} | RTO {s['rto']} | Customer Return {s['customer_return']}")
    print()
    for p in profit_by_product():
        print(f"{p['name']:<26} profit={p['net_profit']:<8} margin={p['margin_pct']}%  rto={p['rto']} customer_return={p['customer_return']}")
    print()
    print("Return loss by product:")
    for p in return_loss_by_product():
        print(f"{p['name']:<26} total={p['total_loss']:<6} rto={p['rto_loss']:<5} charge={p['charge_loss']:<5} damage={p['damage_loss']:<5} return_rate={p['return_rate_pct']}%")
