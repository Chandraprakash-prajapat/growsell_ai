import sys

import streamlit as st

from src.exception import CustomException
from src.logger import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="GrowSell AI", page_icon="📈")
st.title("GrowSell AI")
st.write("Setup ho gaya!")
logger.info("App shuru hua")

if st.button("Error test karo"):
    try:
        1 / 0
    except Exception as e:
        CustomException(e, sys)  # ye khud log me likh deta hai
        st.error("Kuch gadbad hui, log me save ho gaya.")