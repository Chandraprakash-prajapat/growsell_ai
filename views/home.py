import streamlit as st

from ui import card, icon

st.markdown(
    '<div class="hero">'
    '<div class="tag">AI assistant for online sellers</div>'
    '<h1>Know your real profit.<br>Stop losing money on returns.</h1>'
    '<p>Your marketplace dashboard shows sales. It does not show what returns, cancelled orders and '
    'damaged products really cost you. GrowSell AI shows the real numbers, and an AI agent tells you '
    'what to fix first.</p>'
    '</div>',
    unsafe_allow_html=True,
)

st.subheader("What it does")
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
        body = f'{icon(icon_name, tone)}<div style="height:10px"></div><div class="gs-title">{title}</div><p>{text}</p>'
        st.markdown(f'<div class="gs-card tall">{body}</div>', unsafe_allow_html=True)
        st.page_link(path, label=label)

st.subheader("How it works")
st.markdown(
    '<div class="step"><div class="num">1</div><p><b>Your orders</b> are stored with the product cost, '
    'shipping and return details.</p></div>'
    '<div class="step"><div class="num">2</div><p><b>Python does the maths</b>, so every number is exact.</p></div>'
    '<div class="step"><div class="num">3</div><p><b>The AI agent</b> reads those numbers, decides what to '
    'check next, and suggests the top actions with the expected savings.</p></div>',
    unsafe_allow_html=True,
)
st.caption("This demo uses sample data only. Seller tools need a password. "
           "Use the toggles in the sidebar for Dark mode and the Spatial glass look.")
