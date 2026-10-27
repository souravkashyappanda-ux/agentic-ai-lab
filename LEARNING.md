# Learning log

## Phase 1: Python setup and Claude API connectivity

**Status:** Implementation complete; ready for the first GitHub checkpoint.
The learner has not confirmed completing the interactive debugging exercise.
Phase 2 requires explicit approval.

### What we built

| File | Purpose |
| --- | --- |
| [main.py](main.py) | Load configuration, send one Claude request, print response and usage. |
| [test_main.py](test_main.py) | Test request construction, answer printing, and cost arithmetic offline. |
| [.env.example](.env.example) | Safe configuration template without a real key. |
| [requirements.txt](requirements.txt) | Snapshot of installed dependency versions. |
| [README.md](README.md) | Setup, running, testing, debugging, and GitHub instructions. |
| [AGENTS.md](AGENTS.md) | Persistent instructions for future Codex work. |
| [BENCHMARKS.csv](BENCHMARKS.csv) | Header for future controlled experiments. |

The learner verified Python 3.14.2 and pip 25.3 in `.venv`. Direct dependencies
are anthropic 2.3.0, python-dotenv 1.2.4, and pytest 9.1.1. The snapshot includes
transitive packages too. Testing used the existing Windows environment; a fresh
installation has not yet been verified.

### LLM request and response

```text
.env → environment → Python → Anthropic SDK → Claude API
                                                 ↓
terminal ← answer + usage + latency + cost ← Message
```

The API key authenticates the HTTP request; it is not part of the prompt.
There are no explicit system instructions or tool definitions in Phase 1.

```python
model = "claude-haiku-5-5"
max_tokens = 128
thinking = {"type": "disabled"}
messages = [
    {"role": "user", "content": "Explain a purchase order in one short sentence."}
]
```

Automatic retries are disabled and the request timeout is 30 seconds. The SDK
returns a `Message` with content blocks and usage metadata. The application prints
the full response for learning and extracts text blocks for the answer.

The learner reported this live answer:

> A purchase order is a formal document a buyer sends to a seller to request
> specific goods or services at agreed prices and terms.

The stop reason was `end_turn`: the model finished before the 128-token output
ceiling. The ceiling does not mean 128 tokens are automatically billed.

### Measured usage and estimated cost

These figures come from the learner's pasted live terminal output.

| Metric | Value |
| --- | --- |
| Reported live calls | 1 |
| Input tokens | 21 |
| Output tokens | 40 |
| Thinking tokens | 0 |
| Cache creation tokens | 0 |
| Cache read tokens | 0 |
| Request latency | 1.36 seconds |
| Estimated request cost | USD 0.00002210 |
| Cumulative estimated cost of reported live calls | USD 0.00002210 |

```text
input cost  = 21 × $0.10 / 1,000,000 = $0.00000210
output cost = 40 × $0.50 / 1,000,000 = $0.00002000
total                                  $0.00002210
```

