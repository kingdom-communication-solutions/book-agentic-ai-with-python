"""Structured Outputs and Gate Checks — IT Notice Chain — generated from the learner notebook.
Run from this folder or pass this script path from another directory.
"""
from pathlib import Path
import os
os.chdir(Path(__file__).resolve().parent)

from pydantic import BaseModel, ValidationError


maintenance_note = """
Office Wi-Fi will be unavailable on Tuesday
from 09:00 to 10:00 while technicians replace a router.

Wired connections will remain available.
Employees who need help should contact the IT service desk.
"""


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


extraction_instructions = """
Extract the maintenance facts.

Return only a JSON object with these fields:
affected_service, day_and_time, reason,
alternative, support_contact.

Every value must be a string.
If a detail is missing, use "Not provided".
Return plain JSON only, beginning with { and ending with }.
Do not use Markdown or code fences.
Do not add information or explanatory text.
"""


notice_instructions = """
Write a short IT maintenance notice for employees
using only the supplied facts.

Include a subject line and a clear, friendly message.
Explain the interruption, available alternative
and support contact.

Do not add a sender name, department name or sign-off unless explicitly supplied.
Do not invent missing details.
Do not describe a detail marked "Not provided"
as if it were known.
"""


from pydantic import BaseModel, ValidationError


class MaintenanceFacts(BaseModel):
    affected_service: str
    day_and_time: str
    reason: str
    alternative: str
    support_contact: str


# Register a fixed JSON extraction and its supplied notice.
supplied_json = '{\n  "affected_service": "Office Wi-Fi",\n  "day_and_time": "Tuesday, 09:00 to 10:00",\n  "reason": "Router replacement",\n  "alternative": "Wired connections remain available",\n  "support_contact": "IT service desk"\n}'
supplied_notice = "Subject: Office Wi-Fi maintenance on Tuesday\n\nOffice Wi-Fi will be unavailable on Tuesday from 09:00 to 10:00 while technicians replace a router. Wired connections remain available. For help, contact the IT service desk."
register_sample(extraction_instructions, maintenance_note, supplied_json)
register_sample(notice_instructions,
                MaintenanceFacts.model_validate_json(supplied_json).model_dump_json(indent=2),
                supplied_notice)


USE_OPENAI = False
if USE_OPENAI:
    configure_live()
else:
    print("Offline: supplied responses and actual Python gate checks.")


facts_text = get_completion(extraction_instructions, maintenance_note)
print("RAW EXTRACTION")
print(facts_text)


try:
    facts = MaintenanceFacts.model_validate_json(facts_text)

except ValidationError as error:
    print("The extracted facts failed the check.")
    print(error)
    print("Stage 2 was not called.")

else:
    notice = get_completion(
        notice_instructions,
        facts.model_dump_json(indent=2)
    )

    print("EMPLOYEE NOTICE")
    print(notice)


# Change one feature at a time; keep these teaching tests separate from live output.
import json
baseline = json.loads(supplied_json)
missing = dict(baseline)
del missing["support_contact"]
wrong_type = dict(baseline, alternative=["Wired connections"])
wrong_time = dict(baseline, day_and_time="Tuesday, 11:00 to 12:00")
empty_value = dict(baseline, alternative="")
unknown_contact = dict(baseline, support_contact="Not provided")
cases = {
    "Valid record": supplied_json,
    "Missing field": json.dumps(missing),
    "Wrong type": json.dumps(wrong_type),
    "Incorrect time": json.dumps(wrong_time),
    "Empty string": json.dumps(empty_value),
    "Explicitly unavailable": json.dumps(unknown_contact),
    "Malformed JSON": "{broken",
    "Markdown fences": "```json\n" + supplied_json + "\n```"
}
for label, candidate in cases.items():
    try:
        MaintenanceFacts.model_validate_json(candidate)
    except ValidationError:
        print(label + ": rejected — Stage 2 would stop")
    else:
        print(label + ": structure accepted — facts still need checking")


# Release the optional live client without making another request.
clear_live()

