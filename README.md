# Purchase Order Intelligence Agent

A Python learning project that builds a custom Claude tool-calling agent one
phase at a time. The eventual agent compares purchase orders, PDF invoices, and
payment status. Python 3.11+ is required; the current environment is Windows with
Python 3.14.2.

**Completed: Phase 4 — combined PostgreSQL, PDF, and mock payment HTTP.** The
runner retrieves purchase orders from PostgreSQL, invoice fields from a local
PDF, and payment status over HTTP. Payment data is still fictional, served by a
local FastAPI application. The three-source check and combined paid agent trial
both succeeded. The final trial used 4,024 tokens across three Claude calls,
estimated USD 0.00066040, and 6.53 seconds overall with no tool failures.

Combined milestone details: [Phase 4B–4C — PDF and payment HTTP](docs/phase-4b-plan.md).
This continues on the existing Phase 4 branch. The earlier Phase 4A live trial
used 1,827 tokens, estimated USD 0.00027630, and 2.75 seconds; it is a separate case.

## Project layout

```text
agentic-ai-lab/
├── src/
│   └── po_agent/                 # Installable application package
│       ├── __init__.py
│       ├── __main__.py           # python -m po_agent entry point
│       ├── cli.py                # Credentials, client setup, live run
│       ├── models.py             # Validated payment response contract
│       ├── agent/
│       │   ├── loop.py           # LLM iterations, history, limits, accounting
│       │   └── registry.py       # Schemas, argument validation, dispatch
│       ├── db/
│       │   └── purchase_orders.py # Parameterized PostgreSQL lookup
│       ├── integrations/
│       │   └── payments.py       # Bounded, timeout-controlled HTTP client
│       ├── services/
│       │   └── mock_payments.py  # FastAPI service with fictional payment data
│       └── tools/
│           ├── invoice.py        # Bounded extraction of labelled invoice PDFs
│           ├── purchase_order.py # Tool schema and fictional fallback
│           └── payment_status.py # Fictional payment tool
├── tests/
│   └── unit/                    # Offline tests, including mocked DB/LLM calls
├── scripts/
│   ├── check_database.py        # Check DB login and identity
│   ├── check_database_tool.py   # Check registry → DB → JSON, without Claude
│   ├── create_demo_invoice.py   # Generate the fictional PDF fixture
│   └── check_integrations.py    # Verify PostgreSQL + PDF + payment HTTP
├── data/invoices/
│   └── INV-2001.pdf             # Fictional invoice fixture, INR 15,500.00
├── examples/
│   ├── claude_connectivity.py   # Preserved Phase 1 paid example
│   └── tool_calling.py          # Preserved Phase 2 paid example
├── database/
│   ├── init.sql                 # Table and fictional seed record
│   └── readonly.sql             # Create reader role and permissions
├── docs/
│   └── phase-4b-plan.md          # Next implementation and validation checklist
├── compose.yaml                 # Local PostgreSQL service and persistent volume
├── pyproject.toml               # Package, direct dependencies, CLI, pytest config
├── requirements.txt             # Pinned dependency snapshot
├── .env.example                 # Secret-free configuration template
├── .gitignore
├── AGENTS.md                    # Instructions for future Codex work
├── LEARNING.md                  # Phase history, usage evidence, lessons
└── BENCHMARKS.csv               # Header for future controlled experiments
```

Package directories also contain `__init__.py`. Only `po_agent` is included in the
application distribution; `scripts`, `examples`, tests, and database provisioning
files are repository utilities. Run their module commands from the project root.

The `src` layout separates importable application code from repository files.
An editable install makes `po_agent` importable without `sys.path` workarounds.
There is no single mandatory Python folder layout; this uses the
[PyPA src layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)
and pytest's [integration guidance](https://pytest.org/en/stable/explanation/goodpractices.html).

## Setup

Run from the project root. Reuse `.venv` if it already exists:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e ".[dev]"
```

`pyproject.toml` declares direct dependencies and the test extra. The requirements
file is the pinned environment snapshot, not a cross-platform lockfile. Fresh
environment installation has not yet been verified. An editable installation
uses source changes immediately; reinstall after changing package metadata or
entry points. Creating the editable package may download build dependencies.

Without activation, replace `python` with `.\.venv\Scripts\python.exe` in commands.
In VS Code, select this interpreter using **Python: Select Interpreter**.

If `.env` does not exist, copy the template:

```powershell
Copy-Item .env.example .env
```

Set the real values only in local `.env`. Keep all passwords and the API key empty
in `.env.example`. Configuration groups are:

| Settings | Purpose |
| --- | --- |
| `ANTHROPIC_API_KEY` | Authenticates live Claude requests |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Initial Docker database setup |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Python's read-only database connection |
| `INVOICE_DIR` | PDF directory; defaults to `data/invoices` |
| `PAYMENT_API_BASE_URL` | Payment service; defaults to `http://127.0.0.1:8001` |