Rates were checked on 2026-10-26 against
[Anthropic's model documentation](https://platform.claude.com/docs/en/models/haiku-5-5/overview).
They apply to this short, standard request without caching. Estimates exclude
taxes, currency conversion, and unreported account activity. Codex session usage
is separate from application API usage. The application does not automatically
persist traces or cumulative spending yet.

### Validation and failures

- The learner ran `python -m pytest -q`: **1 passed in 3.44s**. This is test-suite
  duration, separate from the 1.36-second live request latency.
- The test uses fake credentials and a mocked client. Its token values are
  fixtures, not additional measured API usage.
- Final preparation checks: Codex ran the offline suite (**1 passed in 3.72s**)
  and `python -m pip check` (**No broken requirements found**). Pytest reported
  a local cache-write warning. A follow-up with
  `python -m pytest -q -p no:cacheprovider` passed (**1 passed in 3.64s**) without
  warnings; the cache issue does not affect the tested application behavior.
- All nine publishable files exist; local Markdown links resolve; duplicate
  filenames are removed; the CSV has one unique-column header and no data rows.
  A limited credential-pattern check found no matches in these files, and the
  example key is empty. Codex did not read `.env` or make a live API call.
- No application failure was reported. Missing configuration prints a message;
  API errors currently propagate as exceptions. Error-path tests are future work.
- Live evidence is the learner's conversation output; no application trace file
  exists. A controlled optimization benchmark has not been run.
- Documentation preparation briefly introduced duplicate learning filenames and
  a misspelled benchmark filename. Before this checkpoint they were consolidated
  into `LEARNING.md` and `BENCHMARKS.csv`, with references updated.

### What we learned and optimized

- Python modules can contain functions without classes. Indentation defines
  blocks; the `__main__` guard calls the entry function when executed directly.
- `with` closes the client, similar to Java's try-with-resources. Mocks replace
  dependencies, similar in purpose to Mockito.
- Tokens are model-processing units; input and output have separate prices.
- A short prompt, bounded output, and disabled retries limit spending exposure.
  No before/after comparison exists, so no measured savings are claimed.
- `.gitignore` controls ordinary Git tracking, not file-reading access. Real keys
  belong in local environment configuration.

### Learner experiment and next checkpoint

Run `python -m pytest -q` and debug `test_main_success` using the README steps.
Pause before cost calculation and inspect the response and token values. Change
the mock's output-token fixture locally, predict the cost, and observe the cost
assertion fail. Restore the fixture and rerun the test. This needs no API call.

Setup began on 2026-10-26 with only an unvalidated `.venv` and no Git repository.
The first live call and passing mocked test are recorded above. Next: commit and
push the Phase 1 checkpoint. Tool calling has not started.

## Phase 2: Basic tool calling — started 2026-10-27

- **Approval and status:** The learner approved starting Phase 2. Work is being
  taught incrementally for the learner to execute. Phase 3 is not approved.
- **First component:** A small `get_purchase_order(po_id)` function backed by
  fictional in-memory data. The saved function is now present in
  [purchase_order.py](purchase_order.py); the learner reported completing the
  direct-call step, without pasting its successful output. No
  database, registry, or general agent loop is introduced at this step.
- **Planned request/response flow:** Send the user's question and tool schema to
  Claude; receive a `tool_use` block; execute the approved Python function; send
  a `tool_result` linked to the tool-use ID; receive the final text answer.
  Claude requests execution; application code actually runs the function.
- **Usage and spend:** The learner reported one Phase 2 live call from
  [tool_demo.py](tool_demo.py): 473 input tokens, 57 output tokens, zero cache
  creation/read and thinking tokens, 1.36-second request latency, and estimated
  cost USD 0.00007580 using the Phase 1 short-prompt pricing assumptions.
  Cumulative estimated spend across the two reported live calls is
  USD 0.00009790. Unreported activity is unknown. Codex made no live call.
  A full single-tool round trip will require two LLM requests.
- **Token implications:** Tool schemas and tool results add input context. The
  second request also resends the question and assistant tool-use message.
- **Validation and failures:** The learner created the
  `phase-2-basic-tool-calling` branch. An unfinished shell quote first caused a
  continuation prompt; cancelling and closing the quote fixed that command.
  Next, import failed because `purchase_order.py` was empty on disk. Saving the
  function fixed the missing definition. Codex verified the saved source, but
  has not executed it. No automated Phase 2 test has run yet.
- **Additional failure and recovery:** Two attempts stopped with
  `IndentationError: unexpected indent` before module execution, so those
  attempts made no API requests. The learner corrected indentation and the
  next attempt returned `stop_reason=tool_use`, requesting `get_purchase_order`
  with `{"po_id": "PO-1001"}`. The saved program currently prints this request
  without executing the function. Evidence is the learner's terminal output.
- **Optimizations:** Plan to keep the fictional tool result small. No optimization
  experiment has run and no savings are claimed.
- **Learner experiment:** Call the Python function directly for a known and an
  unknown PO ID, inspect the returned dictionary/error, then add its mocked LLM
  integration in the following step. No API request is needed for this exercise.
- **Next instruction:** Add a tool schema beside the function and print it as
  JSON locally. This describes the callable to Claude; it does not execute it or
  enforce runtime input validation. Schema creation and inspection are pending.
- **Schema progress:** Codex has now inspected the saved `PURCHASE_ORDER_TOOL`
  dictionary in `purchase_order.py`: it declares a required string `po_id` and
  disallows additional properties. No execution or live-call result was supplied.
- **Next incremental exercise:** Create `tool_demo.py` to send the schema in one
  request and inspect response blocks, including tool name, input, and call ID.
  The demonstration will not execute the function yet. Source creation, mocked
  verification, and live usage measurements for this step remain pending.
- **Exercise update:** The request-inspection step above is now completed and
  measured. Next, import the function, check the requested tool name and input,
  execute the function, and prepare a result linked to the tool-use ID. The
  second model request and automated tool-flow tests are still pending.
- **Interpretation:** Input usage rose from 21 in Phase 1 to 473 in this request,
  but the prompts also differ. Tool definitions and API tool-use instructions
  contribute input context; this is not a controlled measurement of schema cost
  or an optimization comparison. No benchmark row or savings claim is warranted.
- **Local execution code progress:** The learner has saved the function import,
  tool-name check, argument validation, and direct function invocation in
  `tool_demo.py`. Codex inspected the source; execution of this version has not
  been reported. The next instruction adds a JSON tool result and the second API
  request, preserving the original assistant content and matching tool-use ID.
  This step remains unmeasured; no additional spend is added to the ledger.
- **Round-trip scope failure and fix:** A later learner run completed the first
  API request (1.19 seconds, estimated USD 0.00007580), then raised
  `NameError: name 'messages' is not defined`. The continuation block was beneath
  the module-level `if __name__ == "__main__"` guard, outside `main()`, whose
  local variables it needed. Codex moved the guard to the file's end, keeping
  the continuation inside `main()`, and added an early return for a direct
  `end_turn` response. No global variables were introduced. No second API call
  was reached in the failing run. Token counts for this latest call were not
  included in the pasted excerpt and are not inferred from its cost.
- **Updated reported spend:** Three reported paid requests across both phases
  total an estimated USD 0.00017370. This includes the charged request in the
  failed round trip, not just successful application runs. Unreported activity
  remains unknown; this is not an account billing total.
- **Offline regression verification:** Added
  [test_tool_demo.py](test_tool_demo.py). It checks the two-request history,
  matching tool-use ID, actual fictional tool result, combined cost arithmetic,
  direct-answer early exit, invalid name/arguments, and truncated-response
  rejection. SDK responses and mocked transport require no network or credentials.
  `python -m pytest -q -p no:cacheprovider`: **9 passed in 3.33s** including the
  Phase 1 test. Codex made no paid requests. The live two-request flow remains
  awaiting learner execution; Phase 2 is not yet marked complete.

### Phase 2 live completion and routing lesson

The learner reported a successful full round trip after the scope fix:

| Request | Input tokens | Output tokens | Request latency | Estimated USD |
| --- | --- | --- | --- | --- |
| Tool selection | 473 | 57 | 1.34 seconds | 0.00007580 |
| Final answer after tool result | 590 | 45 | 1.06 seconds | 0.00008150 |
| Successful run total | 1063 | 102 | 2.40 seconds summed request time | 0.00015730 |

Both responses reported zero cache creation/read and thinking tokens. The first
stopped with `tool_use`; Python executed the fictional lookup and sent the linked
result. The second stopped with `end_turn` and answered that PO-1001's supplier is
Demo Office Supplies, its amount is INR 15,000, and its status is approved.
The summed request time is not an end-to-end run measurement.

The learner also pasted the earlier failed run again; that is the same already
recorded 1.19-second request, not an additional charge. Its complete pasted usage
now confirms 473 input and 57 output tokens. Across five distinct reported API
requests (one Phase 1, two earlier Phase 2 requests, and this successful pair),
cumulative estimated spend is **USD 0.00033100**. Unreported account activity is
unknown. No new live requests were made by Codex.

**Routing lesson:** For this fixed question, application code can call
`get_purchase_order("PO-1001")` directly and ask Claude only to explain the result.
Model-driven tool selection is useful when natural-language requests may require
different tools, arguments, or follow-up actions. It is an architectural choice,
not a requirement to put an LLM before every function call. If no natural-language
explanation is needed, the application can display the structured data directly.

The observed selection request cost USD 0.00007580, but a direct-routing candidate
has not been run. Its prompt/token count would differ, so net cost/latency savings
and correctness are not yet measured. No benchmark comparison or improvement
claim is recorded. A future controlled experiment can compare these approaches
with the same questions and correctness rubric.

**Status:** Phase 2's basic tool-calling implementation, offline tests, and learner
live verification are complete. GitHub commit/push remains a learner checkpoint.
Phase 3 still requires explicit approval. The earlier progress bullets record
the intermediate states and are superseded by this completion entry.

## Future phase entry template

For each phase, record:

1. Status, what was built, why it exists, and source links.
2. Sanitized request/response flow, model/settings, and mock/live distinction.
3. Actual usage, latency, cost assumptions, and cumulative estimated spend.
4. Failures, fixes, limits, and validation commands/results.
5. Optimizations with comparison IDs and correctness evidence; label hypotheses.
6. A learner experiment, inspection steps, and next-phase approval status.

## Benchmark recording rules

`BENCHMARKS.csv` contains only its header until controlled experiments run. The
connectivity check is not an optimization benchmark.

- One row represents an executed configuration on a versioned dataset with a
  declared repeat count. Pair baseline/candidate rows using `comparison_id`.
- Keep dataset, rubric, model, output limit, and repeats fixed unless one is the
  explicit variable. Save secret-free prompts and settings at `config_path`.
- Separate mock and live results. Sum usage, calls, and cost across all attempts,
  including failures. Empty numeric cells mean unknown or inapplicable; zero
  means observed zero. Explain missing data in `notes`.
- Store rates as fractions from 0 to 1. Task success/error rates use all attempts
  as the denominator. Define the tool-selection denominator in saved config.
- Latencies measure complete case attempts, including failures. Specify the
  percentile calculation in the evaluator; request latency is a different metric.
- Record pricing source/date. Account for cache field semantics without double
  counting. Preserve sanitized per-attempt evidence at `trace_path` and record
  code revision/dirty state.
- Token reduction is `(baseline - candidate) / baseline * 100` for a positive
  baseline. Report correctness changes and sample size alongside savings.
- Resume or interview claims must link to reproducible comparison results.
