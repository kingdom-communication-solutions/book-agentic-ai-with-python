"""Improve a Cancer Classification Report with Feedback — generated from the learner notebook.
Run from this folder or pass this script path from another directory.
"""
from pathlib import Path
import os
os.chdir(Path(__file__).resolve().parent)

import csv
import json
import hashlib
from pathlib import Path

# Explicit text labels avoid confusing malignant with the loader's numeric 1.
with open("predictions.csv", newline="") as file:
    rows = list(csv.DictReader(file))
with open("reference-results.json") as file:
    reference = json.load(file)
print(Path("dataset-notes.md").read_text())
assert rows, "No predictions were loaded."
allowed = {"benign", "malignant"}
assert all(r["reference_label"] in allowed and r["predicted_label"] in allowed for r in rows)
assert len({r["sample_id"] for r in rows}) == len(rows), "Duplicate sample identifiers."
assert hashlib.sha256(Path("predictions.csv").read_bytes()).hexdigest() == reference["prediction_sha256"], "The fixed input file has changed."


# Compute the reference from recorded predictions, not from an LLM's report.
correct = sum(r["reference_label"] == r["predicted_label"] for r in rows)
malignant = [r for r in rows if r["reference_label"] == "malignant"]
detected = sum(r["predicted_label"] == "malignant" for r in malignant)
assert malignant, "Malignant-class recall is undefined without reference malignant samples."
counts = {
    "evaluated_samples": len(rows), "correct_predictions": correct,
    "malignant_samples": len(malignant), "correct_malignant": detected,
    "missed_malignant": len(malignant) - detected,
    "benign_samples": len(rows) - len(malignant),
    "benign_predicted_malignant": sum(r["reference_label"] == "benign" and r["predicted_label"] == "malignant" for r in rows),
}
metrics = {"accuracy": round(correct / len(rows), 4),
           "malignant_recall": round(detected / len(malignant), 4),
           "missed_malignant": len(malignant) - detected}
assert counts == reference["counts"], "Resolve the count disagreement before reporting."
assert all(metrics[k] == reference[k] for k in metrics), "Reference metric disagreement."
print("VERIFIED COUNTS")
for name, value in counts.items():
    print(name.replace("_", " ") + ":", value)
print("VERIFIED METRICS")
print(json.dumps(metrics, indent=2))

# A small confusion table. Rows are reference labels; columns are predictions.
print("\nReference / predicted | malignant | benign")
print(f"malignant             | {detected:9d} | {len(malignant)-detected:6d}")
print(f"benign                | {counts['benign_predicted_malignant']:9d} | {correct-detected:6d}")
evidence = {"counts": counts, **metrics}


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

supplied_prompts = {'writer': 'Write a concise educational report using only the supplied\nclassification results.\n\nReturn a plain JSON object with these fields:\naccuracy, malignant_recall, missed_malignant, summary, limitations.\n\nExpress accuracy and malignant_recall as numbers between\n0 and 1, rounded to four decimal places.\n\nExplain the results without inventing findings.\nDo not claim that these results establish clinical suitability.\nDo not include Markdown fences or additional text.', 'feedback': 'Revise the current report using the reference results\nand the feedback below.\n\nCorrect the identified problems while preserving supported findings.\nKeep the same five JSON fields.\nDo not change the reference values or invent new conclusions.'}
learner_prompts = {'writer': 'TODO: Write the report instruction.', 'feedback': 'TODO: Write the evidence-based revision instruction.'}


from pydantic import BaseModel, ConfigDict, Field, ValidationError


class ClassificationReport(BaseModel):
    # Reject missing/extra fields, numeric strings, booleans and non-finite values.
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)
    accuracy: float = Field(ge=0, le=1)
    malignant_recall: float = Field(ge=0, le=1)
    missed_malignant: int = Field(ge=0)
    summary: str = Field(min_length=1)
    limitations: str = Field(min_length=1)


def check_report(raw):
    try:
        report = ClassificationReport.model_validate_json(raw)
    except ValidationError as error:
        details = "; ".join(str(item["loc"]) + ": " + item["msg"] for item in error.errors())
        return None, ["Invalid report structure: " + details]
    problems = []
    for name, expected in metrics.items():
        actual = getattr(report, name)
        # Round to the instructed precision before numerical comparison.
        matches = round(actual, 4) == expected if name != "missed_malignant" else actual == expected
        if not matches:
            problems.append(f"{name}: reported {actual}; reference {expected}. Correct this value.")
    for name in ["summary", "limitations"]:
        if not getattr(report, name).strip():
            problems.append(name + " must contain a meaningful explanation.")
    return report, problems


def show_report(raw):
    # Keep the JSON visible and print prose separately for easy classroom reading.
    try:
        print(json.dumps(json.loads(raw), indent=2, ensure_ascii=False))
    except (ValueError, TypeError):
        print(raw)


def initial_request():
    return "Report these verified educational results:\n" + json.dumps(evidence, indent=2)


def revision_request(raw, feedback, prompts):
    return f"""{prompts['feedback']}

Original reporting requirements:
{prompts['writer']}

Reference results:
{json.dumps(evidence, indent=2)}

Current report:
{raw}

Feedback:
{feedback}

Return only the revised JSON object.
"""


