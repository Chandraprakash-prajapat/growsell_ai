import streamlit as st

from agent import run_agent
from auth import require_seller_login
from db import clear_action_items, get_action_items, set_action_status
from ui import action_card, card, kpi_card, page_header, report_card, rupees, timeline

TOOL_LABELS = {
    "get_profit_summary": "Checked the overall profit",
    "get_profit_by_product": "Compared the profit of each product",
    "get_return_loss_by_product": "Looked at the return losses",
    "simulate_return_reduction": "Estimated the saving if returns fall",
    "save_action_item": "Saved an action item",
}

require_seller_login()
page_header("AI Business Advisor",
            "The agent checks your numbers with its own tools, finds where you lose money and saves a to-do list.")

if st.button("Analyze my business", type="primary"):
    with st.spinner("The agent is checking your numbers. This can take about a minute..."):
        try:
            report, tools_used = run_agent()
            st.session_state["report"] = report
            st.session_state["tools_used"] = tools_used
        except Exception:
            st.error("The agent failed. Please try again.")   # the details are already in the log file

items = get_action_items()
open_items = [item for item in items if item["status"] != "done"]
if items:
    cards = [
        kpi_card("trend", "Potential saving", rupees(sum(item["expected_saving"] for item in open_items)),
                 "From the open action items", "green"),
        kpi_card("list", "Open actions", str(len(open_items)), "Still to do", "amber"),
        kpi_card("check", "Completed", str(len(items) - len(open_items)), "Marked as done", "blue"),
    ]
    for column, html in zip(st.columns(3), cards):
        column.markdown(html, unsafe_allow_html=True)

if "report" in st.session_state:
    st.markdown(report_card(st.session_state["report"]), unsafe_allow_html=True)
    steps = [TOOL_LABELS.get(tool, tool) for tool in st.session_state["tools_used"]]
    st.markdown(card("What the agent did", "The tools it used, in order", timeline(steps)), unsafe_allow_html=True)

st.subheader("Action items")
if not items:
    st.caption("No action items yet. Click 'Analyze my business'.")
else:
    done_count = len(items) - len(open_items)
    st.progress(done_count / len(items), text=f"{done_count} of {len(items)} done")

for item in items:
    text_col, button_col = st.columns([6, 1], vertical_alignment="center")
    if item["status"] == "done":
        text_col.markdown(action_card(item["title"], "Done", done=True), unsafe_allow_html=True)
    else:
        text_col.markdown(action_card(item["title"], f"Expected saving: {rupees(item['expected_saving'])}"),
                          unsafe_allow_html=True)
        if button_col.button("Done", key=f"done_{item['id']}"):
            set_action_status(item["id"], "done")
            st.rerun()

if items and st.button("Clear all action items"):
    clear_action_items()
    st.rerun()
