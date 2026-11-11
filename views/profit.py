import streamlit as st

from auth import require_seller_login
from calculations import profit_by_product, profit_summary
from ui import bar_rows, callout, card, data_table, kpi_card, page_header, rupees, waterfall

require_seller_login()          # stops the page here until the seller logs in
page_header("Profit Calculator", "What you really earn after returns, cancelled orders and shipping.")

s = profit_summary()
products = profit_by_product()

cards = [
    kpi_card("cart", "Dashboard sales", rupees(s["dashboard_sales"]), "All orders, even returned ones", "indigo"),
    kpi_card("check", "Actual sales", rupees(s["sales"]), f"{s['delivered']} delivered orders", "blue"),
    kpi_card("refund", "Return loss", rupees(s["return_loss"]),
             f"{s['rto']} RTO and {s['customer_return']} customer returns", "red"),
    kpi_card("trend", "Net profit", rupees(s["net_profit"]), "", "green", chip=f"{s['margin_pct']}% margin"),
]
for column, html in zip(st.columns(4), cards):
    column.markdown(html, unsafe_allow_html=True)

gap = s["dashboard_sales"] - s["sales"]
gap_pct = gap / s["dashboard_sales"] * 100 if s["dashboard_sales"] else 0
st.markdown(callout(
    f"Your dashboard shows <b>{rupees(s['dashboard_sales'])}</b> in sales, but only <b>{rupees(s['sales'])}</b> "
    f"was actually delivered. <b>{rupees(gap)}</b> ({gap_pct:.0f}%) never became income."), unsafe_allow_html=True)

costs = s["sales"] - s["delivered_profit"]          # product, packaging and shipping cost of delivered orders
steps = [
    ("Dashboard sales", s["dashboard_sales"], "total"),
    ("Cancelled and returned orders", -gap, "neg"),
    ("Product, packing and shipping", -costs, "neg"),
    ("Return loss", -s["return_loss"], "neg"),
    ("Net profit", s["net_profit"], "final"),
]
product_rows = [(p["name"], p["net_profit"], f"{p['margin_pct']}% margin · {p['orders']} orders") for p in products]

left, right = st.columns([3, 2])
left.markdown(card("Where your sales money goes", "From dashboard sales to the profit you keep", waterfall(steps)),
              unsafe_allow_html=True)
right.markdown(card("Net profit by product", "Highest first", bar_rows(product_rows, "#10B981")),
               unsafe_allow_html=True)

st.subheader("Product details")
st.markdown(data_table(products, [
    ("Product", "name", "text"), ("Orders", "orders", "int"), ("Delivered", "delivered", "int"),
    ("RTO", "rto", "int"), ("Customer return", "customer_return", "int"), ("Sales", "sales", "money"),
    ("Net profit", "net_profit", "money"), ("Margin", "margin_pct", "pct")]), unsafe_allow_html=True)

with st.expander("How the calculation works"):
    st.markdown("""
- **Delivered order:** selling price − manufacturing cost − packaging − shipping
- **RTO** (cancelled before delivery): a normal frame can be resold, so the loss is 0. A custom frame cannot be resold, so its manufacturing cost + packaging is lost.
- **Customer return:** the return charge. If the frame came back damaged or is custom, its manufacturing cost + packaging is lost too.
- **Net profit** = profit from delivered orders − return loss
- **Margin %** = net profit ÷ actual sales × 100
""")
