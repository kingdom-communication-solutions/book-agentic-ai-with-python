# Campus Café Detective — Analysing Sales with CoT

Open `cafe-cot-project.ipynb` from the downloaded companion and run from the beginning. The book's browser workspace names the same file `project-workspace.ipynb`. The canonical starter is `experiment.ipynb`. Keep all five CSV files beside the notebook. No external data service is needed.

The guided task compares daily coffee sales on lecture days with other days. You inspect five files, join context, calculate means, draw a chart, compare basic and CoT prompts and revise one instruction. Then choose a different question and write your own checked report. There is nothing to submit.

## Browser workspace

Open the project from the book's Environment Setup page. The file browser should show the notebook and all five CSV files in the project folder. Wait for Python (Pyodide) to become Idle. Run cells in order with Shift+Enter. Keep USE_OPENAI = False. Download your edited notebook before leaving; browser storage can be cleared.

## Local JupyterLab

Extract the entire companion ZIP. From its root, create/activate your Python environment, run `python -m pip install -r requirements.txt`, then `python -m jupyterlab`. Open this chapter's project folder. Its five CSVs must stay beside the notebook. Alternatively, run `python experiment.py` from a terminal; use JupyterLab for your written answers and independent analysis.

## Optional OpenAI

Copy the package-root `.env.example` to `.env`, and fill your own OPENAI_API_KEY and OPENAI_MODEL. Keep USE_OPENAI false until ready. The three guided requests use the existing get_completion helper. Independent questions require additional requests only when you explicitly run them. Offline reports are supplied teaching examples, not fresh model outputs. Without a key, complete the independent analysis with clearly labelled reader-written draft reports.

## Read the data

Sales has daily quantities, actual prices and revenue for five products across 90 days. Prices already include recorded discounts. Weather and calendar join on date; promotions join on date and product_id. Events are sparse and expected attendance is not café attendance. Read the field descriptions in the notebook and inspect all five tables before analysing.

Consult the separate learner walkthrough after your own attempt. Private instructor review guidance is not included in this package.