For the demonstrated setup, Python uses `127.0.0.1:5433`, database `po_agent`, and
user `agent_reader`. Existing environment variables take precedence over `.env`.
The database password is initialized on the volume's first startup; changing the
environment file does not change an existing database password.

## Offline tests

```powershell
python -m pytest -q -p no:cacheprovider
```

Expected: **89 passed**. Tests are collected from `tests/unit` using pytest's
`importlib` mode. They require neither Docker nor API credentials and make no
live LLM or database calls. Usage and timing values in them are fixtures.

Run one file or one function:

```powershell
python -m pytest tests/unit/test_agent_loop.py -v -p no:cacheprovider
python -m pytest tests/unit/test_database_tool.py::test_po_id_is_bound_as_data -v -p no:cacheprovider
```

## PostgreSQL setup and checks

Start Docker Desktop, then:

```powershell
docker compose up --wait db
docker compose ps
```

For a new database, apply the table/seed script and then create the reader role:

```powershell
Get-Content -Raw database/init.sql | docker compose exec -T db psql -U agent_admin -d po_agent -v ON_ERROR_STOP=1
Get-Content -Raw database/readonly.sql | docker compose exec -T db psql -U agent_admin -d po_agent -v ON_ERROR_STOP=1
```

`init.sql` avoids duplicate seed insertion. **Run `readonly.sql` only once**: it
creates a role and is not an idempotent migration system. Existing users do not
need to reprovision the database for this source reorganization.

Set the reader password interactively:

```powershell
docker compose exec db psql -U agent_admin -d po_agent
```

At the PostgreSQL prompt:

```text
\password agent_reader
\q
```

Save that password as `DB_PASSWORD` locally. The reader receives SELECT permission
on `public.purchase_orders`; application code must not use the setup account.

Run the checks without Claude:

```powershell
python -m scripts.check_database
python -m scripts.check_database_tool
```

The registry check should print `ok: true`, amount `"15000.00"`, and invoice
`"INV-2001"` for the seeded PO. Check an unknown ID with:

```powershell
python -m scripts.check_database_tool PO-9999
```

Its expected generic tool error exits with status 1. Connection failures also
return generic tool errors; the identity check helps diagnose connection issues.

## Run the agent

To see the complete application payload passed to Claude before each call, run:

```powershell
python -m po_agent --log-requests
```

This prints the actual SDK arguments as formatted JSON: model, output limit,
thinking configuration, all tool schemas, and the entire message history,
including prior assistant tool requests and user tool results. SDK content blocks
are represented as JSON with unset fields omitted. It is an application payload
view, not an HTTP wire capture; authentication headers and client credentials
are excluded. No explicit system message is sent by this agent. The mode prints
full prompt/tool content, so use it with this fictional demo data. The default
command keeps this detailed request logging off. Logging adds no API tokens.

The terminal shows the question and data sources first. Each Claude call shows
the history size, output limit, stop reason, tokens, latency, and estimated USD
cost. Tool sections show the arguments, request ID, and returned fields; the same
ID links each result to Claude's request. The run summary separates Claude calls
from local tool executions, then prints the final answer. These local display
details do not add tokens to Claude's requests. Payment records and the sample
invoice are fictional demo data.

The combined flow needs PostgreSQL, the included PDF, and the mock HTTP service.
Start Docker Desktop and run `docker compose up --wait db` as above. The fictional
PDF is included; if missing, generate it with `python -m scripts.create_demo_invoice`.
The generator refuses to overwrite an existing file.

In one activated terminal, keep the local payment service running:

```powershell
python -m uvicorn po_agent.services.mock_payments:app --host 127.0.0.1 --port 8001
```

Its interactive API documentation is at `http://127.0.0.1:8001/docs`. It exposes
GET payment status and health routes; it does not initiate payments.

In another activated terminal, check all sources without Claude:

```powershell
python -m scripts.check_integrations
```

Expect three `ok: true` results and `invoice_minus_po: "500.00"`: PO INR 15,000.00,
invoice INR 15,500.00, and unpaid status with INR 0.00 paid. The checker refuses
to compare invoices linked to another PO or currency. It uses exact Decimal
arithmetic. This check is not an LLM-quality evaluation.

Inspect the entry point without making a paid call:

```powershell
python -m po_agent --help
```

After the database check succeeds, run one paid trial:

```powershell
python -m po_agent
```

The equivalent installed console command is `po-agent`. Run from the project
root when using its `.env`; an installed application can also use process
environment variables. The runner uses one client, disables automatic retries,
and allows at most four LLM calls with a 6,000-token **soft** run threshold.
The live runner caps each response at 768 output tokens or the remaining observed
allowance. The reusable loop defaults to 256; callers can set `max_output_tokens`.
If Claude reaches that limit, any returned text is labelled incomplete, truncated
tool calls are not executed, and the CLI stops with a readable error. There is no
automatic paid retry. A failed payment lookup also prints the mock-service startup
command; keep that service running in a separate terminal.

