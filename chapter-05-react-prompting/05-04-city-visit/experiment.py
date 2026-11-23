"""Project — Plan a One-Day City Visit — generated from the learner notebook.
Run from this folder or pass this script path from another directory.
"""
from pathlib import Path
import os
os.chdir(Path(__file__).resolve().parent)

question = 'I have one day to explore the city on 2026-06-15, from 10:00 to 17:00.\nI enjoy history and art, and I would like to visit three attractions.\nMy admission budget is €40. I will walk between locations.\nPlease check opening hours and the weather before suggesting a plan.\nThe budget covers admission only. Start at the first attraction and\nfinish at the last; no journeys from a hotel need to be planned.'


import json
import os
from pathlib import Path
from types import SimpleNamespace
import pandas as pd
from IPython.display import display

# Keep the four CSV files beside this notebook.
attractions = pd.read_csv("attractions.csv", keep_default_na=False)
opening_hours = pd.read_csv("opening_hours.csv", keep_default_na=False)
weather = pd.read_csv("weather.csv", keep_default_na=False)
travel_times = pd.read_csv("travel_times.csv", keep_default_na=False)
for name, frame in [("Attractions", attractions), ("Opening hours", opening_hours),
                    ("Weather", weather), ("Walking times", travel_times)]:
    print(name)
    display(frame.head(6))


def get_attractions():
    # Return the small catalogue so the model can compare interests and prices.
    return attractions.to_dict(orient="records")


def get_opening_hours(attraction_id, date):
    rows = opening_hours[
        (opening_hours["attraction_id"] == attraction_id)
        & (opening_hours["date"] == date)
    ]
    return rows.to_dict(orient="records")


def get_weather(date):
    return weather[weather["date"] == date].to_dict(orient="records")


def get_travel_time(origin_id, destination_id):
    rows = travel_times[
        (travel_times["origin_id"] == origin_id)
        & (travel_times["destination_id"] == destination_id)
    ]
    return rows.to_dict(orient="records")


print("Known hours:", get_opening_hours("A01", "2026-06-15"))
print("Unavailable date:", get_opening_hours("A01", "2099-01-01"))
print("Closed attraction:", get_opening_hours("A06", "2026-06-15"))


# Describe what each function retrieves. These descriptions do not execute it.
tool_descriptions = {
    "get_attractions": "TODO: Explain get_attractions and missing records.",
    "get_opening_hours": "TODO: Explain get_opening_hours and missing records.",
    "get_weather": "TODO: Explain get_weather and missing records.",
    "get_travel_time": "TODO: Explain get_travel_time and missing records."
}

# Tool parameters use the same JSON-schema structure as Section 5.2.
text_parameter = {"type": "string"}
tools = []
for name, parameters in [
    ("get_attractions", {}),
    ("get_opening_hours", {"attraction_id": text_parameter, "date": text_parameter}),
    ("get_weather", {"date": text_parameter}),
    ("get_travel_time", {"origin_id": text_parameter, "destination_id": text_parameter})
]:
    tools.append({
        "type": "function", "name": name,
        "description": tool_descriptions[name],
        "parameters": {
            "type": "object", "properties": parameters,
            "required": list(parameters), "additionalProperties": False
        }
    })


system_prompt = 'TODO: Write your city-visit planning assistant instructions here.'


# Fixed author-written teaching sequence: this is not model reasoning.
def make_supplied_client():
    actions = [
        ("get_attractions", {}),
        ("get_weather", {"date": "2026-06-15"}),
        ("get_opening_hours", {"attraction_id": "A01", "date": "2026-06-15"}),
        ("get_opening_hours", {"attraction_id": "A02", "date": "2026-06-15"}),
        ("get_opening_hours", {"attraction_id": "A03", "date": "2026-06-15"}),
        ("get_travel_time", {"origin_id": "A01", "destination_id": "A02"}),
        ("get_travel_time", {"origin_id": "A02", "destination_id": "A03"})
    ]
    state = {"step": 0}
    def create(**request):
        i = state["step"]
        state["step"] += 1
        if i < len(actions):
            name, arguments = actions[i]
            call = SimpleNamespace(type="function_call", name=name,
                arguments=json.dumps(arguments), call_id=f"supplied-{i}")
            return SimpleNamespace(output=[call], output_text="")
        return SimpleNamespace(output=[], output_text=(
            "SUPPLIED ITINERARY — not a live model response\n"
            "10:00–11:30 City History Museum (€12).\n"
            "11:30–11:50 Walk to Riverside Art Gallery (20 minutes).\n"
            "11:50–13:20 Riverside Art Gallery (€15).\n"
            "13:20–13:35 Walk to Heritage House (15 minutes).\n"
            "13:35–14:35 Heritage House (€8). Total admission: €35.\n"
            "Three indoor visits suit history/art interests and the recorded rain. "
            "Walking is outdoors. The forecast is a teaching record, not a guarantee. "
            "The plan finishes at 14:35; the remaining time is unallocated. "
            "Food, queues and journeys to/from the first/last stop are not included."
        ))
    return SimpleNamespace(responses=SimpleNamespace(create=create), close=lambda: None)


