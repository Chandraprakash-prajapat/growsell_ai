"""Entry point: sets up the page, the left menu and the login status."""
import streamlit as st

import data_store
from db import setup_database
from src.logger import get_logger
from ui import inject_css

logger = get_logger(__name__)

st.set_page_config(page_title="GrowSell AI", page_icon="📈", layout="wide")
try:
    st.logo("assets/logo.svg", size="large")
except Exception:
    pass                                   # the logo is optional
st.session_state.setdefault("spatial", True)
inject_css(st.session_state.get("dark_mode", False), st.session_state["spatial"])
setup_database()

pages = {
    "Overview": [
        st.Page("views/home.py", title="Home", icon=":material/home:", default=True),
    ],
    "Seller tools": [
        st.Page("views/upload.py", title="Upload My Data", icon=":material/upload_file:"),
        st.Page("views/profit.py", title="Profit Calculator", icon=":material/payments:"),
        st.Page("views/returns.py", title="Return Loss Analyzer", icon=":material/assignment_return:"),
        st.Page("views/advisor.py", title="AI Advisor", icon=":material/smart_toy:"),
    ],
}
page = st.navigation(pages)

with st.sidebar:
    st.toggle("Spatial glass", key="spatial")
    st.toggle("Dark mode", key="dark_mode")
    st.caption("Data: " + ("your uploaded file" if data_store.has_real() else "demo data"))
    if st.session_state.get("seller_ok"):
        st.caption("Signed in as seller")
        if st.button("Log out"):
            st.session_state["seller_ok"] = False
            st.rerun()
    else:
        st.caption("Seller tools need a password")

page.run()
