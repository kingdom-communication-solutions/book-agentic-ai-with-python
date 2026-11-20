"""Campus Café Detective — Analysing Sales with CoT — generated from the learner notebook.
Run from this folder or pass this script path from another directory.
"""
from pathlib import Path
import os
os.chdir(Path(__file__).resolve().parent)

# Shared offline/live request adapter. No API key is stored in this notebook.
# Code origin: get_completion(system_prompt, user_prompt) was introduced in Section 2.3.
# Notebook extension used from Section 3.2: supplied/live mode and interaction records.
# Evaluation notebooks reuse this helper without changing its two-argument interface.
import json
import os
import sys

MODE = "offline"
MODEL = ""
_client = None
request_records = []
OFFLINE_SAMPLES = {}

# Match supplied examples only when both messages are unchanged.
def _request_key(system_prompt, user_prompt):
    return json.dumps([system_prompt.strip(), user_prompt.strip()], ensure_ascii=False)

# Register a supplied teaching response; this does not contact OpenAI.
def register_sample(system_prompt, user_prompt, response):
    OFFLINE_SAMPLES[_request_key(system_prompt, user_prompt)] = response

# Locate one package-root configuration, while retaining standalone notebook use.
def _configuration_file():
    from pathlib import Path
    bases = [Path.cwd()]
    if "__file__" in globals():
        bases.insert(0, Path(__file__).resolve().parent)
    for base in bases:
        for folder in [base, *base.parents]:
            if (folder / "COMPANION_VERSION").is_file():
                return folder / ".env"
    # Standalone notebooks keep their configuration beside the notebook.
    return bases[0] / ".env"

# Load the private configuration and prepare an OpenAI client when live mode is chosen.
def configure_live(model=""):
    global MODE, MODEL, _client
    if sys.platform in {"emscripten", "wasi"}:
        raise RuntimeError("The OpenAI SDK needs a standard Python kernel. Keep offline mode in browser Python.")
    try:
        from openai import OpenAI
        from dotenv import load_dotenv
    except ImportError:
        raise RuntimeError("Install openai and python-dotenv in your Python kernel, then rerun setup.") from None
    # Read the key and model from the local file without printing the key.
    load_dotenv(_configuration_file())
    selected_model = model.strip() or os.getenv("OPENAI_MODEL", "").strip()
    if not selected_model or selected_model.startswith("YOUR_"):
        raise ValueError("Set OPENAI_MODEL in your .env file before choosing live mode.")
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key or key.startswith("YOUR_"):
        raise ValueError("Copy your own OpenAI key into the .env file before choosing live mode.")
    _client = OpenAI(timeout=45.0, max_retries=0)
    MODEL = selected_model
    MODE = "live"
    print("OpenAI configured from .env. No key is printed.")


def get_completion(system_prompt, user_prompt):
    if MODE == "live":
        if _client is None:
            raise RuntimeError("Run configure_live(MODEL) in a private Python kernel first.")
        try:
            # Send role instructions separately from the user task and data.
            response = _client.responses.create(model=MODEL, instructions=system_prompt, input=user_prompt, max_output_tokens=1000, store=False)
        except Exception:
            raise RuntimeError("API request failed. Check your model, account access and connection; no key has been printed.") from None
        text = response.output_text
        print("[Live OpenAI response]")
    else:
        # Offline mode returns stored text, not a newly generated model answer.
        text = OFFLINE_SAMPLES.get(_request_key(system_prompt, user_prompt))
        if text is None:
            print("[No saved response for these edited instructions]")
            return "No model was called. Use OpenAI mode in a standard Python kernel, or label a response you write yourself."
        print("[Supplied teaching response — no API call]")
    # Keep messages and responses for evaluation; never record the API key.
    request_records.append({"mode": MODE, "model": MODEL if MODE == "live" else "supplied-example", "system_prompt": system_prompt, "user_prompt": user_prompt, "response": text})
    return text

# Release the API client after finishing the experiment.
def clear_live():
    global _client, MODE
    if _client is not None:
        _client.close()
    _client = None
    MODE = "offline"
    print("Live client cleared from this kernel.")


# Leave this False to run the complete guided example without API requests.
USE_OPENAI = False
if USE_OPENAI:
    configure_live()
else:
    print("Offline mode: Python runs normally; model responses are supplied examples.")


import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Read files from the notebook's folder. No network or external API is used.
sales = pd.read_csv("sales.csv", parse_dates=["date"])
weather = pd.read_csv("weather.csv", parse_dates=["date"])
calendar = pd.read_csv("academic_calendar.csv", parse_dates=["date"])
events = pd.read_csv("campus_events.csv", parse_dates=["date"])
promotions = pd.read_csv("promotions.csv", parse_dates=["date"])

tables = {"Sales": sales, "Weather": weather, "Calendar": calendar,
          "Events": events, "Promotions": promotions}
for name, table in tables.items():
    print(f"\n{name} — {len(table)} rows")
    print(table.head(3).to_string(index=False))
print("\nDate range:", sales["date"].min().date(), "to", sales["date"].max().date())


# Attach context without adding or removing sales rows.
combined = sales.merge(weather, on="date", validate="many_to_one")
combined = combined.merge(calendar, on="date", validate="many_to_one")
combined = combined.merge(
    events[["date", "event_name", "expected_attendance"]],
    on="date", how="left", validate="many_to_one"
)
combined = combined.merge(
    promotions[["date", "product_id", "discount_percent"]],
    on=["date", "product_id"], how="left", validate="one_to_one"
)

