"""Seller login: a simple shared password (good enough for a demo)."""
import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def require_seller_login():
    """Call this at the top of every seller page.

    If the password is not correct, the rest of the page is not shown.
    """
    if st.session_state.get("seller_ok"):
        return
    _, middle, _ = st.columns([1, 1.2, 1])
    with middle:
        st.markdown("### 🔒 Seller login")
        st.caption("This area is only for the shop owner.")
        with st.form("seller_login"):
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log in", type="primary")
        if submitted:
            if password and password == os.getenv("SELLER_PASSWORD"):
                st.session_state["seller_ok"] = True
                st.rerun()
            else:
                st.error("Wrong password")
    st.stop()
