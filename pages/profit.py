import pandas as pd
import streamlit as st

from auth import require_seller_login
from calculations import profit_by_product, profit_summary
from db import setup_database

st.set_page_config(page_title="Profit Calculator", page_icon="💰", layout="wide")
require_seller_login()          # stops the page here until the seller logs in
setup_database()

st.title("Profit Calculator")
st.caption("This is SAMPLE (fake) data, for demo purposes only.")

s = profit_summary()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Dashboard sales", f"₹{s['dashboard_sales']:,.0f}")
c2.metric("Actual sales (delivered)", f"₹{s['sales']:,.0f}")
c3.metric("Return loss", f"₹{s['return_loss']:,.0f}")
c4.metric("Net profit", f"₹{s['net_profit']:,.0f}", f"{s['margin_pct']}% margin", delta_color="off")

st.write(f"Orders: **{s['total_orders']}** | Delivered: **{s['delivered']}** | "
         f"RTO: **{s['rto']}** | Customer return: **{s['customer_return']}**")

st.subheader("Profit by product")
df = pd.DataFrame(profit_by_product()).rename(columns={
    "name": "Product", "orders": "Orders", "delivered": "Delivered", "rto": "RTO",
    "customer_return": "Customer return", "sales": "Sales (₹)",
    "net_profit": "Net profit (₹)", "margin_pct": "Margin %"})
st.bar_chart(df.set_index("Product")["Net profit (₹)"])
st.dataframe(df, hide_index=True)

with st.expander("How the calculation works"):
    st.markdown("""
- **Delivered order:** selling price − manufacturing cost − packaging − shipping
- **RTO** (cancelled before delivery): a normal frame can be resold, so the loss is 0. A custom frame cannot be resold, so its manufacturing cost + packaging is lost.
- **Customer return:** the return charge. If the frame came back damaged or is custom, its manufacturing cost + packaging is lost too.
- **Net profit** = profit from delivered orders − return loss
- **Margin %** = net profit ÷ actual sales × 100
""")