"""Trace a Python Request — generated from the learner notebook.
Run from this folder or pass this script path from another directory.
"""
from pathlib import Path
import os
os.chdir(Path(__file__).resolve().parent)

from pathlib import Path

config_template = Path("openai.env.example")
if not config_template.exists():
    config_template.write_text("OPENAI_API_KEY=YOUR_OPENAI_API_KEY\nOPENAI_MODEL=YOUR_MODEL_NAME\n", encoding="utf-8")
# The downloaded package uses one configuration at its root.
package_root = next((p for p in [Path.cwd(), *Path.cwd().parents]
                     if (p / "COMPANION_VERSION").is_file()), None)
if package_root:
    print("Configure the package-root .env beside COMPANION_VERSION.")
else:
    print("Open openai.env.example, save a copy as .env, and replace the placeholders there.")


from types import SimpleNamespace

# Supplied examples only. No network calls or API credentials.
SAVED_RESPONSES = {
    "What is a variable in Python?": "A variable is a name that refers to a value. For example, age = 25.",
    "Explain what a Python list is to a beginner. Provide a simple Python example.": "A list holds a sequence of items. For example, books = ['History', 'Science']."
}
request_log = []

class SampleResponses:
    def create(self, *, model, instructions, input):
        text = SAVED_RESPONSES.get(" ".join(input.split()))
        if text is None:
            text = "No saved example matches this request. No AI model was called; save it for an instructor demonstration."
        return SimpleNamespace(output_text="[Supplied example — no API call]\n" + text)

MODE = "offline"  # Set to "live" after preparing .env in a standard Python kernel.
MODEL = "YOUR_MODEL_NAME"
if MODE == "live":
    import sys
    if sys.platform in {"emscripten", "wasi"}:
        raise RuntimeError("The OpenAI SDK needs a standard Python kernel. Use offline mode in browser Python.")
    import os
    from openai import OpenAI
    from dotenv import load_dotenv
    load_dotenv()
    MODEL = os.getenv("OPENAI_MODEL", "")
    if not MODEL or MODEL.startswith("YOUR_"):
        raise ValueError("Set OPENAI_MODEL in your .env file.")
    client = OpenAI(timeout=45.0, max_retries=0)
else:
    client = SimpleNamespace(responses=SampleResponses())


def get_completion(system_prompt, user_prompt):
    request_log.append({"model": MODEL, "instructions": system_prompt, "input": user_prompt, "mode": MODE})
    response = client.responses.create(
        model=MODEL,
        instructions=system_prompt,
        input=user_prompt
    )
    return response.output_text


system_prompt = """You are a friendly Python tutor.
Use simple language and one practical example."""
user_prompt = "What is a variable in Python?"
response = get_completion(system_prompt, user_prompt)
print(response)


user_prompt = """Explain what a Python list is to a beginner.
Provide a simple Python example."""
response = get_completion(system_prompt, user_prompt)
print(response)


print(request_log[-1])

assert request_log[-1]["instructions"] == system_prompt
assert request_log[-1]["input"] == user_prompt
assert request_log[-1]["model"] == MODEL
print("The latest request contains the intended instructions, user input and model field.")


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

