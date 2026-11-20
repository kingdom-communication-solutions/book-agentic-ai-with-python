"""Compare Responses — generated from the learner notebook.
Run from this folder or pass this script path from another directory.
"""
from pathlib import Path
import os
os.chdir(Path(__file__).resolve().parent)

# Author-written responses for a comparison exercise, not actual model benchmarks.
examples = {
    "saved-A": "A Python list and a tuple can both be changed after creation. Use [1, 2] for a list and (1, 2) for a tuple.",
    "saved-B": "A list is mutable: you can replace its items. A tuple is immutable: you cannot replace its items. Examples: values = [1, 2]; point = (1, 2). A tuple can still contain a mutable object, such as a list."
}

def get_completion(system_prompt, user_prompt, model):
    expected = "Explain the difference between a Python list and a tuple to a beginner."
    if " ".join(user_prompt.split()) != expected:
        return "No saved example matches this edited task; no model was called."
    if model not in examples:
        raise ValueError("Choose saved-A or saved-B for offline practice.")
    return "[Supplied example — no API call]\n" + examples[model]


system_prompt = """You are a Python tutor.
Explain programming concepts clearly
using simple language and examples."""
user_prompt = """Explain the difference between a Python list
and a tuple to a beginner."""
for model in ("saved-A", "saved-B"):
    print(model)
    print(get_completion(system_prompt, user_prompt, model))
    print()


values = [1, 2]
values[0] = 9
print("Changed list:", values)
point = (1, 2)
try:
    point[0] = 9
except TypeError:
    print("Tuple item replacement raises TypeError.")


evaluation = {
    "saved-A": {"accuracy": "", "clarity": "", "relevance": "", "latency": "not measured", "cost": "not measured"},
    "saved-B": {"accuracy": "", "clarity": "", "relevance": "", "latency": "not measured", "cost": "not measured"}
}
# Fill in the three empty observations for each example.
print(evaluation)
