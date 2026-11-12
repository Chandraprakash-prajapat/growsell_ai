"""Read the Meesho Payments report (the "Order Payments" and "Ads Cost" sheets).

Money in this file is exact: for every order it says what Meesho really paid after shipping,
TCS and TDS. The only thing the file cannot know is the product cost, which the seller types.
"""
import re

import pandas as pd

import data_store

STATUS_MAP = {"Delivered": "delivered", "RTO": "rto", "Return": "customer_return"}


class PaymentFileError(Exception):
    """Raised with a plain-English message when the file is not a Meesho payments report."""


def _find_column(columns, start):
    """Find the column whose name starts with `start` (the file has very long names)."""
    for col in columns:
        if str(col).strip().lower().startswith(start.lower()):
            return col
    raise PaymentFileError(f"The file has no '{start}' column. Is this the Meesho Payments report?")


def _short_name(raw):
    """Make a readable product name from the long marketplace title."""
    text = re.sub(r"^\s*c\s*sun\s*enterprises\s*\|?\s*", "", str(raw), flags=re.I)
    text = text.split("|")[0].strip() or str(raw)
    return text[:42]


def parse_payment_file(uploaded):
    """Parse the uploaded .xlsx. Returns (rows, ads_cost). Each row is one order."""
    try:
        sheets = pd.read_excel(uploaded, sheet_name=None, header=None, dtype=str)
    except Exception as exc:
        raise PaymentFileError(f"Could not open the file: {exc}") from exc
    if "Order Payments" not in sheets:
        raise PaymentFileError("No 'Order Payments' sheet found. Please upload the Meesho Payments report (.xlsx).")

    raw = sheets["Order Payments"]
    header_at = next((i for i in range(min(10, len(raw))) if str(raw.iloc[i, 0]).strip() == "Sub Order No"), None)
    if header_at is None:
        raise PaymentFileError("Could not find the 'Sub Order No' header row in the Order Payments sheet.")
    table = raw.iloc[header_at + 1:].copy()
    table.columns = [str(c).strip() for c in raw.iloc[header_at]]
    table = table[table["Sub Order No"].notna()]

    status_col = _find_column(table.columns, "Live Order Status")
    settle_col = _find_column(table.columns, "Final Settlement Amount")
    sale_col = _find_column(table.columns, "Total Sale Amount")
    sku_col = _find_column(table.columns, "Supplier SKU")
    name_col = _find_column(table.columns, "Product Name")
    date_col = _find_column(table.columns, "Order Date")

    rows = []
    for rec in table.to_dict("records"):
        settlement = pd.to_numeric(rec[settle_col], errors="coerce")
        gross = pd.to_numeric(rec[sale_col], errors="coerce")
        rows.append({
            "order_id": rec["Sub Order No"],
            "order_date": str(rec[date_col])[:10],
            "sku": str(rec[sku_col]).strip() if pd.notna(rec[sku_col]) else "Unknown",
            "name": _short_name(rec[name_col]) if pd.notna(rec[name_col]) else "Unknown",
            "status": rec[status_col] if pd.notna(rec[status_col]) else "Adjustment",
            "gross": 0.0 if pd.isna(gross) else float(gross),
            "settlement": 0.0 if pd.isna(settlement) else float(settlement),
        })
    if not rows:
        raise PaymentFileError("The Order Payments sheet has no orders.")

    ads_cost = 0.0
    if "Ads Cost" in sheets:
        ads = sheets["Ads Cost"]
        at = next((i for i in range(min(10, len(ads))) if str(ads.iloc[i, 0]).strip() == "Deduction Duration"), None)
        if at is not None:
            body = ads.iloc[at + 1:].copy()
            body.columns = [str(c).strip() for c in ads.iloc[at]]
            if "Total Ads Cost" in body.columns:
                ads_cost = float(-pd.to_numeric(body["Total Ads Cost"], errors="coerce").fillna(0).sum())
    return rows, round(ads_cost, 2)


def real_orders():
    """Turn the stored rows into the same order dictionaries the calculations already use.

    delivered       selling_price = sale amount, shipping_cost = everything Meesho deducted
                    (shipping, TCS, TDS), so price - product cost - deductions = what you really keep
    rto             nothing is charged by Meesho; the made frame is lost
    customer_return the return charge Meesho deducted (about 205) + the made frame is lost
    Rows that are not orders (claims, compensation, recoveries, cancelled) are counted in adjustments().
    """
    state = data_store.get_state()
    skus_by_name = {}
    for r in state["rows"] or []:
        skus_by_name.setdefault(r["name"], set()).add(r["sku"])
    orders = []
    for r in state["rows"] or []:
        status = STATUS_MAP.get(r["status"])
        if status is None:
            continue
        cost = state["costs"].get(r["sku"], state["default_cost"])
        deductions = max(r["gross"] - r["settlement"], 0) if status == "delivered" else 0
        orders.append({
            "id": r["order_id"], "status": status, "shipping_cost": deductions,
            "return_charge": max(-r["settlement"], 0) if status == "customer_return" else 0,
            "resalable": 0, "product_id": r["sku"], "name": r["name"] if len(skus_by_name[r["name"]]) == 1 else f'{r["name"]} ({r["sku"][:16]})',
            "selling_price": r["gross"], "dashboard_price": r["gross"],
            "manufacturing_cost": cost, "packaging_cost": 0, "is_custom": 1,
            "sku": r["sku"], "order_date": r["order_date"],
        })
    return orders


def adjustments():
    """Money from rows that are not normal orders (claims, compensation, recoveries, cancelled)."""
    rows = data_store.get_state()["rows"] or []
    return round(sum(r["settlement"] for r in rows if r["status"] not in STATUS_MAP), 2)


def sku_table():
    """One row per SKU: name, orders, and the cost currently used. Used by the cost editor."""
    state = data_store.get_state()
    seen = {}
    for r in state["rows"] or []:
        if r["status"] in STATUS_MAP:
            item = seen.setdefault(r["sku"], {"SKU": r["sku"], "Product": r["name"], "Orders": 0})
            item["Orders"] += 1
    rows = sorted(seen.values(), key=lambda x: x["Orders"], reverse=True)
    for item in rows:
        item["Cost per piece (₹)"] = state["costs"].get(item["SKU"], state["default_cost"])
    return rows