# Leave both switches False for a normal offline run.
USE_OPENAI = False
RUN_REFINEMENT = False
MAX_STEPS = 12


def create_client():
    if not USE_OPENAI:
        return make_supplied_client(), "supplied-example"

    # Live mode follows Sections 2.3 and 5.3; it requires local Python.
    import sys
    if sys.platform in {"emscripten", "wasi"}:
        raise RuntimeError("Keep offline mode in browser Python.")
    from dotenv import load_dotenv
    from openai import OpenAI

    config_folder = Path.cwd()
    for folder in [config_folder, *config_folder.parents]:
        if (folder / "COMPANION_VERSION").is_file():
            config_folder = folder
            break
    load_dotenv(config_folder / ".env")
    if not os.getenv("OPENAI_API_KEY") or not os.getenv("OPENAI_MODEL"):
        raise RuntimeError("Set OPENAI_API_KEY and OPENAI_MODEL in package-root .env.")
    if "TODO" in system_prompt or any("TODO" in d for d in tool_descriptions.values()):
        raise ValueError("Complete the prompt and tool descriptions before live execution.")
    return OpenAI(timeout=45.0, max_retries=0), os.environ["OPENAI_MODEL"]


def run_investigation(client, model, instructions, question, max_steps=12):
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
        if tool_call.name == "get_attractions":
            observation = get_attractions()
        elif tool_call.name == "get_opening_hours":
            observation = get_opening_hours(arguments["attraction_id"], arguments["date"])
        elif tool_call.name == "get_weather":
            observation = get_weather(arguments["date"])
        elif tool_call.name == "get_travel_time":
            observation = get_travel_time(arguments["origin_id"], arguments["destination_id"])
        else:
            observation = {"error": "Unknown tool."}

        print("Observation:")
        print(json.dumps(observation, indent=2, ensure_ascii=False))
    
        # Return the result with its corresponding request identifier.
        messages.append({
            "type": "function_call_output",
            "call_id": tool_call.call_id,
            "output": json.dumps(observation)
        })
    
    else:
        print("\nStep limit reached. The investigation is unfinished.")
    return messages


# One baseline run. Each iteration may request one lookup or a final answer.
client, model = create_client()
try:
    print("LIVE RUN" if USE_OPENAI else "OFFLINE: fixed supplied interaction")
    baseline_messages = run_investigation(
        client, model, system_prompt, question, MAX_STEPS
    )
finally:
    client.close()


# Read the prices directly from the CSV, independently of the model's arithmetic.
# For a different itinerary, change the identifiers to the chosen attractions.
selected_ids = ["A01", "A02", "A03"]
selected = attractions[attractions["attraction_id"].isin(selected_ids)]
if len(selected) == 3:
    total_admission = selected["admission_eur"].sum()
    print(f"Admission: €{total_admission:.2f}; within €40: {total_admission <= 40}")
else:
    print("A selected attraction is missing; check the identifiers.")


print("Unknown journey:", get_travel_time("A01", "A99"))
print("Unavailable weather:", get_weather("2099-01-01"))


# Set the switch in the configuration cell only after inspecting the baseline.
# Replace this example with an instruction addressing your observed weakness.
additional_instruction = "Show each walking journey as a separate entry with departure, arrival and recorded duration."
if RUN_REFINEMENT:
    client, model = create_client()
    try:
        revised_messages = run_investigation(
            client, model, system_prompt + "\n" + additional_instruction,
            question, MAX_STEPS
        )
    finally:
        client.close()
else:
    print("No second investigation: inspect the baseline before revising.")

