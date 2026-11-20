"""Adapt the Workshop Planning Assistant — generated from the learner notebook.
Run from this folder or pass this script path from another directory.
"""
from pathlib import Path
import os
os.chdir(Path(__file__).resolve().parent)

import json

# Offline mode: these are author-written examples, not live API results.
_SAMPLE_RESPONSES = {'["You are a helpful AI assistant.", "Create a workshop plan for a two-hour\\nintroductory workshop on Artificial Intelligence."]': 'Introduce AI, discuss examples, explore applications, and finish with questions.', '["You are an experienced workshop facilitator\\nspecialising in introductory AI education.\\nDesign engaging and practical workshops\\nfor beginners.", "Create a workshop plan for a two-hour\\nintroductory workshop on Artificial Intelligence."]': 'Introduce the learning goals, use everyday AI examples, include a paired prompt-writing activity, and close with reflection.', '["You are an experienced workshop facilitator\\nspecialising in introductory AI education.\\nDesign engaging and practical workshops\\nfor beginners.\\nThe participants have no prior AI knowledge.\\nThey have laptops and internet access.\\nUse free tools only.\\nCombine short explanations with\\nhands-on activities.", "Create a workshop plan for a two-hour\\nintroductory workshop on Artificial Intelligence."]': 'Use short beginner explanations, a free browser tool, paired prompt practice, and a discussion of limitations.', '["You are an experienced workshop facilitator\\nspecialising in introductory AI education.\\nDesign engaging and practical workshops\\nfor beginners.\\nThe participants have no prior AI knowledge.\\nThey have laptops and internet access.\\nUse free tools only.\\nCombine short explanations with\\nhands-on activities.\\nThe workshop must last exactly 120 minutes.\\nPresent the plan as a Markdown table\\nwith these columns:\\nTime | Topic | Activity | Learning Outcome\\nEnsure the time allocations add up\\nto exactly 120 minutes.", "Create a workshop plan for a two-hour\\nintroductory workshop on Artificial Intelligence."]': '| Time | Topic | Activity | Learning Outcome |\n| --- | --- | --- | --- |\n| 00:00–00:15 | Introduction to AI | Discussion and examples | Understand the basic concept of AI |\n| 00:15–00:35 | How AI works | Short explanation and demonstration | Understand how AI systems process requests |\n| 00:35–00:55 | Generative AI | Explore an AI tool | Recognise practical applications of Generative AI |\n| 00:55–01:25 | Prompting in practice | Create and refine prompts | Apply AI to a practical task |\n| 01:25–01:45 | Limitations and responsibility | Discuss examples | Identify limitations and responsible-use considerations |\n| 01:45–02:00 | Reflection | Questions and discussion | Summarise key insights |', '["You are an experienced workshop facilitator\\nspecialising in introductory AI education.\\nDesign engaging and practical workshops\\nfor beginners.\\nThe participants have no prior AI knowledge.\\nThey have laptops and internet access.\\nUse free tools only.\\nCombine short explanations with\\nhands-on activities.\\nThe workshop must last exactly 120 minutes.\\nPresent the plan as a Markdown table\\nwith these columns:\\nTime | Topic | Activity | Learning Outcome\\nEnsure the time allocations add up\\nto exactly 120 minutes.", "Create a workshop plan for a two-hour\\nintroductory workshop on Data Science."]': '| Time | Topic | Activity | Learning Outcome |\n| --- | --- | --- | --- |\n| 00:00–00:15 | Introduction to Data Science | Discussion and examples | Understand the basic concept of Data Science |\n| 00:15–00:35 | Working with data | Short explanation and demonstration | Understand how data is collected and organised |\n| 00:35–00:55 | Exploring a small dataset | Explore a supplied CSV | Recognise practical applications of Exploring a small dataset |\n| 00:55–01:25 | Data questions in practice | Create and refine data questions | Investigate a dataset |\n| 01:25–01:45 | Limitations and responsibility | Discuss data quality | Identify limitations and responsible-use considerations |\n| 01:45–02:00 | Reflection | Questions and discussion | Summarise key insights |'}

def get_completion(system_prompt, user_prompt, model="YOUR_MODEL_NAME"):
    key = json.dumps([system_prompt, user_prompt])
    if key not in _SAMPLE_RESPONSES:
        return ("No saved example matches this edited prompt. Your code ran, "
                "but no model was called. Save your prompt for an instructor demonstration.")
    return "[Supplied teaching example — no API call]\n" + _SAMPLE_RESPONSES[key]


system_prompt = """You are an experienced workshop facilitator
specialising in introductory AI education.
Design engaging and practical workshops
for beginners.
The participants have no prior AI knowledge.
They have laptops and internet access.
Use free tools only.
Combine short explanations with
hands-on activities.
The workshop must last exactly 120 minutes.
Present the plan as a Markdown table
with these columns:
Time | Topic | Activity | Learning Outcome
Ensure the time allocations add up
to exactly 120 minutes."""

user_prompt = """Replace this with your Data Science workshop request."""
response = get_completion(system_prompt, user_prompt, model="YOUR_MODEL_NAME")
print(response)
