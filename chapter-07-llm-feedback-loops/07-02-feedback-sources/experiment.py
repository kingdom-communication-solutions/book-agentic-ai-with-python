"""Generate and Check Feedback — generated from the learner notebook.
Run from this folder or pass this script path from another directory.
"""
from pathlib import Path
import os
os.chdir(Path(__file__).resolve().parent)

# These fictional facts are the reference; do not add a room number or link.
facts = 'Reading workshop: Saturday, 10:00, in the library.'
draft = 'Join our reading workshop this Saturday in the library.'
instructions = 'Revise the announcement using only the supplied facts.'


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

USE_OPENAI = False  # Keep False for browser/offline practice.
if USE_OPENAI:
    configure_live()  # Uses your private local .env; never put the key in a cell.
else:
    print("OFFLINE: supplied examples; not fresh model responses.")


human_feedback = 'The draft omits the starting time. Include 10:00.'
print("HUMAN FEEDBACK:", human_feedback)
# Optional, in an interactive session: human_feedback = input("Your feedback: ")
required_terms = ["reading workshop", "Saturday", "10:00", "library"]
missing_terms = [term for term in required_terms if term.lower() not in draft.lower()]
print("PYTHON CHECK — missing terms:", missing_terms)


review_instructions = 'Review the announcement against the supplied facts.\nCheck the workshop, day, time and location.\nIdentify omissions and unsupported claims.\nFor each problem, state the evidence and a specific correction.\nIf no problem is found, say so. Do not invent an issue.'
review_prompt = f"Facts: {facts}\nDraft: {draft}"
register_sample('Review the announcement against the supplied facts.\nCheck the workshop, day, time and location.\nIdentify omissions and unsupported claims.\nFor each problem, state the evidence and a specific correction.\nIf no problem is found, say so. Do not invent an issue.', 'Facts: Reading workshop: Saturday, 10:00, in the library.\nDraft: Join our reading workshop this Saturday in the library.', 'The draft omits the starting time. Include 10:00.')
feedback = get_completion(review_instructions, review_prompt)
print("MODEL REVIEW")
print(feedback)


revision_prompt = f"""
Task: Write a short announcement for library visitors.
Facts: {facts}
Current draft: {draft}
Feedback: {feedback}
Apply supported corrections only.
Return only the revised announcement.
"""
register_sample('Revise the announcement using only the supplied facts.', '\nTask: Write a short announcement for library visitors.\nFacts: Reading workshop: Saturday, 10:00, in the library.\nCurrent draft: Join our reading workshop this Saturday in the library.\nFeedback: The draft omits the starting time. Include 10:00.\nApply supported corrections only.\nReturn only the revised announcement.\n', 'Join our reading workshop this Saturday at 10:00 in the library.')
revision = get_completion(instructions, revision_prompt)
print(revision)


def check_announcement(text):
    # Narrow presence checks, not proof of correct meaning or complete factuality.
    required = ["reading workshop", "Saturday", "10:00", "library"]
    missing = [value for value in required if value.lower() not in text.lower()]
    return missing

for label, text in [("Before", draft), ("After", revision)]:
    missing = check_announcement(text)
    print(label + ":", text)
    print("Missing required terms:", missing or "none")


for index, record in enumerate(request_records, 1):
    print(f"Request {index} — {record['mode']}")
    print("INPUT:", record["user_prompt"])
    print("RESPONSE:", record["response"])
clear_live()

