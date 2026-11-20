"""Comparing Basic and Zero-Shot CoT Prompts — generated from the learner notebook.
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

# Optional: set True only in a standard Python kernel with your own .env.
USE_OPENAI = False
if USE_OPENAI:
    configure_live()
else:
    print("Supplied examples selected. No model will be called.")

problem = """
A café sold 35 sandwiches in the morning
and 52 in the afternoon.

How many sandwiches were sold in total?
"""

reasoning_instruction = (
    "Solve the problem step by step and give a short calculation."
)

# Basic prompt: contains only the problem
basic_prompt = problem

# Zero-shot CoT prompt: combines the problem and instruction
zero_shot_cot_prompt = (
    problem + "\n" + reasoning_instruction
)

# These are supplied teaching examples, not results of live calls.
# Exact prompt matching prevents edited questions receiving an unrelated answer.
system_prompt = "You are a helpful assistant."
register_sample(system_prompt, basic_prompt, "The café sold 87 sandwiches in total.")
register_sample(system_prompt, zero_shot_cot_prompt,
                "Morning: 35 sandwiches. Afternoon: 52 sandwiches.\n"
                "35 + 52 = 87. The café sold 87 sandwiches in total.")

system_prompt = "You are a helpful assistant."

basic_response = get_completion(
    system_prompt,
    basic_prompt
)

cot_response = get_completion(
    system_prompt,
    zero_shot_cot_prompt
)

print("BASIC RESPONSE")
print(basic_response)

print("\nZERO-SHOT COT RESPONSE")
print(cot_response)

problem = """
A café sold 24 coffees at €3 each
and 15 sandwiches at €5 each.

What was the total revenue?
"""

coffee_revenue = 24 * 3
sandwich_revenue = 15 * 5

expected_revenue = coffee_revenue + sandwich_revenue

print("Expected revenue:", expected_revenue)

# Rerun prompt construction whenever the problem changes.
basic_prompt = problem
zero_shot_cot_prompt = problem + "\n" + reasoning_instruction

# Supply examples for this exact revenue problem.
register_sample(system_prompt, basic_prompt, "The total revenue was €147.")
register_sample(system_prompt, zero_shot_cot_prompt,
                "24 × €3 = €72; 15 × €5 = €75.\n"
                "€72 + €75 = €147 total revenue.")

system_prompt = "You are a helpful assistant."

basic_response = get_completion(
    system_prompt,
    basic_prompt
)

cot_response = get_completion(
    system_prompt,
    zero_shot_cot_prompt
)

print("BASIC RESPONSE")
print(basic_response)

print("\nZERO-SHOT COT RESPONSE")
print(cot_response)

reasoning_instruction = """
Calculate the revenue for each product.
Then calculate the total revenue.
Present the calculations and a short final answer in euros.
"""

# Rebuild the prompt so the revised instruction is actually sent.
zero_shot_cot_prompt = problem + "\n" + reasoning_instruction
register_sample(system_prompt, zero_shot_cot_prompt,
                "Coffee revenue: 24 × €3 = €72.\n"
                "Sandwich revenue: 15 × €5 = €75.\n"
                "Total revenue: €72 + €75 = €147.")
refined_response = get_completion(system_prompt, zero_shot_cot_prompt)
print("REFINED RESPONSE")
print(refined_response)

# Write your own problem, rebuild both prompts and calculate a reference.
# Use the same system prompt and model when comparing the two requests.

if USE_OPENAI:
    clear_live()