Usage is known after a request finishes, so the threshold can be exceeded by one
request. The current policy stops at or above it even if that response contains
an answer. The loop prints stop reason, usage, LLM latency, and estimated uncached
request/run cost. The runner prints the final answer and total run time.

The last reported Phase 3 fictional-data trial used two LLM calls, 1,780 tokens,
estimated USD 0.00025920, and 4.34 seconds overall. It is not a controlled benchmark.
The separate Phase 4A database-backed trial is recorded above and in `LEARNING.md`.

## Earlier learning examples

Both examples make paid Claude requests when executed:

```powershell
python -m examples.claude_connectivity
python -m examples.tool_calling
```

Phase 1 makes one request. Phase 2 demonstrates a fixed tool round trip, separately
from the reusable agent loop. Historical entries in `LEARNING.md` retain old
filenames/commands; the links and current commands use this organized layout.

## Cost accounting

The current estimator uses Haiku 5.5 short-prompt standard rates: USD 0.10 per
million input tokens and USD 0.50 per million output tokens, checked 2026-10-29
against [Anthropic's model documentation](https://platform.claude.com/docs/en/models/haiku-5-5/overview).
Verify pricing before changing models or using this example later.

```text
estimated USD = (input_tokens × 0.10 + output_tokens × 0.50) / 1,000,000
```

Cached usage makes the basic run-cost estimate unavailable; cache pricing and
longer-prompt tiers are not implemented. Estimates exclude taxes and currency
conversion. Cumulative reported spend is recorded manually in `LEARNING.md`;
there is no persisted spend ledger or full tracing yet. No measured optimization
improvement is claimed. `BENCHMARKS.csv` remains header-only.

## Debug in VS Code

The checked-in [.vscode/launch.json](.vscode/launch.json) provides five Windows
configurations, explicitly using the project's `.venv` interpreter:

| Configuration | What it executes |
| --- | --- |
| Database registry check (no Claude) | Real PostgreSQL lookup through the registry |
| Registry override test (offline) | Fake function dispatch; no Docker or Claude needed |
| Mock payment HTTP service (no Claude) | Local FastAPI server; keep running for HTTP checks |
| All integrations check (no Claude) | PostgreSQL, PDF extraction, payment HTTP, and comparison |
| Full agent (paid Claude API) | Actual agent loop, database lookup, and Claude calls |

1. Open this project folder in VS Code with the Python Debugger extension.
2. For the database check, start Docker Desktop and run `docker compose up --wait db`.
3. The database configuration has `stopOnEntry: true`: it pauses automatically
   at startup, so a manual breakpoint is optional. You can also place one on
   `result = execute_tool(...)` in `scripts/check_database_tool.py`.
4. Open Run and Debug with **Ctrl+Shift+D**, select **Database registry check
   (no Claude)**, and press **F5**.
5. Press **F11** to enter `execute_tool`. Inspect `name`, `arguments`, and
   `tool_functions`. Use **F10** to step over validation, then inspect `function`
   before stepping into the database lookup.
6. **Shift+F11** steps out, **F5** continues, and **Shift+F5** stops debugging.

Choose the offline configuration to learn dictionary dispatch without a running
database. The full-agent configuration spends API credits; use it after the
database check succeeds. Set additional breakpoints in `src/po_agent/cli.py` and
`src/po_agent/agent/loop.py` to inspect messages and tool results. Do not share
credentials from debugger variables. Configuration format and shortcuts follow
[VS Code's Python debugging documentation](https://code.visualstudio.com/docs/python/debugging).

## Troubleshooting and Git checkpoints

| Symptom | Check |
| --- | --- |
| `No module named po_agent` | Activate `.venv` and run `python -m pip install -e ".[dev]"`. |
| `No module named psycopg` | Use the project interpreter and install requirements. |
| Root `agent_runner.py` or `database_tool.py` is missing | Use module commands above; these files moved into packages. |
| Database timeout | Start Docker Desktop, check `docker compose ps`, then run the DB identity check. |
| Missing setting | Configure local `.env` or process environment variables. |
| API request failure | Inspect status/stop reason; check credit, model access, and network connectivity. |

At each phase checkpoint, run offline tests, update `LEARNING.md`, inspect
`git diff` and staged changes, commit, and push the phase branch. Merge completed
phases into `main` before branching for the next phase. The package layout and
combined integrations belong to the completed Phase 4; the next phase has not
been started.

`.env`, `.venv`, caches, and packaging artifacts are ignored. `.gitignore` affects
tracking, not read access or removal of secrets from earlier commits. To refresh
the dependency snapshot after an editable install without adding a machine-local
project path, use `python -m pip freeze --exclude po-intelligence-agent > requirements.txt`.
