# Project working agreement

Build the Purchase Order Intelligence Agent incrementally using Python 3.11+,
FastAPI, Pydantic, and the official Anthropic Python SDK. Use Claude for project
LLM calls. Start with a custom agent loop; do not introduce orchestration frameworks.

Work on one phase at a time. Explain the concept, request/response flow, and token
implications before implementing it. Ask for approval before starting the next
phase. Phase 1 covers setup and one minimal Claude call only; tools, databases,
RAG, and memory belong to later phases.

## Repository layout

Keep application code in the installable `src/po_agent` package: `agent/` for the
loop and registry, `tools/` for tool schemas/fictional implementations, and `db/`
for PostgreSQL access. Keep offline tests in `tests/unit`, local checks in
`scripts`, earlier learning demos in `examples`, and provisioning SQL in
`database`. Do not reintroduce root-level Python application modules.

HTTP clients belong in `src/po_agent/integrations`; local mock servers belong in
`src/po_agent/services`. Keep shared response contracts in `src/po_agent/models.py`
and clearly distinguish fictional service data from the real HTTP transport.

Use an editable install (`python -m pip install -e ".[dev]"`) and package imports,
not `sys.path` modifications. Run tests with
`python -m pytest -q -p no:cacheprovider`. Use `python -m po_agent` for a paid live
run and `python -m scripts.check_database_tool` for a database check without LLM
usage. Mock both external services and configuration loading in unit tests.

## Required learning record

Update `LEARNING.md` at the end of every phase and whenever a phase is paused with
unfinished work. Preserve earlier entries; label incomplete work accurately.
Each phase entry must contain:

- What was built, why it exists, and links to the relevant source files.
- The actual LLM request/response flow: system instructions, user messages, model,
  output limit, tool schemas/results when applicable, and stop reason. Use small,
  sanitized examples and distinguish mocks from live responses.
- Reported input/output tokens and cache creation/read tokens when available,
  LLM call count, latency, estimated cost, and cumulative estimated API spend.
  Record unknown fields as `not measured` or `not reported`, never as zero.
  Application API usage is separate from Codex session usage.
- Failures, their causes, fixes, and anything still unresolved.
- Optimizations attempted, their rationale, and measured before/after results.
  Label untested ideas as hypotheses; do not claim savings without evidence.
- Validation performed, a small experiment for the learner to run, instructions
  for inspecting its results, and the phase completion/approval status.

Never put API keys, secrets, or sensitive document contents in learning records,
benchmarks, or traces. Use mocked Claude responses for most unit tests. Respect
the approximate INR 500 API budget; track cumulative estimated spend and require
explicit confirmation before expensive batch experiments.

## Benchmark record (introduced when experiments begin)

Maintain `BENCHMARKS.csv` with its header; append measured rows when experiments
run. Do not populate it with invented measurements or placeholder rows. Follow
the recording rules in `LEARNING.md`, using one row per configuration on a fixed dataset
and declared repeat count. Record baseline and candidate as separate rows sharing
a comparison ID. Keep mock and live runs separate.

For valid comparisons, hold dataset/version, scoring rubric, model, output limit,
and repeat count fixed unless one is the explicit variable being tested. Retain
sanitized per-run traces so aggregate results can be checked. Record failures in
the denominator. Report correctness alongside token/cost/latency changes; token
savings alone do not establish an improvement. Include cache tokens in accounting
without double counting and record pricing assumptions and their source/date.

Only use measured, reproducible comparisons for resume or interview claims. Link
each claim to its benchmark comparison and supporting traces in `LEARNING.md`.

