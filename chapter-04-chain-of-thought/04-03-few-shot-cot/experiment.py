"""Comparing Zero-Shot and Few-Shot CoT Prompts — generated from the learner notebook.
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
The café has 45 cups and uses 8.
How many cups remain?
"""

reasoning_instruction = (
    "Give a short step-by-step calculation "
    "and a final answer."
)

worked_examples = """
Example 1
Problem: The café has 20 cups and uses 4.
How many cups remain?

Solution:
Start with 20 cups.
Subtract the 4 cups used: 20 - 4 = 16.
Answer: 16 cups remain.

Example 2
Problem: The café has 30 cups and uses 5.
How many cups remain?

Solution:
Start with 30 cups.
Subtract the 5 cups used: 30 - 5 = 25.
Answer: 25 cups remain.
"""

# Zero-shot CoT: problem and instruction, without examples.
zero_shot_prompt = (
    problem + "\n" + reasoning_instruction
)

# Few-shot CoT: worked examples followed by the same new problem.
few_shot_prompt = (
    worked_examples
    + "\nNew problem:\n"
    + problem
    + "\n"
    + reasoning_instruction
)

# Supplied teaching examples only; live mode ignores these stored responses.
system_prompt = "You are a helpful assistant."
register_sample(system_prompt, zero_shot_prompt,
                "45 - 8 = 37. There are 37 cups remaining.")
register_sample(system_prompt, few_shot_prompt,
                "Start with 45 cups.\nSubtract the 8 cups used: 45 - 8 = 37.\n"
                "Answer: 37 cups remain.")

system_prompt = "You are a helpful assistant."

zero_shot_response = get_completion(
    system_prompt,
    zero_shot_prompt
)

few_shot_response = get_completion(
    system_prompt,
    few_shot_prompt
)

print("ZERO-SHOT COT RESPONSE")
print(zero_shot_response)

print("\nFEW-SHOT COT RESPONSE")
print(few_shot_response)

expected_cups = 45 - 8

print("Expected cups remaining:", expected_cups)

problem = """
The café has 64 cups and uses 19.
How many cups remain?
"""

expected_cups = 64 - 19

print("Expected cups remaining:", expected_cups)

# Zero-shot CoT: problem and instruction, without examples.
zero_shot_prompt = (
    problem + "\n" + reasoning_instruction
)

# Few-shot CoT: worked examples followed by the same new problem.
few_shot_prompt = (
    worked_examples
    + "\nNew problem:\n"
    + problem
    + "\n"
    + reasoning_instruction
)

# Supplied examples for the changed problem; no model output is invented here.
register_sample(system_prompt, zero_shot_prompt,
                "64 - 19 = 45. There are 45 cups remaining.")
register_sample(system_prompt, few_shot_prompt,
                "Start with 64 cups.\nSubtract the 19 cups used: 64 - 19 = 45.\n"
                "Answer: 45 cups remain.")

system_prompt = "You are a helpful assistant."

zero_shot_response = get_completion(
    system_prompt,
    zero_shot_prompt
)

few_shot_response = get_completion(
    system_prompt,
    few_shot_prompt
)

print("ZERO-SHOT COT RESPONSE")
print(zero_shot_response)

print("\nFEW-SHOT COT RESPONSE")
print(few_shot_response)

# Write two worked revenue examples and the unanswered new task.
# Build the prompt, call get_completion() in live mode and check with Python.

if USE_OPENAI:
    clear_live()
