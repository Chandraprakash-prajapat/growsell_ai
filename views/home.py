import streamlit as st

from ui import icon, tile, tile_head

hero_col, steps_col = st.columns([2, 1])
with hero_col:
    st.markdown(
        '<div class="hero" style="margin-bottom:0">'
        '<div class="tag">AI assistant for online sellers</div>'
        '<h1>Know your real profit.<br>Stop losing money on returns.</h1>'
        '<p>Your marketplace dashboard shows sales. It does not show what returns, cancelled orders and '
        'damaged products really cost you. GrowSell AI shows the real numbers, and an AI agent tells you '
        'what to fix first.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
with steps_col:
    with tile("steps"):
        tile_head("How it works", "Three simple steps")
        st.markdown(
            '<div class="step"><div class="num">1</div><p><b>Your orders</b> are stored with the product cost, '
            'shipping and return details.</p></div>'
            '<div class="step"><div class="num">2</div><p><b>Python does the maths</b>, so every number is exact.</p></div>'
            '<div class="step"><div class="num">3</div><p><b>The AI agent</b> reads the numbers and suggests the '
            'top actions with the expected savings.</p></div>',
            unsafe_allow_html=True,
        )

features = [
    ("wallet", "indigo", "Real profit",
     "Sales on the dashboard include orders that were later returned or cancelled. See the profit you actually keep.",
     "views/profit.py", "Open Profit Calculator"),
    ("box", "amber", "Return losses",
     "See which product loses money through RTO, return charges and damaged frames.",
     "views/returns.py", "Open Return Loss Analyzer"),
    ("bot", "green", "AI advisor",
     "An agent checks your numbers, finds the biggest problem, estimates the savings and saves a to-do list.",
     "views/advisor.py", "Open AI Advisor"),
]
for column, (icon_name, tone, title, text, path, label) in zip(st.columns(3), features):
    with column:
        with tile(f"feature-{icon_name}"):
            st.markdown(f'{icon(icon_name, tone)}<div style="height:10px"></div><div class="gs-title">{title}</div>'
                        f'<div class="gs-card-text" style="opacity:0.8;line-height:1.55;margin-top:6px">{text}</div>',
                        unsafe_allow_html=True)
            st.page_link(path, label=label)

st.caption("This demo uses sample data only. Seller tools need a password. "
           "Use the toggles in the sidebar for Dark mode and the Spatial glass look.")
