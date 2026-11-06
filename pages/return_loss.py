import pandas as pd
import streamlit as st

from auth import require_seller_login
from calculations import return_loss_by_product
from db import setup_database

st.set_page_config(page_title="Return Loss Analyzer", page_icon="📦", layout="wide")
require_seller_login()
setup_database()

st.title("Return Loss Analyzer")
st.caption("This is SAMPLE (fake) data, for demo purposes only.")

rows = return_loss_by_product()
rto_loss = sum(r["rto_loss"] for r in rows)
charge_loss = sum(r["charge_loss"] for r in rows)
damage_loss = sum(r["damage_loss"] for r in rows)
total_loss = rto_loss + charge_loss + damage_loss

c1, c2, c3, c4 = st.columns(4)
c1.metric("RTO loss", f"₹{rto_loss:,.0f}")
c2.metric("Return charges", f"₹{charge_loss:,.0f}")
c3.metric("Damaged / unsellable", f"₹{damage_loss:,.0f}")
c4.metric("Total return loss", f"₹{total_loss:,.0f}")

worst = rows[0]
st.info(f"Biggest loss: **{worst['name']}** lost ₹{worst['total_loss']:,.0f} "
        f"({worst['return_rate_pct']}% of its orders came back).")

df = pd.DataFrame(rows).rename(columns={
    "name": "Product", "orders": "Orders", "rto": "RTO", "customer_return": "Customer return",
    "rto_loss": "RTO loss (₹)", "charge_loss": "Return charges (₹)",
    "damage_loss": "Damaged (₹)", "total_loss": "Total loss (₹)", "return_rate_pct": "Return rate %"})

st.subheader("Loss by product")
st.bar_chart(df.set_index("Product")[["RTO loss (₹)", "Return charges (₹)", "Damaged (₹)"]])
st.dataframe(df, hide_index=True)

with st.expander("What each loss means"):
    st.markdown("""
- **RTO loss:** the order was cancelled before delivery. If the frame cannot be resold (custom frames), its manufacturing cost + packaging is lost.
- **Return charges:** the charge paid on every customer return.
- **Damaged:** the frame came back damaged or is custom, so its manufacturing cost + packaging is lost.
- **Return rate %:** (RTO + customer returns) ÷ total orders × 100
""")