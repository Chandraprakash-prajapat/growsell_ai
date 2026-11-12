import pandas as pd
import streamlit as st

from auth import require_seller_login
from calculations import profit_by_product, profit_summary
from ui import kpi_card, page_header, rupees, tile, tile_head, waterfall

require_seller_login()          # stops the page here until the seller logs in
page_header("Profit Calculator", "What you really earn after returns, cancelled orders and shipping.")

s = profit_summary()
products = profit_by_product()
gap = s["dashboard_sales"] - s["sales"]
gap_pct = gap / s["dashboard_sales"] * 100 if s["dashboard_sales"] else 0
costs = s["sales"] - s["delivered_profit"]          # product cost plus shipping and fees of delivered orders
other = s["ads_cost"] - s["adjustments"]            # ads minus claims and compensation (0 for demo data)

# ---- Row 1: the key numbers (the first one is the big tile)
cards = [
    kpi_card("trend", "Net profit", rupees(s["net_profit"]), "What you really keep", "green",
             chip=f"{s['margin_pct']}% margin", accent=True),
    kpi_card("cart", "Dashboard sales", rupees(s["dashboard_sales"]), "All orders, even returned ones", "indigo"),
    kpi_card("check", "Actual sales", rupees(s["sales"]), f"{s['delivered']} delivered orders", "blue"),
    kpi_card("refund", "Return loss", rupees(s["return_loss"]),
             f"{s['rto']} RTO and {s['customer_return']} customer returns", "red"),
]
for column, html in zip(st.columns([1.5, 1, 1, 1]), cards):
    column.markdown(html, unsafe_allow_html=True)

# ---- Row 2: money flow (big tile) + two smaller tiles
steps = [
    ("Dashboard sales", s["dashboard_sales"], "total"),
    ("Cancelled and returned orders", -gap, "neg"),
    ("Product cost, shipping and fees", -costs, "neg"),
    ("Return loss", -s["return_loss"], "neg"),
]
if other > 0:
    steps.append(("Ads cost, net of claims", -other, "neg"))
elif other < 0:
    steps.append(("Claims and compensation", -other, "pos"))
steps.append(("Net profit", s["net_profit"], "final"))
flow_csv = pd.DataFrame([{"Step": label, "Amount (₹)": value} for label, value, _ in steps]).to_csv(index=False)
chart_data = pd.DataFrame(products).set_index("name")[["net_profit"]].rename(columns={"net_profit": "Net profit (₹)"})

left, right = st.columns([3, 2])
with left:
    with tile("flow"):
        tile_head("Where your sales money goes", "From dashboard sales to the profit you keep")
        st.markdown(waterfall(steps, height=300), unsafe_allow_html=True)
        st.download_button("Download CSV", flow_csv, "money_flow.csv", "text/csv", key="download_flow")
with right:
    with tile("reality"):
        tile_head("Reality check", "Dashboard sales vs delivered sales")
        st.markdown(f'<div class="stat-big amber">{gap_pct:.0f}%</div>'
                    f'<div class="stat-text">of your dashboard sales (<b>{rupees(gap)}</b>) never became income. '
                    f'Your dashboard shows <b>{rupees(s["dashboard_sales"])}</b>, but only <b>{rupees(s["sales"])}</b> '
                    f'was delivered.</div>', unsafe_allow_html=True)
    with tile("by-product"):
        tile_head("Net profit by product", "Highest first")
        st.bar_chart(chart_data, color="#10B981", horizontal=True, height=240)

# ---- Row 3: the full table (sort, search, download and full screen work as usual)
df = pd.DataFrame(products).rename(columns={
    "name": "Product", "orders": "Orders", "delivered": "Delivered", "rto": "RTO",
    "customer_return": "Customer return", "sales": "Sales (₹)",
    "net_profit": "Net profit (₹)", "margin_pct": "Margin %"})
with tile("table"):
    tile_head("Product details", "Click a column to sort. Use the icons on the top right of the table to search, download or open it full screen.")
    st.dataframe(
        df, hide_index=True,
        column_config={
            "Sales (₹)": st.column_config.NumberColumn(format="₹%d"),
            "Net profit (₹)": st.column_config.NumberColumn(format="₹%d"),
            "Margin %": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100),
        },
    )

with st.expander("How the calculation works"):
    st.markdown("""
- **Delivered order:** selling price − product cost − shipping, TCS and TDS that Meesho deducted
- **RTO** (cancelled before delivery): a normal frame can be resold, so the loss is 0. A custom frame cannot be resold, so its manufacturing cost + packaging is lost.
- **Customer return:** the return charge. If the frame came back damaged or is custom, its manufacturing cost + packaging is lost too.
- **Net profit** = profit from delivered orders − return loss − ads cost + claims and compensation (ads and claims appear only with your uploaded Meesho data)
- **Margin %** = net profit ÷ actual sales × 100
""")
