# Agentic AI with Python — learner companion

Version: **0.3.1-preview**. This preview contains the currently developed learner resources for the book. It contains developed examples from Chapters 1–4; later activities are not yet included. Use CONTENTS.md to locate the exact notebook matching your book section.

## Start here

1. Extract the entire ZIP. Keep the chapter and data folders together; do not move individual notebooks.
2. Open a terminal in the extracted package root, where README.md and COMPANION_VERSION are located.
3. Use Python 3.10 or later. Create a virtual environment:

```sh
python -m venv .venv
```

On macOS/Linux activate it with `source .venv/bin/activate`. On Windows PowerShell use `.venv\Scripts\Activate.ps1`.

```sh
python -m pip install -r requirements.txt
python -m jupyterlab
```

Open the named notebook from CONTENTS.md and run it from the beginning using its Python kernel. Follow named sections rather than relying on cell numbers. Detailed instructions and any required small resources accompany each experiment.

## Optional live OpenAI requests

Copy `.env.example` to `.env` **at this package root**, then replace both placeholders with your own key and model name. Keep one configuration file here. Shared helpers find it by locating COMPANION_VERSION; standalone notebooks outside this package can still use a configuration beside the notebook.

The default uses supplied examples or deterministic Python checks. An activity must contain a live-mode switch before it can send requests. Follow that notebook's setup to enable it. Live SDK requests require standard Python and your own API access; they do not run in the browser Python kernel. Supplied responses do not measure how a model reacts to new instructions. Never share your filled `.env` file.

## Python scripts

Every notebook has an `experiment.py` containing the same code cells. Run it from its folder with `python experiment.py`, or pass its full path. Scripts locate their own activity folder before reading resources. Start with `chapter-01-getting-started/01-03-readiness/01-03-readiness.ipynb`. This first activity uses basic Python and needs no API key.

## Resources and results

The five CSVs under `data/campus_cafe/` are synthetic teaching data. Read their README and data dictionary before using them. A source absent from a sparse events/promotions table is explained there. The developing data experiments will identify which files they need; downloading these CSVs does not require studying later methods.

The notebooks include the worked examples and supplied responses used in the book. Evaluation activities include the reference facts needed to perform their checks. The Email Safety Assistant includes its reader-facing worked example; private instructor assessment notes and separate hidden answer keys are not included. Notebook outputs are cleared before packaging.

## Version and verification

Use the package version matching your book draft or edition. PACKAGE_MANIFEST.json records the exported files and their hashes. This preview is not a frozen public edition. Offline execution is tested separately from live API access; no live model result is implied by a passing offline check. Dependency installation and provider access can change, so a fully pinned public release will require a separate environment check.

Official repository: https://github.com/kingdom-communication-solutions/book-agentic-ai-with-python

Download the matching ZIP from the repository’s Releases page, or use Code → Download ZIP for the current files. You do not need Git or an online notebook to run the examples.
