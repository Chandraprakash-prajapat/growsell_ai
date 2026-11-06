import streamlit as st

from agent import run_agent
from auth import require_seller_login
from db import clear_action_items, get_action_items, set_action_status, setup_database

st.set_page_config(page_title="AI Advisor", page_icon="🤖", layout="wide")
require_seller_login()
setup_database()

st.title("AI Business Advisor")
st.caption("This is SAMPLE (fake) data, for demo purposes only.")
st.write("The agent checks your numbers with its own tools, finds where you lose money, "
         "suggests what to do and saves the action items below.")

if st.button("Analyze my business", type="primary"):
    with st.spinner("The agent is checking your numbers. This can take about a minute..."):
        try:
            report, tools_used = run_agent()
            st.session_state["report"] = report
            st.session_state["tools_used"] = tools_used
        except Exception:
            st.error("The agent failed. Please try again.")   # the details are already in the log file

if "report" in st.session_state:
    st.subheader("Report")
    st.markdown(st.session_state["report"])
    with st.expander("What the agent did"):
        for number, tool in enumerate(st.session_state["tools_used"], start=1):
            st.write(f"{number}. {tool}")

st.subheader("Action items")
items = get_action_items()
if not items:
    st.write("No action items yet. Click 'Analyze my business'.")
for item in items:
    text_col, button_col = st.columns([6, 1])
    saving = f"₹{item['expected_saving']:,.0f}"
    if item["status"] == "done":
        text_col.write(f"✅ ~~{item['title']}~~")
    else:
        text_col.write(f"⬜ {item['title']}  (expected saving: {saving})")
        if button_col.button("Done", key=f"done_{item['id']}"):
            set_action_status(item["id"], "done")
            st.rerun()

if items and st.button("Clear all action items"):
    clear_action_items()
    st.rerun()