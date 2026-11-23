"""Test and Revise a Python Function — generated from the learner notebook.
Run from this folder or pass this script path from another directory.
"""
from pathlib import Path
import os
os.chdir(Path(__file__).resolve().parent)

task = 'Write average_reading(values), returning the average of the readings.\nThe initial inputs are non-empty lists of finite numbers.\nReturn only the Python function, without Markdown fences.'
expanded_task = 'Write average_reading(values). Inputs contain finite numbers and None only.\nIgnore None values. Return None if no readings remain.\nOtherwise return the average, preserving valid negative temperatures.\nReturn only the Python function, without Markdown fences.'
code_instructions = "Write a simple, readable Python function."
initial_cases = [([18, 20, 22], 20.0)]
test_cases = [([18, 20, 22], 20.0), ([18, None, 22], 20.0), ([], None), ([None], None), ([-4, 0, 4], 0.0)]


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


from math import isclose
from time import perf_counter


def run_tests(function, cases):
    # Each case records its own result. Exceptions are failures, not missing tests.
    result = {"passed": 0, "failed": 0, "cases": []}
    for values, expected in cases:
        row = {"input": values, "expected": expected}
        try:
            actual = function(list(values))
            passed = (actual is None) if expected is None else (
                isinstance(actual, (int, float)) and not isinstance(actual, bool)
                and isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-9))
            row.update(actual=actual, passed=passed)
        except Exception as error:
            row.update(error=type(error).__name__ + ": " + str(error), passed=False)
        result["passed" if row["passed"] else "failed"] += 1
        result["cases"].append(row)
    return result


def format_feedback(result):
    lines = [f"Tests: {result['passed']} passed; {result['failed']} failed."]
    for row in result["cases"]:
        if not row["passed"]:
            actual = row.get("error", repr(row.get("actual")))
            lines.append(f"Input: {row['input']} | Expected: {row['expected']} | Actual/error: {actual}")
    return "\n".join(lines)


def make_revision_prompt(current_code, feedback):
    return f"""
Requirements: {expanded_task}
Current code:
{current_code}
Test feedback:
{feedback}
Fix the reported problems while preserving the other requirements.
Return only the revised function, without Markdown fences.
"""


initial_code = 'def average_reading(values):\n    return sum(values) / len(values)'
partial_code = 'def average_reading(values):\n    valid = [value for value in values if value is not None]\n    return sum(valid) / len(valid)'
complete_code = 'def average_reading(values):\n    valid = [value for value in values if value is not None]\n    if not valid:\n        return None\n    return sum(valid) / len(valid)'

# Version 1 handles ordinary inputs only.
def ordinary_average(values):
    return sum(values) / len(values)

# Version 2 ignores missing readings but still fails on an empty result.
def ignore_missing_average(values):
    valid = [value for value in values if value is not None]
    return sum(valid) / len(valid)

# Version 3 adds the required empty-input behaviour.
def complete_average(values):
    valid = [value for value in values if value is not None]
    if not valid:
        return None
    return sum(valid) / len(valid)

reviewed_candidates = {initial_code: ordinary_average,
                       partial_code: ignore_missing_average,
                       complete_code: complete_average}


register_sample(code_instructions, task, initial_code)
current_code = get_completion(code_instructions, task)
print("INITIAL CODE\n", current_code)
function = reviewed_candidates.get(current_code)
if function is not None:
    print("ORIGINAL REQUIREMENTS:", format_feedback(run_tests(function, initial_cases)))
    print("EXPANDED REQUIREMENTS:\n", format_feedback(run_tests(function, test_cases)))
else:
    print("New code needs review before any execution.")


# Author-written offline responses, tied to observed feedback on reviewed code.
for before, after in [(initial_code, partial_code), (partial_code, complete_code)]:
    observed = run_tests(reviewed_candidates[before], test_cases)
    prompt = make_revision_prompt(before, format_feedback(observed))
    register_sample(code_instructions, prompt, after)


def run_feedback_loop(start_code, cases, max_attempts=3):
    if max_attempts < 1:
        raise ValueError("Allow at least one attempt.")
    current_code = start_code
    history = []
    stop_reason = "attempt limit"
    for attempt in range(1, max_attempts + 1):
        # Only supplied/reviewed functions run automatically. Never exec model text.
        function = reviewed_candidates.get(current_code)
        if function is None:
            print("Review this new code before running it:\n", current_code)
            stop_reason = "unreviewed code"
            break
        started = perf_counter()
        result = run_tests(function, cases)
        feedback = format_feedback(result)
        history.append({"attempt": attempt, "code": current_code,
                        "result": result, "feedback": feedback,
                        "test_seconds": perf_counter() - started})
        print(f"Attempt {attempt}: {result['passed']} passed, {result['failed']} failed")
        if result["failed"] == 0:
            stop_reason = "all supplied tests passed"
            break
        if attempt == max_attempts:
            break  # No unused revision request after the limit.
        revision_prompt = make_revision_prompt(current_code, feedback)
        current_code = get_completion(code_instructions, revision_prompt)
    print("STOP:", stop_reason)
    return history, stop_reason, current_code


history, stop_reason, final_code = run_feedback_loop(current_code, test_cases, max_attempts=3)
print("Model/helper requests recorded:", len(request_records))


for row in history:
    print(f"\nATTEMPT {row['attempt']} — test time {row['test_seconds']:.6f} s")
    print(row["feedback"])
    print("CODE:\n", row["code"])
print("STOPPING REASON:", stop_reason)


RUN_STAGNATION_DEMO = False
if RUN_STAGNATION_DEMO:
    original_helper = get_completion
    def repeat_same_code(system_prompt, user_prompt):
        print("[Deliberately repeated supplied code — no API call]")
        return initial_code
    get_completion = repeat_same_code
    try:
        stalled_history, stalled_stop, stalled_code = run_feedback_loop(initial_code, test_cases, 3)
    finally:
        get_completion = original_helper
    print("Unresolved failures:", stalled_history[-1]["result"]["failed"])


clear_live()
