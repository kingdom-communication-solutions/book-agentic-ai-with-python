"""Café Tools and One OpenAI Tool Interaction — generated from the learner notebook.
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


print("Previous sales:")
print(get_sales("2026-02-10", "P01"))

print("\nSelected-day sales:")
print(get_sales("2026-02-11", "P01"))

print("\nCampus events:")
print(get_events("2026-02-11"))

print("\nCoffee promotions:")
print(get_promotions("2026-02-11", "P01"))


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


messages = [
    {
        "role": "user",
        "content": (
            "Was a campus event recorded on 2026-02-11? "
            "Report its name and expected attendance. "
            "Explain what this information cannot establish "
            "about café sales."
        )
    }
]

if USE_OPENAI:
    response = client.responses.create(
        model=model,
        input=messages,
        tools=[events_tool],
        tool_choice={"type": "function", "name": "get_events"},
        max_output_tokens=300,
        store=False
    )
else:
    # A supplied stand-in for the model's request; not a live response.
    response = SimpleNamespace(output=[SimpleNamespace(
        type="function_call", name="get_events",
        arguments=json.dumps({"date": "2026-02-11"}),
        call_id="supplied-event-call"
    )])
    print("Supplied tool request: get_events(date='2026-02-11')")


# Retain the model's response, including its tool request.
messages += response.output

for item in response.output:
    if item.type == "function_call" and item.name == "get_events":
        arguments = json.loads(item.arguments)

        # Python performs the lookup.
        observation = get_events(arguments["date"])

        print("Requested tool:", item.name)
        print("Arguments:", arguments)
        print("Observation:", observation)

        # Associate this result with the model's specific request.
        messages.append({
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps(observation)
        })


if USE_OPENAI:
    # Second and final model request: no additional tools are offered.
    answer = client.responses.create(
        model=model,
        input=messages,
        max_output_tokens=300,
        store=False
    )
    print("LIVE MODEL ANSWER")
    print(answer.output_text)
    client.close()
else:
    print("SUPPLIED TEACHING ANSWER — NOT A MODEL OUTPUT")
    print("A Campus community gathering was recorded on 2026-02-11, with expected attendance of 200.")
    print("Expected attendance does not measure actual café customers or establish an effect on sales.")

