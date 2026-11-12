from html import escape

import streamlit as st

from agent import run_agent
from auth import require_seller_login
from db import clear_action_items, get_action_items, set_action_status
from ui import kpi_card, markdown_to_html, page_header, rupees, tile, tile_head, timeline

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

# ---- Row 1: the button (big tile) + three numbers
top = st.columns([2, 1, 1, 1])
with top[0]:
    with tile("run"):
        tile_head("Run the agent", "It reads your numbers, finds the biggest problem and saves action items.")
        run = st.button("Analyze my business", type="primary")

if run:
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
    numbers = [
        kpi_card("trend", "Potential saving", rupees(sum(item["expected_saving"] for item in open_items)),
                 "From the open action items", "green"),
        kpi_card("list", "Open actions", str(len(open_items)), "Still to do", "amber"),
        kpi_card("check", "Completed", str(len(items) - len(open_items)), "Marked as done", "blue"),
    ]
    for column, html in zip(top[1:], numbers):
        column.markdown(html, unsafe_allow_html=True)

# ---- Row 2: report (big tile) + what the agent did
if "report" in st.session_state:
    left, right = st.columns([3, 2])
    with left:
        with tile("report"):
            tile_head("Report", "Written by the agent from your numbers")
            st.markdown(f'<div class="report">{markdown_to_html(st.session_state["report"])}</div>', unsafe_allow_html=True)
    with right:
        with tile("steps"):
            tile_head("What the agent did", "The tools it used, in order")
            steps = [TOOL_LABELS.get(tool, tool) for tool in st.session_state["tools_used"]]
            st.markdown(timeline(steps), unsafe_allow_html=True)

# ---- Row 3: action items as tiles
st.subheader("Action items")
if not items:
    st.caption("No action items yet. Click 'Analyze my business'.")
else:
    done_count = len(items) - len(open_items)
    st.progress(done_count / len(items), text=f"{done_count} of {len(items)} done")
    for start in range(0, len(items), 2):
        for column, item in zip(st.columns(2), items[start:start + 2]):
            with column:
                with tile(f"action-{item['id']}"):
                    if item["status"] == "done":
                        st.markdown(f'<div class="act-title done">✅ {escape(item["title"])}</div>'
                                    f'<div class="gs-sub" style="margin-bottom:0">Done</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="act-title">{escape(item["title"])}</div>'
                                    f'<div class="gs-sub">Expected saving: {rupees(item["expected_saving"])}</div>',
                                    unsafe_allow_html=True)
                        if st.button("Mark as done", key=f"done_{item['id']}"):
                            set_action_status(item["id"], "done")
                            st.rerun()

if items and st.button("Clear all action items"):
    clear_action_items()
    st.rerun()
