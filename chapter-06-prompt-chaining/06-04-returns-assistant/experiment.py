"""Online Shop Returns Assistant — generated from the learner notebook.
Run from this folder or pass this script path from another directory.
"""
from pathlib import Path
import os
os.chdir(Path(__file__).resolve().parent)

import csv
import json
from datetime import date
from pydantic import BaseModel, ValidationError

# Every record is synthetic. Files stay beside this notebook.
with open("return_requests.csv", newline="") as file:
    requests_data = list(csv.DictReader(file))
with open("orders.csv", newline="") as file:
    orders_data = list(csv.DictReader(file))
with open("return_policy.json") as file:
    policy = json.load(file)

for row in requests_data:
    print(row["request_id"], "—", row["message"])
print("Policy window:", policy["return_window_days"], "calendar days")


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


# These definitions repeat the Pydantic pattern from Section 6.3.
class ReturnRequest(BaseModel):
    order_number: str
    item: str
    return_reason: str


class ReturnAssessment(BaseModel):
    outcome: str
    reason: str
    policy_rule: str


supplied_prompts = {'extract': 'Extract the customer\'s return request.\nReturn a plain JSON object with these string fields:\norder_number, item, return_reason.\nUse "Not provided" for missing details.\nDo not invent an identifier, item condition or reason.\nDo not include Markdown, code fences or explanatory text.', 'assess': 'Assess the return request using only the supplied customer request,\norder record, policy and calculations. Respect the stated rule priority.\nReturn plain JSON with these string fields: outcome, reason, policy_rule.\nUse one outcome: eligible, not_eligible or needs_review.\nUse a policy_rule identifier from the supplied policy.\nExplain how the evidence supports the outcome.\nIf information is insufficient, use needs_review.\nDo not invent facts, policy conditions, Markdown or code fences.', 'respond': 'Write a concise, helpful customer response using the supplied request\nand checked assessment. Explain the outcome and its supported reason.\nFor needs_review, explain what remains uncertain or needs employee review.\nDo not invent contact details, sender identities or sign-offs.\nDo not invent return procedures, shipping instructions, addresses, links or next steps.\nExplain only the checked assessment. If return instructions are unavailable,\nsay that the customer should ask support for those instructions.\nDo not claim a refund, return label or order change has been completed.\nPrepare a draft only; do not claim a message has been sent.'}

learner_prompts = {'extract': 'TODO: Write extraction instructions.', 'assess': 'TODO: Write evidence-based policy assessment instructions.', 'respond': 'TODO: Write supported response instructions.'}


def missing(value):
    return value.strip().lower() in {"", "not provided"}


def find_order(request, request_date):
    # A structural string check alone does not establish an order match.
    if missing(request.order_number):
        return None, None, "Please provide the order number so the request can be assessed."
    matches = [row for row in orders_data
               if row["order_number"] == request.order_number.strip()]
    if len(matches) != 1:
        return None, None, "An employee needs to check the order number; no unique matching order was found."
    order = matches[0]
    if request.item.strip().lower() != order["item"].strip().lower():
        return None, None, "An employee needs to check which item belongs to this order."
    try:
        days = (date.fromisoformat(request_date)
                - date.fromisoformat(order["delivered_date"])).days
    except (ValueError, TypeError):
        return None, None, "An employee needs to check the request and delivery dates."
    if days < 0:
        return None, None, "The request date is before delivery; an employee needs to check the dates."
    return order, days, None


def reference_decision(request, order, days):
    # Independent, readable policy check. Priority matches return_policy.json.
    condition = order["item_condition"]
    if condition == "damaged":
        return "needs_review", "DAMAGED"
    if condition not in {"unused", "used"}:
        return "needs_review", "CONDITION_UNKNOWN"
    if missing(request.return_reason):
        return "needs_review", "REASON_MISSING"
    if days > policy["return_window_days"]:
        return "not_eligible", "WINDOW"
    if condition == "used":
        return "not_eligible", "USED"
    return "eligible", "ELIGIBLE"


def assessment_input(request, order, row, days):
    return json.dumps({"request": request.model_dump(), "order": order,
                       "request_date": row["request_date"],
                       "days_since_delivery": days, "policy": policy}, indent=2)


def response_input(request, assessment):
    return json.dumps({"request": request.model_dump(),
                       "assessment": assessment.model_dump()}, indent=2)


