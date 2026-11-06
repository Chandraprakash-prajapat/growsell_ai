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
    st.subheader("Seller login")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if password and password == os.getenv("SELLER_PASSWORD"):
            st.session_state["seller_ok"] = True
            st.rerun()
        else:
            st.error("Wrong password")
    st.stop()