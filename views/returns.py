import streamlit as st

from auth import require_seller_login
from calculations import return_loss_by_product
from ui import callout, card, data_table, donut, kpi_card, page_header, rupees, stacked_rows

RTO_COLOR, CHARGE_COLOR, DAMAGE_COLOR = "#F59E0B", "#6366F1", "#EF4444"

require_seller_login()
page_header("Return Loss Analyzer", "Where returns and cancelled orders cost you money.")

rows = return_loss_by_product()
rto_loss = sum(r["rto_loss"] for r in rows)
charge_loss = sum(r["charge_loss"] for r in rows)
damage_loss = sum(r["damage_loss"] for r in rows)
total_loss = rto_loss + charge_loss + damage_loss

cards = [
    kpi_card("box", "RTO loss", rupees(rto_loss), "Cancelled, cannot be resold", "amber"),
    kpi_card("refund", "Return charges", rupees(charge_loss), "Paid on customer returns", "indigo"),
    kpi_card("alert", "Damaged / unsellable", rupees(damage_loss), "Product cost lost", "red"),
    kpi_card("wallet", "Total return loss", rupees(total_loss), "", "red"),
]
for column, html in zip(st.columns(4), cards):
    column.markdown(html, unsafe_allow_html=True)

worst = rows[0]
st.markdown(callout(
    f"Biggest loss: <b>{worst['name']}</b> lost <b>{rupees(worst['total_loss'])}</b>, and "
    f"{worst['return_rate_pct']}% of its orders came back.", "amber"), unsafe_allow_html=True)

series = [("RTO loss", RTO_COLOR), ("Return charges", CHARGE_COLOR), ("Damaged", DAMAGE_COLOR)]
product_rows = [(r["name"], [r["rto_loss"], r["charge_loss"], r["damage_loss"]],
                 f"{r['return_rate_pct']}% of orders returned") for r in rows]
parts = [("RTO loss", rto_loss, RTO_COLOR), ("Return charges", charge_loss, CHARGE_COLOR),
         ("Damaged", damage_loss, DAMAGE_COLOR)]

left, right = st.columns([3, 2])
left.markdown(card("Loss by product", "Biggest loss first", stacked_rows(product_rows, series)),
              unsafe_allow_html=True)
right.markdown(card("Loss by type", "What kind of loss it is", donut(parts, rupees(total_loss), "total loss")),
               unsafe_allow_html=True)

st.subheader("Product details")
st.markdown(data_table(rows, [
    ("Product", "name", "text"), ("Orders", "orders", "int"), ("RTO", "rto", "int"),
    ("Customer return", "customer_return", "int"), ("RTO loss", "rto_loss", "money"),
    ("Return charges", "charge_loss", "money"), ("Damaged", "damage_loss", "money"),
    ("Total loss", "total_loss", "money"), ("Return rate", "return_rate_pct", "pct")],
    pct_max=max(max(row["return_rate_pct"] for row in rows), 1)), unsafe_allow_html=True)

with st.expander("What each loss means"):
    st.markdown("""
- **RTO loss:** the order was cancelled before delivery. If the frame cannot be resold (custom frames), its manufacturing cost + packaging is lost.
- **Return charges:** the charge paid on every customer return.
- **Damaged:** the frame came back damaged or is custom, so its manufacturing cost + packaging is lost.
- **Return rate %:** (RTO + customer returns) ÷ total orders × 100
""")
