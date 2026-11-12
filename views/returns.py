import pandas as pd
import streamlit as st

from auth import require_seller_login
from calculations import return_loss_by_product
from ui import donut, kpi_card, page_header, rupees, tile, tile_head, callout

RTO_COLOR, CHARGE_COLOR, DAMAGE_COLOR = "#F59E0B", "#6366F1", "#EF4444"

require_seller_login()
page_header("Return Loss Analyzer", "Where returns and cancelled orders cost you money.")

rows = return_loss_by_product()
rto_loss = sum(r["rto_loss"] for r in rows)
charge_loss = sum(r["charge_loss"] for r in rows)
damage_loss = sum(r["damage_loss"] for r in rows)
total_loss = rto_loss + charge_loss + damage_loss

# ---- Row 1: the key numbers (the first one is the big tile)
cards = [
    kpi_card("wallet", "Total return loss", rupees(total_loss), "RTO + charges + damaged", "red", accent=True),
    kpi_card("box", "RTO loss", rupees(rto_loss), "Cancelled, cannot be resold", "amber"),
    kpi_card("refund", "Return charges", rupees(charge_loss), "Paid on customer returns", "indigo"),
    kpi_card("alert", "Damaged / unsellable", rupees(damage_loss), "Product cost lost", "red"),
]
for column, html in zip(st.columns([1.5, 1, 1, 1]), cards):
    column.markdown(html, unsafe_allow_html=True)

# ---- Row 2: loss by product (big tile) + insight and loss by type
df = pd.DataFrame(rows).rename(columns={
    "name": "Product", "orders": "Orders", "rto": "RTO", "customer_return": "Customer return",
    "rto_loss": "RTO loss (₹)", "charge_loss": "Return charges (₹)",
    "damage_loss": "Damaged (₹)", "total_loss": "Total loss (₹)", "return_rate_pct": "Return rate %"})
loss_columns = ["RTO loss (₹)", "Return charges (₹)", "Damaged (₹)"]
parts = [("RTO loss", rto_loss, RTO_COLOR), ("Return charges", charge_loss, CHARGE_COLOR),
         ("Damaged", damage_loss, DAMAGE_COLOR)]
type_csv = pd.DataFrame([{"Type": label, "Amount (₹)": value} for label, value, _ in parts]).to_csv(index=False)
worst = rows[0]

left, right = st.columns([3, 2])
with left:
    with tile("by-product"):
        tile_head("Loss by product", "Biggest loss first (use the icon on the chart to open it full screen)")
        st.bar_chart(df.set_index("Product")[loss_columns], color=[RTO_COLOR, CHARGE_COLOR, DAMAGE_COLOR],
                     horizontal=True, height=440)
        st.download_button("Download CSV", df[["Product"] + loss_columns].to_csv(index=False),
                           "loss_by_product.csv", "text/csv", key="download_loss")
with right:
    with tile("worst"):
        tile_head("Biggest loss", "The product to fix first")
        st.markdown(f'<div class="stat-big amber">{rupees(worst["total_loss"])}</div>'
                    f'<div class="stat-text"><b>{worst["name"]}</b> lost this much, and '
                    f'{worst["return_rate_pct"]}% of its orders came back.</div>', unsafe_allow_html=True)
    with tile("by-type"):
        tile_head("Loss by type", "What kind of loss it is")
        st.markdown(donut(parts, rupees(total_loss), "total loss"), unsafe_allow_html=True)
        st.download_button("Download CSV", type_csv, "loss_by_type.csv", "text/csv", key="download_type")

# ---- Row 3: the full table (sort, search, download and full screen work as usual)
with tile("table"):
    tile_head("Product details", "Click a column to sort. Use the icons on the top right of the table to search, download or open it full screen.")
    st.dataframe(
        df, hide_index=True,
        column_config={
            "RTO loss (₹)": st.column_config.NumberColumn(format="₹%d"),
            "Return charges (₹)": st.column_config.NumberColumn(format="₹%d"),
            "Damaged (₹)": st.column_config.NumberColumn(format="₹%d"),
            "Total loss (₹)": st.column_config.NumberColumn(format="₹%d"),
            "Return rate %": st.column_config.ProgressColumn(
                format="%.1f%%", min_value=0, max_value=max(float(df["Return rate %"].max()), 1.0)),
        },
    )

with st.expander("What each loss means"):
    st.markdown("""
- **RTO loss:** the order was cancelled before delivery. If the frame cannot be resold (custom frames), its manufacturing cost + packaging is lost.
- **Return charges:** the charge paid on every customer return.
- **Damaged:** the frame came back damaged or is custom, so its manufacturing cost + packaging is lost.
- **Return rate %:** (RTO + customer returns) ÷ total orders × 100
""")