# In these generated files, no matching record means no recorded event/promotion.
combined["event_name"] = combined["event_name"].fillna("No recorded event")
combined["expected_attendance"] = combined["expected_attendance"].fillna(0)
combined["discount_percent"] = combined["discount_percent"].fillna(0)
print("Sales rows before and after joining:", len(sales), len(combined))
print("Revenue unchanged:", round(sales["revenue"].sum(), 2) ==
      round(combined["revenue"].sum(), 2))


# Select one product; each remaining row represents one day.
coffee = combined[combined["product_name"] == "Coffee"].copy()
summary = coffee.groupby("is_lecture_day")["quantity_sold"].agg(
    days="count", total_units="sum", mean_daily_units="mean"
).round(2)
summary.index = ["Lecture day" if value else "Other day" for value in summary.index]
print(summary.to_string())

lecture_mean = summary.loc["Lecture day", "mean_daily_units"]
other_mean = summary.loc["Other day", "mean_daily_units"]
difference = round(lecture_mean - other_mean, 2)
print(f"\nDifference in the displayed daily means: {difference:.2f} coffees per day")


# Show both the overall comparison and variation across individual days.
fig, axes = plt.subplots(1, 2, figsize=(10, 3.5))
summary["mean_daily_units"].plot.bar(ax=axes[0], color=["#d69710", "#174283"])
axes[0].set(title="Coffee: mean daily sales", ylabel="Coffees per day")
axes[0].tick_params(axis="x", rotation=0)
coffee.plot(x="date", y="quantity_sold", ax=axes[1], legend=False, color="#174283")
axes[1].set(title="Coffee: daily variation", xlabel="Date", ylabel="Coffees sold")
fig.tight_layout()
plt.show()


columns = ["date", "quantity_sold", "is_lecture_day", "temperature_c",
           "event_name", "expected_attendance", "discount_percent"]
print(coffee[columns].head(6).to_string(index=False))

# Package only the calculated evidence needed for this question.
evidence = (
    "Synthetic café data, 5 January–4 April 2026. Product: Coffee.\n"
    + summary.to_string()
    + f"\nDifference of displayed means (lecture minus other): {difference:.2f}."
    + "\nThe calendar groups have different day counts. These are observational comparisons."
)
print("\nEvidence to include in the prompt:\n" + evidence)


system_prompt = "You are a café data analyst. Use only the supplied evidence."
question = "How do daily coffee sales differ between lecture days and other days?"
basic_instruction = "Answer the question briefly."
cot_instruction = "Give a short step-by-step comparison, followed by a conclusion."

# Keep the shared question and evidence visible, separate from each instruction.
basic_prompt = question + "\n" + evidence + "\n" + basic_instruction
cot_prompt = question + "\n" + evidence + "\n" + cot_instruction
print("BASIC PROMPT\n" + basic_prompt)
print("\nCOT PROMPT\n" + cot_prompt)


# Supplied responses illustrate a comparison; they are not generated by an LLM.
supplied_basic = (
    f"Coffee sales averaged {lecture_mean:.2f} on lecture days and "
    f"{other_mean:.2f} on other days. The difference was {difference:.2f} per day."
)
supplied_cot = (
    f"1. Compare mean daily sales, rather than totals across unequal day counts.\n"
    f"2. Lecture days: {lecture_mean:.2f}; other days: {other_mean:.2f} coffees per day.\n"
    f"3. Subtract the displayed means: {lecture_mean:.2f} - {other_mean:.2f} = {difference:.2f}.\n"
    "Conclusion: the lecture-day group had higher average daily coffee sales."
)
register_sample(system_prompt, basic_prompt, supplied_basic)
register_sample(system_prompt, cot_prompt, supplied_cot)

basic_response = get_completion(system_prompt, basic_prompt)
cot_response = get_completion(system_prompt, cot_prompt)
print("\nBASIC RESPONSE\n" + basic_response)
print("\nCOT RESPONSE\n" + cot_response)


revised_instruction = (
    cot_instruction
    + " Clearly separate the observed difference from causal claims, "
      "and state one limitation or additional comparison needed."
)
revised_prompt = question + "\n" + evidence + "\n" + revised_instruction
supplied_revised = (
    supplied_cot
    + "\nLimitation: these records show an association, not that lectures caused the difference. "
      "Weekday/weekend patterns, weather, promotions or events may overlap. "
      "Compare more similar days before proposing a cause."
)
register_sample(system_prompt, revised_prompt, supplied_revised)
revised_response = get_completion(system_prompt, revised_prompt)
print("\nREVISED RESPONSE\n" + revised_response)


lecture_values = coffee.loc[coffee["is_lecture_day"], "quantity_sold"]
other_values = coffee.loc[~coffee["is_lecture_day"], "quantity_sold"]
checked_lecture = round(lecture_values.sum() / len(lecture_values), 2)
checked_other = round(other_values.sum() / len(other_values), 2)
print(f"Lecture: {lecture_values.sum()} units / {len(lecture_values)} days = {checked_lecture:.2f}")
print(f"Other:   {other_values.sum()} units / {len(other_values)} days = {checked_other:.2f}")
print(f"Difference of displayed means: {checked_lecture - checked_other:.2f}")
print("\nNow check every numerical claim in the three responses against these figures.")


# Your independent analysis goes here.
# Start by writing your own question, then select relevant rows from combined.
# Add cells as needed; keep calculations and prompts separate.
independent_question = ""
print("Write your independent question and analysis before consulting the walkthrough.")


# Close an optional live client after all requested work is finished.
clear_live()

