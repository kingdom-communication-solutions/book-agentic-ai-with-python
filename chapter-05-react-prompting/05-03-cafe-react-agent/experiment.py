"""Building and Refining a Café ReAct Agent — generated from the learner notebook.
Run from this folder or pass this script path from another directory.
"""
from pathlib import Path
import os
os.chdir(Path(__file__).resolve().parent)

import pandas as pd

sales = pd.read_csv("sales.csv")
events = pd.read_csv("campus_events.csv")
promotions = pd.read_csv("promotions.csv")


def get_sales(date, product_id):
    # Match both the date and the product.
    rows = sales[
        (sales["date"] == date)
        & (sales["product_id"] == product_id)
    ]

    columns = ["date", "product_name", "quantity_sold"]
    return rows[columns].to_dict("records")


def get_events(date):
    # Retrieve events recorded on the requested date.
    rows = events[events["date"] == date]

    columns = ["date", "event_name", "expected_attendance"]
    return rows[columns].to_dict("records")


def get_promotions(date, product_id):
    # Exclude promotions for other products.
    rows = promotions[
        (promotions["date"] == date)
        & (promotions["product_id"] == product_id)
    ]

    columns = ["date", "product_id", "discount_percent"]
    return rows[columns].to_dict("records")


events_tool = {
    "type": "function",
    "name": "get_events",
    "description": (
        "Retrieve recorded campus events for a date. "
        "Attendance figures are expected attendance, "
        "not actual café visits."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": "Date in YYYY-MM-DD format."
            }
        },
        "required": ["date"],
        "additionalProperties": False
    }
}


import json
import os
from pathlib import Path
from types import SimpleNamespace

# Offline is the default. Set True only when ready for two real API requests.
USE_OPENAI = False
client = None
model = "supplied-example"

if USE_OPENAI:
    import sys
    if sys.platform in {"emscripten", "wasi"}:
        raise RuntimeError("Use offline mode in browser Python; live calls need a local Python kernel.")
    from dotenv import load_dotenv
    from openai import OpenAI

    # Section 2.3 setup extended only to locate the downloaded package root.
    config_folder = Path.cwd()
    for folder in [config_folder, *config_folder.parents]:
        if (folder / "COMPANION_VERSION").is_file():
            config_folder = folder
            break
    load_dotenv(config_folder / ".env")
    model = os.environ["OPENAI_MODEL"]
    client = OpenAI(timeout=45.0, max_retries=0)
    print("Live mode configured. Running the next request cell uses OpenAI.")
else:
    print("Offline mode: supplied messages, real Python CSV lookups, no API requests.")


# Offline infrastructure only: supplied requests are not model decisions.
# This stand-in exposes the same response fields used by the book loop.
def make_supplied_client():
    state = {"step": 0}
    actions = [
        ("get_sales", {"date": "2026-02-10", "product_id": "P01"}),
        ("get_sales", {"date": "2026-02-11", "product_id": "P01"}),
        ("get_events", {"date": "2026-02-11"}),
        ("get_promotions", {"date": "2026-02-11", "product_id": "P01"})
    ]

    def create(**request):
        index = state["step"]
        state["step"] += 1
        if index < len(actions):
            name, arguments = actions[index]
            call = SimpleNamespace(
                type="function_call", name=name,
                arguments=json.dumps(arguments), call_id=f"supplied-{index}"
            )
            return SimpleNamespace(output=[call], output_text="")
        # This is author-written teaching text, not a live model response.
        report = (
            "SUPPLIED REPORT: coffee sales increased by 71 units. A campus gathering "
            "and a coffee promotion were recorded on 11 February. These records "
            "do not establish the cause of the increase."
        )
        if "state the sales quantity" in request["instructions"]:
            report = (
                "SUPPLIED REVISED REPORT: 10 February: 35 coffees; 11 February: 106. "
                "Change: 106 - 35 = 71 coffees. A campus gathering (expected attendance "
                "200) and a 20% coffee discount were recorded. This does not prove causation."
            )
        return SimpleNamespace(output=[], output_text=report)

    return SimpleNamespace(responses=SimpleNamespace(create=create), close=lambda: None)


