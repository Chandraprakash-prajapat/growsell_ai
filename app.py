import streamlit as st

from db import setup_database
from src.logger import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="GrowSell AI", page_icon="📈")
setup_database()

st.title("GrowSell AI")
st.write("An AI business assistant for e-commerce sellers.")
st.info("Choose a page from the left menu. Seller pages need a password.")
logger.info("Home page opened")