supplied_reports = ['{\n  "accuracy": 1.0,\n  "malignant_recall": 1.0,\n  "missed_malignant": 0,\n  "summary": "All evaluated samples were correctly classified.",\n  "limitations": "The classifier can be used for diagnosis."\n}', '{\n  "accuracy": 0.986,\n  "malignant_recall": 0.9811,\n  "missed_malignant": 1,\n  "summary": "The classifier identified every malignant sample correctly.",\n  "limitations": "These results establish readiness for clinical use."\n}', '{\n  "accuracy": 0.986,\n  "malignant_recall": 0.9811,\n  "missed_malignant": 1,\n  "summary": "The classifier correctly classified 141 of 143 samples. It identified 52 of 53 malignant samples and missed 1. One benign sample was classified as malignant.",\n  "limitations": "These results describe one held-out educational split. They do not establish clinical suitability or performance on future populations."\n}']
supplied_reviews = {
    supplied_reports[0]: {'accepted': False, 'feedback': "The report's perfect-classification claim contradicts the recorded errors. Remove the unsupported diagnosis claim and describe this educational split only."},
    supplied_reports[1]: {'accepted': False, 'feedback': 'The summary claims every malignant sample was identified, but the reference records one missed malignant sample. Correct the interpretation. Replace the unsupported clinical-readiness claim with the limits of this educational evaluation.'},
    supplied_reports[2]: {'accepted': True, 'feedback': ''}
}

# Human reviews of fresh live reports belong here, keyed by the EXACT report text.
human_reviews = {}


# Register supplied examples with unchanged prompts/evidence only.
register_sample(supplied_prompts["writer"], initial_request(), supplied_reports[0])
for before, after in zip(supplied_reports, supplied_reports[1:]):
    _, problems = check_report(before)
    problems.append("Content review: " + supplied_reviews[before]["feedback"])
    prompt = revision_request(before, "\n".join(problems), supplied_prompts)
    register_sample(supplied_prompts["writer"], prompt, after)


def run_report_loop(prompts, reviews, max_attempts=3):
    if not 1 <= max_attempts <= 3:
        raise ValueError("Use one to three total report attempts.")
    raw = get_completion(prompts["writer"], initial_request())
    history = []
    stop_reason = "attempt limit reached with unresolved problems"
    for attempt in range(1, max_attempts + 1):
        print(f"\nREPORT ATTEMPT {attempt}")
        show_report(raw)
        report, problems = check_report(raw)
        # Reviews are tied to the exact report, never carried over to a new draft.
        review = reviews.get(raw)
        text_feedback = review["feedback"].strip() if review else ""
        if text_feedback:
            problems.append("Content review: " + text_feedback)
        accepted = report is not None and not problems and review is not None and review["accepted"]
        history.append({"attempt": attempt, "report": raw,
                        "problems": list(problems), "content_review": review,
                        "accepted": accepted})
        print("CHECK FEEDBACK:")
        print("\n".join(problems) if problems else "Numerical/structure checks passed; examine the text.")
        if accepted:
            stop_reason = "checks and content review satisfactory"
            break
        if not problems:
            stop_reason = "awaiting human review"
            break  # Numeric success alone is never an acceptance decision.
        if attempt == max_attempts:
            break  # Do not request a fourth report or an unused final revision.
        feedback = "\n".join(problems)
        raw = get_completion(prompts["writer"], revision_request(raw, feedback, prompts))
    print("\nSTOP:", stop_reason)
    return history, stop_reason


USE_OPENAI = False
MAX_ATTEMPTS = 3
if USE_OPENAI:
    if any("TODO" in value for value in learner_prompts.values()):
        raise ValueError("Complete both instructions before enabling OpenAI.")
    configure_live()
    active_prompts = learner_prompts
    active_reviews = human_reviews
else:
    print("OFFLINE SUPPLIED DEMONSTRATION — edits are not sent to a model.")
    active_prompts = supplied_prompts
    active_reviews = supplied_reviews

history, stop_reason = run_report_loop(active_prompts, active_reviews, MAX_ATTEMPTS)
print("Helper requests in this run:", len(request_records))


# Disabled by default. Review the current live report without an API call.
APPLY_HUMAN_REVIEW = False
if APPLY_HUMAN_REVIEW:
    raw = history[-1]["report"]
    if raw not in human_reviews:
        raise ValueError("Add a review for the exact current report first.")
    report, problems = check_report(raw)
    review = human_reviews[raw]
    if review["feedback"].strip():
        problems.append("Content review: " + review["feedback"].strip())
    accepted = report is not None and not problems and review["accepted"]
    history[-1].update(problems=problems, content_review=review, accepted=accepted)
    stop_reason = ("checks and content review satisfactory" if accepted else
                   "attempt limit reached with unresolved problems" if len(history) >= MAX_ATTEMPTS else
                   "awaiting human review")
    print("REVIEW STATUS:", stop_reason)


# One explicit live revision after human feedback; never a new initial report.
REQUEST_REVIEWED_REVISION = False
if REQUEST_REVIEWED_REVISION:
    if not USE_OPENAI or history[-1]["accepted"] or len(history) >= MAX_ATTEMPTS:
        raise ValueError("No live revision is permitted in this state.")
    raw = history[-1]["report"]
    review = human_reviews.get(raw)
    if review is None:
        raise ValueError("Review the exact current report before requesting a revision.")
    _, problems = check_report(raw)
    if review["feedback"].strip():
        problems.append("Content review: " + review["feedback"].strip())
    if not problems:
        raise ValueError("No specific correction feedback is available.")
    revised = get_completion(active_prompts["writer"], revision_request(raw, "\n".join(problems), active_prompts))
    report, problems = check_report(revised)
    history.append({"attempt": len(history)+1, "report": revised,
                    "problems": problems, "content_review": None, "accepted": False})
    stop_reason = "awaiting human review"
    show_report(revised)
    print("Review this new report separately; it has not been accepted.")


print("\nTRACE SUMMARY")
for attempt in history:
    print("Attempt", attempt["attempt"], "| problems:", len(attempt["problems"]),
          "| accepted:", attempt["accepted"])
print("STOP:", stop_reason)


clear_live()
