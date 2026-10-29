# Purchase Order Intelligence Agent

A learning project for building a multi-tool AI agent incrementally with Python
and the official Anthropic SDK. The eventual agent will compare purchase orders,
invoices, and payment status.

**Current checkpoint: Phase 3 — custom multi-tool loop, tested offline and live.**
The loop uses two registered fictional tools, an iteration limit, a soft run-token
budget, and per-request usage/latency/cost reporting. The learner's live trial
completed in two LLM calls: 1,780 tokens, estimated USD 0.00025920, 4.34 seconds
overall. This validates one fixture case, not an optimization benchmark.
The Phase 1 example remains in `main.py`. Phase 2 adds a fictional purchase-order
tool and a two-request demonstration in `tool_demo.py`. Database/PDF/REST
integration belongs to Phase 4 and requires learner approval.

## Project files

```text
agentic-ai-lab/
├── .env.example       # Safe configuration template
├── .gitignore         # Excludes secrets, virtual environment, and caches
├── AGENTS.md          # Instructions for future Codex work
├── BENCHMARKS.csv     # Header for future measured comparisons
├── LEARNING.md        # Phase notes, actual usage, and lessons
├── README.md          # Setup and execution guide
├── agent_loop.py      # Iterative tool calling with request/output/token limits
├── agent_runner.py    # Live entry point using one client and a 3,000-token soft budget
├── main.py            # One live Claude request and usage reporting
├── payment_status.py  # Fictional payment-status function and schema
├── purchase_order.py  # Fictional purchase-order function and tool schema
├── requirements.txt   # Installed dependency snapshot
├── test_agent_limits.py # Loop limits, errors, and multiple-tool tests
├── test_agent_loop.py # Basic mocked agent round trip
├── test_agent_runner.py # Offline runner startup and missing-key tests
├── test_main.py       # Phase 1 offline success-path test
├── test_payment_status.py # Payment fixture and registry tests
├── test_tool_demo.py  # Phase 2 mocked round-trip and validation tests
├── test_tool_registry.py # Input validation and registry tests
├── tool_registry.py   # Schemas, functions, validators, and execution boundary
└── tool_demo.py       # Request tool, execute locally, send result, get answer
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

Expected: `33 passed`. The tests mock the SDK and environment loading; they make
no API calls. Their token numbers are fixtures.

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

For the current Phase 3 runner, execute `python agent_runner.py` after running
the offline tests. It uses one client, at most four LLM requests, and a
3,000-token soft threshold. The loop prints usage, request latency, and uncached
request/run cost estimates; the runner prints the final answer and total runtime.
Each execution incurs API usage. The threshold is checked after receiving usage,
so it can be exceeded by a request. Cached usage disables the basic run-cost
estimate rather than presenting an incomplete total.

For the Phase 2 demonstration, run `python tool_demo.py` from the activated
environment after testing. A normal run makes two paid API requests: the first
requests the tool; Python validates the arguments and reads fictional data;
the second includes the original question, assistant tool request, and matching
`tool_result`. The second request uses `tool_choice={"type": "none"}`. Per-request
usage/cost and combined run cost are printed. This is a fixed round trip, not a
general agent loop. Invalid inputs currently raise exceptions rather than being
returned as tool errors. Run it only when ready to incur API usage.

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
