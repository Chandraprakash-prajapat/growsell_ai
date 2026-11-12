"""Upload page: the seller uploads the Meesho Payments report and sets the product cost."""
import pandas as pd
import streamlit as st

import data_store
import meesho_payments
from auth import require_seller_login
from calculations import profit_summary
from ui import callout, kpi_card, page_header, rupees, tile, tile_head

require_seller_login()
page_header("Upload My Data",
            "Upload your Meesho Payments report. Every page then shows your real numbers. "
            "Your file is kept in memory only, never saved to disk.")

state = data_store.get_state()

# ---- Row 1: upload
with tile("upload-payments"):
    tile_head("1. Meesho Payments report",
              "Supplier Panel → Payments → download the report (.xlsx with the Order Payments sheet).")
    uploaded = st.file_uploader("Payments report (.xlsx)", type=["xlsx"], key="payments_file")
    if uploaded is not None and state["file_name"] != uploaded.name:
        try:
            rows, ads_cost = meesho_payments.parse_payment_file(uploaded)
        except meesho_payments.PaymentFileError as error:
            st.error(str(error))
        else:
            data_store.set_real(rows, ads_cost, uploaded.name)
            st.rerun()
    if data_store.has_real():
        st.success(f"Using your data: {state['file_name']}")
        if st.button("Clear my data"):
            data_store.clear()
            st.rerun()

if not data_store.has_real():
    st.info("No file uploaded yet, so the other pages show demo data.")
    st.stop()

# ---- Row 2: product cost
with tile("cost"):
    tile_head("2. Product cost", "Frame + print + packing for one piece. Meesho files do not contain this, so you enter it.")
    default_cost = st.number_input("Cost per piece for all products (₹)", min_value=0.0, max_value=5000.0,
                                   value=float(state["default_cost"]), step=5.0)
    if default_cost != state["default_cost"]:               # a new default replaces any per-product costs
        data_store.set_costs(default_cost, {})
        st.rerun()
    with st.expander("A different cost for some products?"):
        edited = st.data_editor(pd.DataFrame(meesho_payments.sku_table()), hide_index=True,
                                disabled=["SKU", "Product", "Orders"], key=f"cost_editor_{default_cost}")
        st.caption("Change a number only where the cost is different from the default above.")
    costs = {row["SKU"]: float(row["Cost per piece (₹)"]) for _, row in edited.iterrows()
             if float(row["Cost per piece (₹)"]) != default_cost}
    if costs != state["costs"]:
        data_store.set_costs(default_cost, costs)
        st.rerun()

# ---- Row 3: what the file says
s = profit_summary()
cards = [
    kpi_card("trend", "Net profit", rupees(s["net_profit"]), "After cost, returns, ads", "green", chip=f"{s['margin_pct']}% margin", accent=True),
    kpi_card("cart", "Dashboard sales", rupees(s["dashboard_sales"]), f"{s['total_orders']} orders", "indigo"),
    kpi_card("refund", "Return loss", rupees(s["return_loss"]), f"{s['rto']} RTO, {s['customer_return']} returns", "red"),
    kpi_card("box", "Ads cost", rupees(s["ads_cost"]), "From the Ads Cost sheet", "amber"),
]
for column, html in zip(st.columns([1.5, 1, 1, 1]), cards):
    column.markdown(html, unsafe_allow_html=True)
st.markdown(callout("Returned frames (RTO and customer returns) are counted as lost, because custom frames cannot be resold. "
                    "Meesho's return charge comes from your file. Open Profit Calculator, Return Loss Analyzer and AI Advisor "
                    "from the menu to see the details."), unsafe_allow_html=True)
