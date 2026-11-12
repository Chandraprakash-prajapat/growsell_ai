"""The AI agent: an LLM that decides which tools to run, reads the results and saves action items.

All money math is done by our Python functions (tools). The LLM only explains and advises.
Run:  uv run python agent.py
"""
import json
import os
import sys

from dotenv import load_dotenv
from groq import Groq

from calculations import profit_by_product, profit_summary, return_loss_by_product
from db import add_action_item, setup_database
from src.exception import CustomException
from src.logger import get_logger

load_dotenv()
logger = get_logger(__name__)

MODEL = "openai/gpt-oss-20b"
MAX_STEPS = 8          # safety limit: the agent cannot loop forever
TOP_PRODUCTS = 6       # tools send only the most important products, so the model reads less and answers faster

SYSTEM_PROMPT = """You are a business advisor for an Indian e-commerce seller who sells photo frames on Meesho.
Goal: find where the seller loses money and how to increase profit.

Rules:
- Always use the tools to get numbers. Never calculate or guess numbers yourself.
- Write every amount in Indian rupees using the symbol ₹ (never $) and the Indian digit grouping, for example ₹1,15,177.
- First look at the overall profit, then the profit and the return loss for each product.
- Use simulate_return_reduction to estimate how much money a suggestion can save.
- When several tools do not depend on each other, call them together in the same step.
- Suggestions must be specific to the numbers you see. Typical levers: better packaging for products
  with high damage loss; making custom frames only after the customer confirms a preview (custom frames
  cannot be resold, so their RTO loss is the full product cost); fixing the products with the highest
  return rate or lowest margin.
- Be fast. Plan: step 1 call get_profit_summary, get_profit_by_product and get_return_loss_by_product together;
  step 2 call simulate_return_reduction for the 3 products with the biggest loss, all together;
  step 3 call save_action_item three times, all together; then write the report. Do not call any other tools.
- Suggestions must be concrete and based on the data. Useful ideas: better packaging when the damaged loss is high,
  asking the customer to confirm the preview before making a custom frame when the RTO loss is high,
  fixing the product that has the highest return rate.
- For each of your top 3 suggestions, call save_action_item once.
- Finish with a short report in English with exactly these parts:
  **Biggest problem** (1-2 sentences with numbers)
  **Top 3 suggestions** (each with the expected saving in ₹)
  **Next step** (one sentence)
"""


# ---------- Tools (plain Python functions the agent can call) ----------

def tool_get_profit_summary(**_):
    return profit_summary()


def _top(rows, count=TOP_PRODUCTS):
    """Keep only the first `count` rows (the lists are already sorted), and say how many exist."""
    return {"total_products": len(rows), "shown": min(count, len(rows)), "products": rows[:count]}


def tool_get_profit_by_product(**_):
    rows = profit_by_product()                       # most profitable first
    return {"total_products": len(rows), "best": rows[:3], "worst": rows[-3:] if len(rows) > 3 else []}


def tool_get_return_loss_by_product(**_):
    return _top(return_loss_by_product())            # biggest loss first


def tool_simulate_return_reduction(product_name, reduction_pct):
    """Estimate the saving if the return loss of a product falls by reduction_pct percent."""
    for row in return_loss_by_product():
        if row["name"].lower() == product_name.lower():
            saving = round(row["total_loss"] * reduction_pct / 100, 2)
            return {"product": row["name"], "current_loss": row["total_loss"],
                    "reduction_pct": reduction_pct, "estimated_saving": saving,
                    "note": "Assumes the loss falls in the same proportion."}
    return {"error": f"Product not found: {product_name}"}


def tool_save_action_item(title, expected_saving=0):
    saved = add_action_item(title, expected_saving)
    return {"saved": saved, "title": title}


TOOL_FUNCTIONS = {
    "get_profit_summary": tool_get_profit_summary,
    "get_profit_by_product": tool_get_profit_by_product,
    "get_return_loss_by_product": tool_get_return_loss_by_product,
    "simulate_return_reduction": tool_simulate_return_reduction,
    "save_action_item": tool_save_action_item,
}


def _tool(name, description, properties=None, required=None):
    return {"type": "function", "function": {
        "name": name, "description": description,
        "parameters": {"type": "object", "properties": properties or {}, "required": required or []}}}


TOOLS = [
    _tool("get_profit_summary", "Overall sales, return loss, net profit and margin of the business."),
    _tool("get_profit_by_product", "Orders, sales, net profit and margin for each product."),
    _tool("get_return_loss_by_product",
          "Return loss for each product, split into RTO loss, return charges and damaged-product loss."),
    _tool("simulate_return_reduction",
          "Estimate the money saved if the return loss of one product falls by a given percent.",
          {"product_name": {"type": "string", "description": "Exact product name"},
           "reduction_pct": {"type": "number", "description": "Percent reduction, for example 30"}},
          ["product_name", "reduction_pct"]),
    _tool("save_action_item", "Save one to-do item for the seller, with the expected saving in rupees.",
          {"title": {"type": "string", "description": "Short action, for example 'Add bubble wrap for A4 frames'"},
           "expected_saving": {"type": "number", "description": "Expected saving in rupees"}},
          ["title"]),
]


def run_tool(name, arguments):
    """Run one tool by name. Errors go back to the model as text instead of crashing the agent."""
    try:
        function = TOOL_FUNCTIONS[name]
        return function(**json.loads(arguments or "{}"))
    except Exception as e:
        logger.error(f"Tool {name} failed: {e}")
        return {"error": str(e)}


# ---------- The agent loop ----------

_USE_EFFORT = True


def _chat(client, messages, tools=None):
    """Call the model. A low reasoning effort makes gpt-oss answer much faster."""
    options = {"model": MODEL, "messages": messages}
    if tools:
        options["tools"] = tools
    global _USE_EFFORT
    if _USE_EFFORT:
        try:
            return client.chat.completions.create(reasoning_effort="low", **options).choices[0].message
        except Exception as e:                       # the option may be rejected: stop using it from now on
            logger.warning(f"Not using reasoning_effort any more: {e}")
            _USE_EFFORT = False
    return client.chat.completions.create(**options).choices[0].message


def run_agent(task="Analyze my business and tell me how to increase my profit."):
    """Run the agent. Returns the final report text and the list of tools it used."""
    try:
        setup_database()
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": task}]
        tools_used = []

        for step in range(MAX_STEPS):
            reply = _chat(client, messages, TOOLS)
            if not reply.tool_calls:                       # no more tools needed: this is the final report
                logger.info(f"Agent finished in {step + 1} steps, tools used: {tools_used}")
                return reply.content, tools_used
            messages.append(reply)
            for call in reply.tool_calls:                  # run every tool the model asked for
                tools_used.append(call.function.name)
                result = run_tool(call.function.name, call.function.arguments)
                messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)})

        # Step limit reached: ask for the final report without allowing more tools
        messages.append({"role": "user", "content": "Write the final report now, using only the numbers you already have."})
        final = _chat(client, messages)
        logger.info("Agent hit the step limit, final report was forced")
        return final.content, tools_used
    except Exception as e:
        raise CustomException(e, sys)


if __name__ == "__main__":
    report, used = run_agent()
    print("Tools used:", used)
    print()
    print(report)