# Author-written offline examples only. They are not proof of prompt quality.
supplied_requests = {'R01': {'order_number': 'O1001', 'item': 'desk lamp', 'return_reason': 'changed my mind'}, 'R02': {'order_number': 'O1002', 'item': 'headphones', 'return_reason': 'no longer need them'}, 'R03': {'order_number': 'Not provided', 'item': 'desk lamp', 'return_reason': 'changed my mind'}, 'R04': {'order_number': 'O1004', 'item': 'mug', 'return_reason': 'arrived damaged'}, 'R05': {'order_number': 'O9999', 'item': 'desk lamp', 'return_reason': 'changed my mind'}, 'R06': {'order_number': 'O1001', 'item': 'headphones', 'return_reason': 'changed my mind'}, 'R07': {'order_number': 'O1007', 'item': 'notebook', 'return_reason': 'no longer need it'}, 'R08': {'order_number': 'O1008', 'item': 'speaker', 'return_reason': 'changed my mind'}}
supplied_assessments = {'R01': {'outcome': 'eligible', 'reason': 'The unused item was requested 14 days after delivery, within the 30-day window.', 'policy_rule': 'ELIGIBLE'}, 'R02': {'outcome': 'not_eligible', 'reason': 'The request was made 45 days after delivery, outside the 30-day window.', 'policy_rule': 'WINDOW'}, 'R04': {'outcome': 'needs_review', 'reason': 'The item is recorded as damaged and needs employee review.', 'policy_rule': 'DAMAGED'}, 'R07': {'outcome': 'needs_review', 'reason': 'The item condition is unknown and needs employee review.', 'policy_rule': 'CONDITION_UNKNOWN'}, 'R08': {'outcome': 'not_eligible', 'reason': 'The non-damaged item is recorded as used; the policy excludes it.', 'policy_rule': 'USED'}}
supplied_notices = {'R01': 'Your desk lamp return meets the supplied policy: it is unused and the request was made within 30 days of delivery. This assessment does not mean a refund has been issued.', 'R02': 'The supplied policy does not accept this return because the request was made 45 days after delivery, beyond the 30-day window.', 'R04': 'The mug is recorded as damaged. An employee needs to review this case before an outcome can be confirmed. No refund has been issued by this assistant.', 'R07': 'The notebook’s condition has not been confirmed. An employee needs to check it before the return can be assessed fully.', 'R08': 'The supplied policy excludes this return because the speaker is recorded as used. This draft does not change your order.'}

for row in requests_data:
    request = ReturnRequest(**supplied_requests[row["request_id"]])
    register_sample(supplied_prompts["extract"], row["message"],
                    request.model_dump_json(indent=2))
    order, days, problem = find_order(request, row["request_date"])
    if problem:
        continue
    assessment = ReturnAssessment(**supplied_assessments[row["request_id"]])
    register_sample(supplied_prompts["assess"],
                    assessment_input(request, order, row, days),
                    assessment.model_dump_json(indent=2))
    register_sample(supplied_prompts["respond"],
                    response_input(request, assessment),
                    supplied_notices[row["request_id"]])


def run_return(row, prompts):
    # Variables belong to this request only; no earlier case result is reused.
    result = {"request_id": row["request_id"], "status": "stopped",
              "outcome": None, "stopped_at": None, "message": ""}
    print("\nCASE", row["request_id"])
    raw_request = get_completion(prompts["extract"], row["message"])
    print("EXTRACTION:", raw_request)
    try:
        request = ReturnRequest.model_validate_json(raw_request)
    except ValidationError:
        result.update(stopped_at="extraction structure", message="The extraction was not a valid request record.")
        print(result["message"])
        return result
    order, days, problem = find_order(request, row["request_date"])
    if problem:
        result.update(stopped_at="order/date match", message=problem)
        print(problem)
        return result

    # Python supplies the matching record, policy and reproducible date calculation.
    result["days_since_delivery"] = days
    raw_assessment = get_completion(prompts["assess"],
                                    assessment_input(request, order, row, days))
    print("ASSESSMENT:", raw_assessment)
    try:
        assessment = ReturnAssessment.model_validate_json(raw_assessment)
    except ValidationError:
        result.update(stopped_at="assessment structure", message="The assessment structure failed.")
        print(result["message"])
        return result

    # Named gates: inspect and test each condition before passing information on.
    allowed_outcomes = {"eligible", "not_eligible", "needs_review"}
    rule_ids = {rule["id"] for rule in policy["rules"]}
    if assessment.outcome not in allowed_outcomes or assessment.policy_rule not in rule_ids:
        result.update(stopped_at="outcome/rule", message="An outcome or policy identifier is not permitted.")
        print(result["message"])
        return result
    expected_outcome, expected_rule = reference_decision(request, order, days)
    if (assessment.outcome, assessment.policy_rule) != (expected_outcome, expected_rule):
        result.update(stopped_at="policy disagreement", message="The assessment disagrees with the independent policy check. Employee review is needed.")
        print(result["message"])
        return result
    if missing(assessment.reason):
        result.update(stopped_at="missing explanation", message="The assessment does not explain its decision.")
        print(result["message"])
        return result

    # A correct label does not prove the explanation is factual: inspect it too.
    draft = get_completion(prompts["respond"], response_input(request, assessment))
    print("DRAFT RESPONSE:", draft)
    result.update(status="draft_ready", outcome=assessment.outcome,
                  assessment=assessment.model_dump(), draft=draft)
    return result


USE_OPENAI = False
RUN_ALL_CASES = False
CASE_ID = "R01"

if USE_OPENAI:
    if RUN_ALL_CASES:
        raise ValueError("Choose one case for live mode; do not run a live batch.")
    if any("TODO" in prompt for prompt in learner_prompts.values()):
        raise ValueError("Complete all three prompts before live execution.")
    configure_live()
    active_prompts = learner_prompts
else:
    # Fixed supplied instructions/responses demonstrate the gates.
    # They do not evaluate the reader's edited prompts.
    active_prompts = supplied_prompts
    print("OFFLINE SUPPLIED DEMONSTRATION — learner prompts are not sent to a model.")


chosen_rows = requests_data if RUN_ALL_CASES else [
    row for row in requests_data if row["request_id"] == CASE_ID
]
if not chosen_rows:
    raise ValueError("Unknown CASE_ID. Choose one shown in the input table.")
results = [run_return(row, active_prompts) for row in chosen_rows]
print("\nSUMMARY")
for result in results:
    print(result["request_id"], "|", result["status"], "|",
          result["outcome"] or "not assessed", "|", result["stopped_at"] or "all gates passed")
print("Requests recorded in this run:", len(request_records))


# Close the optional live client without another request.
clear_live()

