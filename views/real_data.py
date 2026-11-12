"""Upload page: the seller analyses real Meesho report files. Nothing is saved."""
import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

from agent import MODEL
from auth import require_seller_login
from real_reports import (ReportError, facts_for_advisor, load_gst_report, load_return_report,
                          return_file_summary, return_summary, sales_summary)
from ui import callout, donut, kpi_card, page_header, report_card, rupees, tile, tile_head

load_dotenv()
AMBER, INDIGO = "#F59E0B", "#6366F1"

require_seller_login()
page_header("Real Data Analyzer",
            "Upload your own Meesho report files and see your real return problem. Files are read in memory and never saved.")

# ---- Row 1: uploads
with tile("upload"):
    tile_head("Upload your reports", "Any one file works. Upload more files to see more.")
    c1, c2, c3 = st.columns(3)
    sales_file = c1.file_uploader("GST sales report", type=["xlsx", "csv"], help="tcs_sales.xlsx from the GST reports zip")
    return_gst_file = c2.file_uploader("GST sales return report", type=["xlsx", "csv"], help="tcs_sales_return.xlsx")
    returns_csv = c3.file_uploader("Returns / in-transit report", type=["csv"], help="CSV from the Returns section")
    charge = st.number_input("Charge Meesho takes per customer return (₹)", min_value=0, max_value=2000,
                             value=200, step=10,
                             help="An assumption. Change it to your real charge. It is used only for the estimate below.")

if not (sales_file or return_gst_file or returns_csv):
    st.info("Upload at least one file above to start.")
    st.stop()

sales = returns = file_df = None
try:
    if sales_file:
        sales = load_gst_report(sales_file, "GST sales report")
    if return_gst_file:
        returns = load_gst_report(return_gst_file, "GST sales return report", is_return=True)
    if returns_csv:
        file_df = load_return_report(returns_csv)
except ReportError as error:
    st.error(str(error))
    st.stop()

sales_sum = sales_summary(sales) if sales is not None else None
ret_sum = return_summary(sales, returns, charge) if (sales is not None and returns is not None) else None
file_sum = return_file_summary(file_df) if file_df is not None else None

# ---- Row 2: the key numbers
cards = []
if ret_sum:
    cards = [
        kpi_card("alert", "Return rate", f'{ret_sum["rate_pct"]}%',
                 f'{ret_sum["returned"]} of {sales_sum["orders"]} orders', "red", accent=True),
        kpi_card("wallet", "Sales (with GST)", rupees(sales_sum["sales"]), f'{sales_sum["orders"]} orders', "indigo"),
        kpi_card("refund", "Value returned", rupees(ret_sum["value_returned"]), "Invoice value of returned orders", "amber"),
        kpi_card("box", "Estimated charges", rupees(ret_sum["charge_cost"]), f"{ret_sum['returned']} × ₹{charge}", "red"),
    ]
elif sales_sum:
    cards = [
        kpi_card("wallet", "Sales (with GST)", rupees(sales_sum["sales"]), "", "indigo", accent=True),
        kpi_card("cart", "Orders", str(sales_sum["orders"]), "", "indigo"),
        kpi_card("trend", "Average order", rupees(sales_sum["avg_order"]), "", "indigo"),
    ]
if cards:
    for column, html in zip(st.columns([1.5] + [1] * (len(cards) - 1)), cards):
        column.markdown(html, unsafe_allow_html=True)
    st.markdown(callout("The return rate is (returned rows ÷ sales rows). Some returns can belong to orders "
                        "from an earlier month, so treat it as a close estimate.", "amber") if ret_sum else "",
                unsafe_allow_html=True)

