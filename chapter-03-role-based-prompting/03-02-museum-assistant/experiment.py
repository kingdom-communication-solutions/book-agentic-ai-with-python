"""Construct the museum prompt — generated from the learner notebook.
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

from pathlib import Path

config_template = Path("openai.env.example")
if not config_template.exists():
    config_template.write_text("OPENAI_API_KEY=YOUR_OPENAI_API_KEY\nOPENAI_MODEL=YOUR_MODEL_NAME\n", encoding="utf-8")
print("Open openai.env.example, save a copy as .env, and replace the placeholders there.")


RUN_OPENAI_EXAMPLE = False
if RUN_OPENAI_EXAMPLE:
    import sys
    if sys.platform in {"emscripten", "wasi"}:
        raise RuntimeError("Run this OpenAI cell in a standard Python kernel; browser practice uses supplied responses.")
    import os
    from openai import OpenAI
    from dotenv import load_dotenv

    load_dotenv()
    client = OpenAI()
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL"),
        input="Explain what an AI agent is in a few sentences."
    )
    print(response.output_text)
    client.close()


MODE = "offline"  # Set to "live" in a standard Python kernel after editing .env.
MODEL = ""        # Leave empty to use OPENAI_MODEL from .env.
if MODE == "live":
    configure_live(MODEL)
else:
    print("Supplied examples: no OpenAI request. Set MODE to live to use your .env configuration.")


feedback_text = """F01: The exhibition labels were too small for me to read comfortably.
F02: I wanted clearer explanations next to the objects.
F03: The labels used specialist terms without explaining them.
F04: I waited a long time at the ticket desk.
F05: The queue at the entrance moved slowly.
F06: I could not find a seat when I needed a rest.
F07: More benches along the exhibition route would help.
F08: The staff were welcoming and helped me find the gallery."""


# Role: the perspective the model should adopt.
role = 'You are a museum visitor-feedback analyst.'

# Task: the work requested by the user.
task = 'Summarize this visitor feedback:'

# Context: the audience, objective and data boundary.
context = (
    "The audience is museum management deciding which visitor "
    "experiences to improve. Use only the supplied comments."
)

# Output expectations: the required response.
output_expectations = (
    "Summarize three recurring improvement themes in concise bullet points. "
    "Add one limitation."
)


system_prompt = f"{role}\n{context}\n{output_expectations}"
user_prompt = f"{task}\n{feedback_text}"


# Supplied teaching responses for the exact comparison prompts below.
# These are examples, not live model results.
register_sample('You are a helpful assistant.', 'Summarize this visitor feedback:\nF01: The exhibition labels were too small for me to read comfortably.\nF02: I wanted clearer explanations next to the objects.\nF03: The labels used specialist terms without explaining them.\nF04: I waited a long time at the ticket desk.\nF05: The queue at the entrance moved slowly.\nF06: I could not find a seat when I needed a rest.\nF07: More benches along the exhibition route would help.\nF08: The staff were welcoming and helped me find the gallery.', 'The comments mention exhibition labels, entrance waiting, seating and helpful staff.')
register_sample('You are a museum visitor-feedback analyst.', 'Summarize this visitor feedback:\nF01: The exhibition labels were too small for me to read comfortably.\nF02: I wanted clearer explanations next to the objects.\nF03: The labels used specialist terms without explaining them.\nF04: I waited a long time at the ticket desk.\nF05: The queue at the entrance moved slowly.\nF06: I could not find a seat when I needed a rest.\nF07: More benches along the exhibition route would help.\nF08: The staff were welcoming and helped me find the gallery.', 'Visitors report difficulties with labels, queues and seating. One comment praises the staff.')
register_sample('You are a museum visitor-feedback analyst.\nThe audience is museum management deciding which visitor experiences to improve. Use only the supplied comments.', 'Summarize this visitor feedback:\nF01: The exhibition labels were too small for me to read comfortably.\nF02: I wanted clearer explanations next to the objects.\nF03: The labels used specialist terms without explaining them.\nF04: I waited a long time at the ticket desk.\nF05: The queue at the entrance moved slowly.\nF06: I could not find a seat when I needed a rest.\nF07: More benches along the exhibition route would help.\nF08: The staff were welcoming and helped me find the gallery.', 'The recurring improvement areas are labels and explanations, entrance waiting and rest seating. These comments can guide management discussion but do not establish causes.')
register_sample('You are a museum visitor-feedback analyst.\nThe audience is museum management deciding which visitor experiences to improve. Use only the supplied comments.\nSummarize three recurring improvement themes in concise bullet points. Add one limitation.', 'Summarize this visitor feedback:\nF01: The exhibition labels were too small for me to read comfortably.\nF02: I wanted clearer explanations next to the objects.\nF03: The labels used specialist terms without explaining them.\nF04: I waited a long time at the ticket desk.\nF05: The queue at the entrance moved slowly.\nF06: I could not find a seat when I needed a rest.\nF07: More benches along the exhibition route would help.\nF08: The staff were welcoming and helped me find the gallery.', '- Labels and explanations: visitors wanted easier-to-read, clearer labels.\n- Entrance waiting: comments mention a slow queue and ticket desk.\n- Seating: comments ask for places to rest.\nLimitation: eight comments cannot establish the views of all visitors.')
register_sample('You are a museum visitor-feedback analyst.\nThe audience is museum management deciding which visitor experiences to improve. Use only the supplied comments.\nSummarize three recurring improvement themes in concise bullet points. Add one limitation.\nSupport each theme with the IDs of the relevant comments.', 'Summarize this visitor feedback:\nF01: The exhibition labels were too small for me to read comfortably.\nF02: I wanted clearer explanations next to the objects.\nF03: The labels used specialist terms without explaining them.\nF04: I waited a long time at the ticket desk.\nF05: The queue at the entrance moved slowly.\nF06: I could not find a seat when I needed a rest.\nF07: More benches along the exhibition route would help.\nF08: The staff were welcoming and helped me find the gallery.', '- Labels and explanations: F01, F02 and F03.\n- Entrance waiting: F04 and F05.\n- Rest seating: F06 and F07.\nF08 praises helpful staff.\nLimitation: these eight comments do not establish the views of all visitors.')
register_sample('You are a museum visitor-feedback analyst.\nThe audience is museum visitors seeking a brief overview. Use only the supplied comments.\nSummarize three recurring improvement themes in concise bullet points. Add one limitation.', 'Summarize this visitor feedback:\nF01: The exhibition labels were too small for me to read comfortably.\nF02: I wanted clearer explanations next to the objects.\nF03: The labels used specialist terms without explaining them.\nF04: I waited a long time at the ticket desk.\nF05: The queue at the entrance moved slowly.\nF06: I could not find a seat when I needed a rest.\nF07: More benches along the exhibition route would help.\nF08: The staff were welcoming and helped me find the gallery.', 'Visitors mentioned exhibition labels, entrance waiting and rest seating; one praised helpful staff. This is a small collection of comments, not a promise that the museum has changed its services.')


baseline_system_prompt = "You are a helpful assistant."
baseline_response = get_completion(baseline_system_prompt, user_prompt)
print(baseline_response)


role_system_prompt = role
role_response = get_completion(role_system_prompt, user_prompt)
print(role_response)


context_system_prompt = f"{role}\n{context}"
context_response = get_completion(context_system_prompt, user_prompt)
print(context_response)


constructed_system_prompt = system_prompt
constructed_response = get_completion(system_prompt, user_prompt)
print(constructed_response)


refined_system_prompt = constructed_system_prompt + "\nSupport each theme with the IDs of the relevant comments."
refined_response = get_completion(refined_system_prompt, user_prompt)
print(refined_response)
