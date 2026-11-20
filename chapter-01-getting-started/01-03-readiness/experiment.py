"""Check Your Readiness — generated from the learner notebook.
Run from this folder or pass this script path from another directory.
"""
from pathlib import Path
import os
os.chdir(Path(__file__).resolve().parent)

support_request = {
    "order_number": "84729",
    "message": "I returned my order two weeks ago. Where is my refund?"
}

print(support_request["order_number"])
print(support_request["message"])

def get_message(request):
    return request["message"]
