# Purchase Order Intelligence Agent

A learning project for building a multi-tool AI agent incrementally with Python
and the official Anthropic SDK. The eventual agent will compare purchase orders,
invoices, and payment status.

**Current checkpoint: Phase 1 — Python setup and Claude API connectivity.**
The application sends one short prompt and reports the answer, token usage,
request latency, and estimated cost. It includes one offline mocked test.
Tool calling, databases, PDFs, and orchestration belong to later phases.

## Project files

```text
agentic-ai-lab/
├── .env.example       # Safe configuration template
├── .gitignore         # Excludes secrets, virtual environment, and caches
├── AGENTS.md          # Instructions for future Codex work
├── BENCHMARKS.csv     # Header for future measured comparisons
├── LEARNING.md        # Phase notes, actual usage, and lessons
├── README.md          # Setup and execution guide
├── main.py            # One live Claude request and usage reporting
├── requirements.txt   # Installed dependency snapshot
└── test_main.py       # Offline success-path test
```

Local `.env` and `.venv/` are excluded from Git.

## Setup on Windows / PowerShell

Requires Python 3.11+; this checkpoint was tested with Python 3.14.2 on Windows.
Run from the project directory. Reuse `.venv` if it already exists; otherwise
create it with the first command:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Explicit interpreter paths work without activation. Optionally activate with
`.\.venv\Scripts\Activate.ps1`, after which `python` uses the virtual environment.
The requirements file snapshots this environment, including transitive packages;
a fresh installation has not yet been verified.

If `.env` does not already exist, copy the template:

```powershell
Copy-Item .env.example .env
```

Edit `.env` locally and set `ANTHROPIC_API_KEY`. Leave `.env.example` without a real
key. Existing environment variables take precedence over `.env` by default.
The mocked test needs no API key.

## Run and inspect

Run the offline test first:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Expected: `1 passed`. The test mocks the SDK and environment loading; it makes no
API call. Its token numbers are fixtures.

For one paid live request, run from the project root:

```powershell
.\.venv\Scripts\python.exe main.py
```

The script uses `claude-haiku-5-5`, a 128-token output cap, disabled thinking,
disabled automatic retries, and a 30-second timeout. It prints the full SDK
response, answer, model, stop reason, usage, request latency, and estimated cost.
Model access requires a valid Anthropic API account and available credit.

The prompt is `Explain a purchase order in one short sentence.` The learner's
first reported call used 21 input and 40 output tokens, took 1.36 seconds, and had
an estimated cost of USD 0.00002210. Actual usage can vary. `end_turn` means the
answer finished normally; `max_tokens` means output reached its cap.

## Cost assumptions and limits

The example hardcodes short-prompt standard rates of USD 0.10 per million input
tokens and USD 0.50 per million output tokens, checked on 2026-10-26 against
[Anthropic's model documentation](https://platform.claude.com/docs/en/models/haiku-5-5/overview).
Verify rates before changing models or using the example later.

```text
estimated USD = (input_tokens × input_rate + output_tokens × output_rate) / 1,000,000
```

This covers the basic uncached request, excluding future cache pricing, other
tiers, taxes, and currency conversion. Cumulative reported spend is recorded
manually in `LEARNING.md`; the application does not persist spending or traces
yet. No measured token-optimization improvement is claimed.

## Debug in VS Code

1. Install the Microsoft Python extension if needed.
2. Open the project folder. Use **Python: Select Interpreter** in the command
   palette and choose `.venv\Scripts\python.exe`.
3. Run **Python: Configure Tests**, choose **pytest**, then the project root.
4. Set a breakpoint on `input_tokens = response.usage.input_tokens` in `main.py`.
5. In Testing, right-click `test_main_success` and choose **Debug Test**.
6. Inspect `response` and its usage. Press **F10** to step through the token and
   cost calculation. Press **F5** to continue. This test makes no API request.

To debug a live call, open `main.py` and choose **Python Debugger: Debug Python
File** from the command palette. Each execution can make a paid request. Avoid
inspecting or sharing credentials.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| `ModuleNotFoundError` | Select `.venv` and install requirements with that interpreter. |
| Missing-key message | Set the key in local `.env` or the process environment. |
| Authentication error | Verify the key locally; do not share it in logs or chat. |
| API request error | Inspect the status code for model access, credit, rate-limit, or network issues. |
| Truncated response | Review the prompt and output cap before increasing it. |
| Pytest cache-write warning | Run `python -m pytest -q -p no:cacheprovider` to test without the optional cache. |

API failures currently propagate as exceptions; structured error handling is
future work. `.gitignore` controls ordinary tracking, not file-reading access or
removal of secrets already committed.

## First GitHub checkpoint

Create an empty GitHub repository without an initial README, license, or gitignore.
Initialize Git locally and review the staged files:

```powershell
git init
git branch -M main
git check-ignore .env .venv/
git add .gitignore .env.example AGENTS.md BENCHMARKS.csv LEARNING.md README.md main.py requirements.txt test_main.py
git diff --cached --check
git diff --cached
git status --short
```

Confirm `.env` and `.venv/` are ignored and no real credentials appear in the diff.
Then commit and connect the empty repository, replacing YOUR_USERNAME:

```powershell
git commit -m "Complete phase 1 Claude connectivity and mocked test"
git remote add origin https://github.com/YOUR_USERNAME/agentic-ai-lab.git
git push -u origin main
```

If Git requests identity, set `git config user.name "Your Name"` and
`git config user.email "YOUR_EMAIL"`. A GitHub noreply email can be used.
For later checkpoints, push working code, relevant tests, and updated learning
notes together; add reproducible benchmark results when experiments begin.