product_parameters = {
    "type": "object",
    "properties": {
        "date": {
            "type": "string",
            "description": "Date in YYYY-MM-DD format."
        },
        "product_id": {
            "type": "string",
            "description": "Product identifier; Coffee is P01."
        }
    },
    "required": ["date", "product_id"],
    "additionalProperties": False
}


sales_tool = {
    "type": "function",
    "name": "get_sales",
    "description": (
        "Retrieve recorded sales quantity for a product and date. "
        "An empty result means the sales record is unavailable."
    ),
    "parameters": product_parameters
}

promotions_tool = {
    "type": "function",
    "name": "get_promotions",
    "description": (
        "Retrieve recorded promotions for a product and date. "
        "An empty result means no matching promotion was recorded."
    ),
    "parameters": product_parameters
}

tools = [sales_tool, events_tool, promotions_tool]


system_prompt = """
You are a café data analyst.

Use the available tools to investigate the user's question.
Use only information supported by the returned records.
Coffee has product identifier P01.

Compare sales on the requested dates and inspect relevant
event and promotion records before preparing your answer.

If a required record is unavailable, explain what is missing.
Distinguish observed changes from possible explanations.
Keep the final report concise.
"""

question = """
How did coffee sales change between 2026-02-10 and 2026-02-11,
and what recorded events or promotions might be relevant?
"""


max_steps = 8
# Each investigation creates its own message list inside run_investigation().

def run_investigation(client, model, instructions, question, max_steps=8):
    system_prompt = instructions
    messages = [{"role": "user", "content": question}]
    for step in range(max_steps):
        response = client.responses.create(
            model=model,
            instructions=system_prompt,
            input=messages,
            tools=tools,
            parallel_tool_calls=False,
            max_output_tokens=500,
            store=False
        )
    
        # Retain the complete response for the next request.
        messages += response.output
    
        # Select function requests from the response.
        tool_calls = [
            item for item in response.output
            if item.type == "function_call"
        ]
    
        # No tool request: display the model's answer and stop.
        if not tool_calls:
            if response.output_text.strip():
                print("\nFINAL ANSWER")
                print(response.output_text)
            else:
                print("No answer returned. The investigation is unfinished.")
            break
    
        # This example allows one tool request per model turn.
        tool_call = tool_calls[0]
        arguments = json.loads(tool_call.arguments)
    
        print(f"\nStep {step + 1}")
        print("Requested tool:", tool_call.name)
        print("Arguments:", arguments)
    
        # Execute only the functions explicitly available here.
        if tool_call.name == "get_sales":
            observation = get_sales(
                arguments["date"],
                arguments["product_id"]
            )
    
        elif tool_call.name == "get_events":
            observation = get_events(arguments["date"])
    
        elif tool_call.name == "get_promotions":
            observation = get_promotions(
                arguments["date"],
                arguments["product_id"]
            )
    
        else:
            observation = {"error": "Unknown tool."}
    
        print("Observation:", observation)
    
        # Return the result with its corresponding request identifier.
        messages.append({
            "type": "function_call_output",
            "call_id": tool_call.call_id,
            "output": json.dumps(observation)
        })
    
    else:
        print("\nStep limit reached. The investigation is unfinished.")
    return messages


if not USE_OPENAI:
    print("SUPPLIED SEQUENCE — no API calls; CSV functions execute normally.")
    client = make_supplied_client()

try:
    baseline_messages = run_investigation(client, model, system_prompt, question, max_steps)
finally:
    client.close()


previous = get_sales("2026-02-10", "P01")
current = get_sales("2026-02-11", "P01")

if previous and current:
    expected_change = (
        current[0]["quantity_sold"]
        - previous[0]["quantity_sold"]
    )
    print("Checked change in coffees sold:", expected_change)
else:
    print("Cannot calculate the change: a record is unavailable.")


additional_instruction = """
In the final report, state the sales quantity for each date
and show the subtraction used to calculate the change.
"""

revised_system_prompt = (
    system_prompt + "\n" + additional_instruction
)


RUN_REFINEMENT = False

if RUN_REFINEMENT:
    if USE_OPENAI:
        client = OpenAI(timeout=45.0, max_retries=0)
    else:
        client = make_supplied_client()
    try:
        revised_messages = run_investigation(
            client, model, revised_system_prompt, question, max_steps
        )
    finally:
        client.close()
else:
    print("Refinement not run. Inspect the baseline, then choose whether to enable it.")