# ---- Row 3: states
if ret_sum:
    states = ret_sum["by_state"].rename(columns={"state": "State", "orders": "Orders", "returns": "Returns",
                                                  "return_rate_pct": "Return rate %"})
    left, right = st.columns([3, 2])
    with left:
        with tile("state-chart"):
            tile_head("Returns by state", "Top 10 states with the most returns")
            st.bar_chart(states.head(10).set_index("State")[["Returns"]], color=[AMBER], horizontal=True, height=360)
            st.download_button("Download CSV", states.to_csv(index=False), "returns_by_state.csv", "text/csv",
                               key="dl_state")
    with right:
        worst = states[states["Orders"] >= 10].sort_values("Return rate %", ascending=False).head(1)
        with tile("state-worst"):
            tile_head("Highest return rate", "States with at least 10 orders")
            if len(worst):
                row = worst.iloc[0]
                st.markdown(f'<div class="stat-big amber">{row["Return rate %"]}%</div>'
                            f'<div class="stat-text"><b>{row["State"]}</b>: {int(row["Returns"])} returns out of '
                            f'{int(row["Orders"])} orders.</div>', unsafe_allow_html=True)
            else:
                st.caption("Not enough orders per state yet.")
        with tile("days"):
            tile_head("Time to return", "Average days from order to return or cancel")
            st.markdown(f'<div class="stat-big">{ret_sum["avg_days"]:.1f}</div><div class="stat-text">days</div>',
                        unsafe_allow_html=True)
    with tile("state-table"):
        tile_head("All states", "Click a column to sort. Use the table icons to search or open it full screen.")
        st.dataframe(states, hide_index=True, column_config={
            "Return rate %": st.column_config.ProgressColumn(
                format="%.1f%%", min_value=0, max_value=max(float(states["Return rate %"].max()), 1.0))})

# ---- Row 4: RTO vs customer return (from the returns CSV)
if file_sum:
    kinds = {row.Kind: int(row.count) for row in file_sum["by_kind"].itertuples()}
    parts = [("RTO (cancelled)", kinds.get("RTO (cancelled before delivery)", 0), AMBER),
             ("Customer return", kinds.get("Customer return", 0), INDIGO)]
    products = file_sum["by_product"].rename(columns={"RTO (cancelled before delivery)": "RTO",
                                                      "Customer return": "Customer return", "total": "Total"})
    for needed in ("RTO", "Customer return"):
        if needed not in products.columns:
            products[needed] = 0
    left, right = st.columns([3, 2])
    with left:
        with tile("product-returns"):
            tile_head("Returns by product", "From your returns file")
            st.bar_chart(products.set_index("Product")[["RTO", "Customer return"]], color=[AMBER, INDIGO],
                         horizontal=True, height=360)
            st.download_button("Download CSV", products.to_csv(index=False), "returns_by_product.csv", "text/csv",
                               key="dl_prod")
    with right:
        with tile("rto-split"):
            tile_head("RTO vs customer return", "RTO frames (custom) cannot be resold")
            st.markdown(donut(parts, str(file_sum["total"]), "returns"), unsafe_allow_html=True)
        reasons = file_sum["by_reason"].rename(columns={"Detailed Return Reason": "Customer's reason", "count": "Count"})
        with tile("reasons"):
            tile_head("Why customers return", "Reasons given on customer returns")
            if len(reasons):
                st.dataframe(reasons, hide_index=True)
            else:
                st.caption("No customer returns in this file.")


# ---- Row 5: AI advice on the real numbers
def ask_ai(facts):
    """Ask the model for advice. It only explains the numbers that Python calculated."""
    prompt = ("You advise a small Indian online seller (photo frames on Meesho). Use ONLY these facts, "
              "never invent numbers. Use ₹. Give: **Biggest problem**, **Top 3 suggestions** (specific, e.g. which "
              "state or return type to act on), **Next step**. Keep it short.\n\n" + facts)
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": prompt}]) \
        .choices[0].message.content


with tile("ai"):
    tile_head("Ask the AI about this data", "Python calculates the numbers, the AI only explains and advises.")
    if st.button("Get advice on my real data", type="primary"):
        facts = facts_for_advisor(sales_sum, ret_sum, file_sum)
        with st.spinner("Thinking..."):
            try:
                st.session_state["real_advice"] = ask_ai(facts)
            except Exception as error:               # network or key problem: show a short message
                st.session_state["real_advice"] = None
                st.error(f"The AI could not answer right now: {error}")
    if st.session_state.get("real_advice"):
        st.markdown(report_card(st.session_state["real_advice"]), unsafe_allow_html=True)
