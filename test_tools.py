"""Small test: can the Groq model call one of our Python functions as a tool?

Run:  uv run python test_tools.py
"""
import json
import os

from dotenv import load_dotenv
from groq import Groq

from calculations import profit_summary
from db import setup_database

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "openai/gpt-oss-20b"

tools = [{
    "type": "function",
    "function": {
        "name": "get_profit_summary",
        "description": "Get the overall sales, return loss and net profit of the business.",
        "parameters": {"type": "object", "properties": {}},
    },
}]

setup_database()
messages = [{"role": "user", "content": "What is my net profit? Use the tool to find out."}]

# Step 1: the model decides whether to call a tool
reply = client.chat.completions.create(model=MODEL, messages=messages, tools=tools).choices[0].message
print("Tool calls requested:", [c.function.name for c in (reply.tool_calls or [])])

if reply.tool_calls:
    messages.append(reply)
    # Step 2: we run the tool and give the result back
    for call in reply.tool_calls:
        result = profit_summary()
        messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)})
    # Step 3: the model writes the final answer
    final = client.chat.completions.create(model=MODEL, messages=messages, tools=tools).choices[0].message
    print("Final answer:", final.content)
else:
    print("Model did not call the tool. Answer:", reply.content)