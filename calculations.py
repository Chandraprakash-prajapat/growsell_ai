import sys

from db import connect
from src.exception import CustomException
from src.logger import get_logger

logger = get_logger(__name__)


def get_orders():
    """Return all orders together with their product details."""
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
             "dashboard_sales": 0, "sales": 0, "delivered_profit": 0, "return_loss": 0}
        for order in orders:
            result = order_result(order)
            s[order["status"]] += 1
            s["dashboard_sales"] += order["selling_price"]       # sales as the dashboard shows them (all orders)
            s["sales"] += result["sales"]                        # actual sales (delivered orders only)
            s["return_loss"] += result["loss"]
            if order["status"] == "delivered":
                s["delivered_profit"] += result["profit"]
        s["net_profit"] = s["delivered_profit"] - s["return_loss"]
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
            p = products.setdefault(order["name"], {"name": order["name"], "orders": 0, "delivered": 0,
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
        


# Run:  uv run python calculations.py 