"""Building a Prompt Chain — IT Maintenance Notice — generated from the learner notebook.
Run from this folder or pass this script path from another directory.
"""
from pathlib import Path
import os
os.chdir(Path(__file__).resolve().parent)

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
Extract these facts from the maintenance note:
- Affected service
- Day and time
- Reason for the interruption
- Available alternative
- Support contact

Use a short labelled list.
If a detail is not provided, write "Not provided".
Do not invent information.
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


# Author-written offline fixtures. Registering them makes no API call.
supplied_facts = """
Affected service: Office Wi-Fi
Day and time: Tuesday, 09:00 to 10:00
Reason for the interruption: Technicians are replacing a router
Available alternative: Wired connections remain available
Support contact: IT service desk
"""

supplied_notice = """
Subject: Office Wi-Fi maintenance on Tuesday

Office Wi-Fi will be unavailable on Tuesday from 09:00 to 10:00 while technicians replace a router. Wired connections will remain available during this time. If you need help, please contact the IT service desk.
"""

bullet_notice_instructions = """
Write a short IT maintenance notice for employees
using only the supplied facts.

Include a subject line followed by three short bullet points.
Explain the interruption, available alternative
and support contact.

Do not add a sender name, department name or sign-off unless explicitly supplied.
Do not invent missing details.
Do not describe a detail marked "Not provided"
as if it were known.
"""

supplied_bullet_notice = """
Subject: Office Wi-Fi maintenance on Tuesday

- Office Wi-Fi will be unavailable on Tuesday from 09:00 to 10:00 for a router replacement.
- Wired connections will remain available.
- For help, contact the IT service desk.
"""

note_without_contact = """
Office Wi-Fi will be unavailable on Tuesday
from 09:00 to 10:00 while technicians replace a router.

Wired connections will remain available.
"""

supplied_missing_facts = """
Affected service: Office Wi-Fi
Day and time: Tuesday, 09:00 to 10:00
Reason for the interruption: Technicians are replacing a router
Available alternative: Wired connections remain available
Support contact: Not provided
"""

supplied_missing_notice = """
Subject: Office Wi-Fi maintenance on Tuesday

Office Wi-Fi will be unavailable on Tuesday from 09:00 to 10:00 while technicians replace a router. Wired connections will remain available. No support contact was provided in the supplied information.
"""

register_sample(extraction_instructions, maintenance_note, supplied_facts)
register_sample(notice_instructions, supplied_facts, supplied_notice)
register_sample(bullet_notice_instructions, supplied_facts, supplied_bullet_notice)
register_sample(extraction_instructions, note_without_contact, supplied_missing_facts)
register_sample(notice_instructions, supplied_missing_facts, supplied_missing_notice)


USE_OPENAI = False
RUN_FORMAT_CHANGE = False
RUN_MISSING_CONTACT = False

# No client or private configuration is loaded in offline mode.
if USE_OPENAI:
    if MODE != "live":
        configure_live()
else:
    if MODE == "live":
        clear_live()
    print("Offline mode: supplied teaching responses, no OpenAI requests.")


# Stage 1 sends the original note and stores its response.
facts = get_completion(extraction_instructions, maintenance_note)
print("INTERMEDIATE FACTS")
print(facts)


# Stage 2 explicitly receives the first response as its user input.
notice = get_completion(notice_instructions, facts)
print("EMPLOYEE NOTICE")
print(notice)


# Display just the baseline messages so the data flow is easy to trace.
for number, record in enumerate(request_records[:2], start=1):
    print(f"\nSTAGE {number} — {record['mode']}")
    print("INPUT:")
    print(record["user_prompt"])
    print("OUTPUT:")
    print(record["response"])


if RUN_FORMAT_CHANGE:
    # Reuse the saved baseline facts; only the writing instruction changes.
    bullet_notice = get_completion(bullet_notice_instructions, facts)
    print("REVISED PRESENTATION")
    print(bullet_notice)
else:
    print("Presentation task not run. Inspect the baseline first.")


if RUN_MISSING_CONTACT:
    # A changed source requires extraction again before writing.
    missing_facts = get_completion(extraction_instructions, note_without_contact)
    print("FACTS WITHOUT CONTACT")
    print(missing_facts)
    missing_notice = get_completion(notice_instructions, missing_facts)
    print("NOTICE WITHOUT CONTACT")
    print(missing_notice)
else:
    print("Missing-information task not run.")


# Close the client without making any request or erasing displayed outputs.
clear_live()

