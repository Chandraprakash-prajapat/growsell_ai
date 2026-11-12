"""Read real Meesho report files and turn them into simple numbers.

Supported files (all downloaded from the Meesho Supplier Panel):
  1. GST sales report        (tcs_sales.xlsx, or a CSV with the same columns)
  2. GST sales return report (tcs_sales_return.xlsx)
  3. Returns / in-transit report (CSV with a "Meesho Supplier Panel" header block)

Nothing is saved: the files are analysed in memory and then forgotten.
"""
import csv
import io

import pandas as pd

SALES_COLUMNS = ["sub_order_num", "order_date", "total_invoice_value", "end_customer_state_new"]
RETURN_FILE_COLUMNS = ["Product Name", "Type of Return", "Status", "Return Reason"]


class ReportError(Exception):
    """Raised with a plain-English message when a file cannot be read."""


def _read_table(uploaded, name_hint):
    """Read an uploaded .xlsx or .csv file into a DataFrame."""
    name = getattr(uploaded, "name", name_hint).lower()
    try:
        if name.endswith((".xlsx", ".xlsm")):
            return pd.read_excel(uploaded, dtype=str)
        return pd.read_csv(uploaded, dtype=str)
    except Exception as exc:
        raise ReportError(f"Could not open {name_hint}: {exc}") from exc


def _check_columns(df, needed, name_hint):
    """Make sure the file has the columns we need."""
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ReportError(f"{name_hint} looks like the wrong file. Missing columns: {', '.join(missing)}")


def load_gst_report(uploaded, name_hint, is_return=False):
    """Load a GST sales or GST sales-return file with clean number columns.

    is_return=True means the file must be the return report (it has a cancel_return_date column).
    """
    df = _read_table(uploaded, name_hint)
    _check_columns(df, SALES_COLUMNS, name_hint)
    if is_return and "cancel_return_date" not in df.columns:
        raise ReportError(f"{name_hint}: this looks like the GST SALES file. Please upload the sales RETURN file here.")
    if not is_return and "cancel_return_date" in df.columns:
        raise ReportError(f"{name_hint}: this looks like the GST sales RETURN file. Please upload the sales file here.")
    for col in ["total_invoice_value", "total_taxable_sale_value", "tax_amount", "quantity"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df["state"] = df["end_customer_state_new"].fillna("Unknown").str.title()
    return df


def load_return_report(uploaded):
    """Load the returns / in-transit CSV (it has a few info lines above the table)."""
    raw = uploaded.read() if hasattr(uploaded, "read") else open(uploaded, "rb").read()
    text = raw.decode("utf-8-sig", errors="replace")
    rows = list(csv.reader(io.StringIO(text)))
    start = next((i for i, r in enumerate(rows) if r and r[0] == "S No"), None)
    if start is None:
        raise ReportError("The returns file looks like the wrong file (no 'S No' header row found).")
    header = rows[start]
    data = [r for r in rows[start + 1:] if r and r[0].strip() and len(r) == len(header)]
    df = pd.DataFrame(data, columns=header)
    _check_columns(df, RETURN_FILE_COLUMNS, "Returns file")
    df["Product"] = df["Product Name"].str.replace(r"\s+", " ", regex=True).str.split("|").str[1].str.strip()
    df["Product"] = df["Product"].fillna(df["Product Name"]).str.slice(0, 60)
    df["Kind"] = df["Type of Return"].map(
        lambda t: "RTO (cancelled before delivery)" if "RTO" in str(t) else "Customer return")
    return df


def sales_summary(sales):
    """Headline numbers and a state-wise table from the GST sales file."""
    by_state = (sales.groupby("state")
                .agg(orders=("sub_order_num", "count"), sales=("total_invoice_value", "sum"))
                .reset_index())
    return {
        "orders": int(len(sales)),
        "sales": float(sales["total_invoice_value"].sum()),
        "avg_order": float(sales["total_invoice_value"].mean()) if len(sales) else 0.0,
        "by_state": by_state,
    }


def return_summary(sales, returns, charge_per_return):
    """Return rate, money returned, state-wise return rate and the estimated charge cost.

    The GST return file only lists returned or cancelled orders, so the return rate is
    (returned rows) / (sales rows). The charge cost is an estimate: the seller types the
    per-return charge, we do not know it from the files.
    """
    orders, returned = len(sales), len(returns)
    rate = round(returned / orders * 100, 1) if orders else 0.0
    sales_by_state = sales.groupby("state").size().rename("orders")
    returns_by_state = returns.groupby("state").size().rename("returns")
    state = pd.concat([sales_by_state, returns_by_state], axis=1).fillna(0).reset_index()
    state["return_rate_pct"] = (state["returns"] / state["orders"] * 100).round(1)
    state = state.sort_values(["returns", "return_rate_pct"], ascending=False)

    returns = returns.copy()
    returns["days"] = (pd.to_datetime(returns.get("cancel_return_date"), errors="coerce") - returns["order_date"]).dt.days
    monthly = sales.dropna(subset=["order_date"]).groupby(sales["order_date"].dt.date).size()
    return {
        "returned": int(returned),
        "rate_pct": rate,
        "value_returned": float(returns["total_invoice_value"].sum()),
        "charge_cost": float(returned * charge_per_return),
        "avg_days": float(returns["days"].mean()) if returns["days"].notna().any() else 0.0,
        "by_state": state,
        "daily_orders": monthly,
    }


def return_file_summary(df):
    """Split of RTO vs customer returns, by product and by reason, from the returns CSV."""
    by_kind = df.groupby("Kind").size().reset_index(name="count")
    by_product = (df.pivot_table(index="Product", columns="Kind", values="S No", aggfunc="count", fill_value=0)
                  .assign(total=lambda t: t.sum(axis=1)).sort_values("total", ascending=False).reset_index())
    reasons = df[df["Kind"] == "Customer return"]
    by_reason = (reasons.groupby("Detailed Return Reason").size().reset_index(name="count")
                 .sort_values("count", ascending=False))
    return {"total": int(len(df)), "by_kind": by_kind, "by_product": by_product, "by_reason": by_reason}


def facts_for_advisor(sales, ret, file_sum):
    """Short plain-text facts the AI can use (numbers come from Python, not the AI)."""
    lines = []
    if sales:
        lines.append(f"Orders in GST sales file: {sales['orders']}, sales value Rs {sales['sales']:.0f}.")
    if ret:
        lines.append(f"Returned/cancelled orders: {ret['returned']} ({ret['rate_pct']}% of orders).")
        top = ret["by_state"].head(3)
        lines.append("Top return states: " + ", ".join(f"{r.state} ({int(r.returns)})" for r in top.itertuples()))
    if file_sum:
        kinds = ", ".join(f"{r.Kind}: {r.count}" for r in file_sum["by_kind"].itertuples())
        lines.append("Return types: " + kinds)
    return "\n".join(lines)
