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

## Phase 3: Custom multi-tool agent loop — started 2026-10-28

- **Approval and status:** The learner approved proceeding after Phase 2.
  Workspace inspection shows a clean `main` tracking `origin/main`; the Phase 3
  branch has not yet been created locally. Phase 4 is not approved.
- **First component planned:** `tool_registry.py`, a small mapping from approved
  tool names to Python function references, with a separate list of schemas for
  Claude. The learner will create and inspect it before writing the loop.
  No Phase 3 source has been created yet.
- **Planned request/response flow:** Send question and tool schemas; append
  assistant content; if `tool_use`, validate and execute all requested approved
  tools and return linked results; repeat until `end_turn` or a budget limit.
  Tool failures will become error results. Independent tools will execute
  sequentially initially; parallel execution belongs to a later phase.
- **Token implications:** Each iteration resends the accumulated context. Input
  cost can grow even when new tool results are small. A per-response output cap,
  iteration cap, and explicit accounting/budget checks must bound the loop.
- **Usage and spend:** No Phase 3 API request has run. Phase 3 tokens, latency,
  and cost are not measured. Cumulative estimated reported spend remains
  USD 0.00033100; unreported activity is unknown. Codex has made no live call.
- **Validation and failures:** Existing Phase 2 source and branch state inspected.
  No Phase 3 tests or failures yet; registry creation and execution are pending.
- **Optimizations:** Reuse one client and share loop code rather than duplicating
  request logic. These are planned design changes, not measured token savings.
- **Learner experiment:** Retrieve the function from the registry and call it
  with PO-1001. Inspect that the dictionary stores a callable, not its result.
  This requires no LLM call. Input validation and loop tests follow next.

### Phase 3 registry progress

Codex verified `tool_registry.py` contains `TOOL_SCHEMAS` and `TOOL_FUNCTIONS`,
and the current branch is `phase-3-multi-tool-agent-loop`. The registry stores
the function reference rather than invoking it. No direct-call output has been
pasted, so successful execution is not inferred from source inspection.

The next learner step adds a strict Pydantic input model and `execute_tool` to
the registry. Pydantic 2.14.1 is already installed. This replaces repetitive
manual argument checks with runtime validation, looks up only registered
functions, and converts validation/execution failures into bounded structured
results. Result dictionaries are application data; the loop will later wrap them
in API `tool_result` blocks. Source creation and offline tests for this addition
are pending. Phase 3 token usage and latency remain unmeasured, and no paid calls
or additional estimated spend are recorded.

### Phase 3 execution boundary progress

The learner saved `PurchaseOrderInput` and `execute_tool` in
[tool_registry.py](tool_registry.py), plus [test_tool_registry.py](test_tool_registry.py).
Codex inspected the saved source: unknown names are rejected, strict Pydantic
validation rejects malformed arguments, and execution failures return a generic
error rather than exposing exception details. The broad execution exception
handler deliberately hides internal errors from the model; detailed sanitized
diagnostics are not implemented yet.

Codex ran `python -m pytest -q -p no:cacheprovider`: **16 passed in 4.15s**.
All SDK interactions were mocked; no `.env` read or live API call was needed.

The next learner instruction introduces `agent_loop.py`: an injected SDK client,
local conversation history, iteration/output limits, sequential handling of all
tool-use blocks, linked error/success results, and an `end_turn` exit. This first
loop increment does not yet implement a cumulative input/output token budget;
iteration and per-response output limits alone are not a total token budget.
Token accounting/budget enforcement and live execution remain later steps in
Phase 3. The learner will create the loop and its offline test; no new LLM usage
or measured optimization is recorded here.

### Phase 3 loop progress and budget instruction

The learner saved [agent_loop.py](agent_loop.py) and
[test_agent_loop.py](test_agent_loop.py). Codex ran
`python -m pytest -q -p no:cacheprovider`: **17 passed in 3.51s**. The added
mocked test covers a tool request followed by a final answer and the linked
result's contents. Multi-round, multi-call, and limit/error coverage is not yet
complete. No live Phase 3 request has been made by Codex or reported by the learner.

Next instruction: accumulate usage across requests, including base input, cache
creation/read, and output without double-counting thinking/cache breakdowns;
stop when the observed token threshold is reached, and lower each request's
output cap to the remaining observed allowance. This is a **soft run budget**:
usage arrives after the request, so a request's input can exceed the remaining
allowance. It must not be described as a strict pre-request spending guarantee.
The new budget code and limit tests are pending learner implementation. Cumulative
estimated reported live spend remains USD 0.00033100. This adds a spending control,
not a measured token optimization.

### Phase 3 stopping rules and history verification

Codex inspected the learner's saved token-budget implementation: reported input,
output, cache creation, and cache read tokens accumulate across iterations; each
request's output cap uses the remaining observed allowance; reaching the threshold
raises before tool execution. This is a soft, post-response budget, not a strict
spend cap. Under the current policy, even an `end_turn` answer is rejected if its
reported usage reaches or exceeds the threshold. No token-counting preflight is
implemented yet.

Added [test_agent_limits.py](test_agent_limits.py) with nine offline cases covering:
iteration exhaustion without wasted tool execution, cumulative usage, cache-token
accounting, multiple tool requests with both success/error results, repeated tool
rounds with one original question, truncated output, malformed tool-use responses,
and invalid limit configuration. The multi-call test uses one available tool and
one unavailable tool; it does not establish routing between two registered tools.

Final validation: `python -m pytest -q -p no:cacheprovider` — **26 passed in 3.42s**.
Mocks simulate LLM responses; no live API request or credentials are needed.
No measured latency/cost optimization is claimed. Live Phase 3 usage remains
unmeasured and cumulative estimated reported spend remains USD 0.00033100.
Next: inspect these tests, then add a live runner with retries disabled and per-run
latency/cost reporting. A second registered fictional tool is still needed to
demonstrate successful multi-tool routing. Phase 3 remains in progress.

### Phase 3 second-tool instruction

The next learner step adds `payment_status.py` with a fictional, read-only
`get_payment_status(po_id)` function. PO-1001 is unpaid in this fixture. Its
schema and function will be registered alongside the purchase-order lookup;
both accept the same strict `po_id` input model. No HTTP service, database,
payment action, or new dependency is introduced. The existing loop should need
no changes because it dispatches through the registry.

Source creation, direct/registry execution, and payment-tool unit tests remain
pending learner implementation. Adding a second schema will increase request
context; its actual overhead and Phase 3 live cost remain unmeasured. Reported
estimated spend remains USD 0.00033100. No benchmark or optimization is claimed.

### Phase 3: two registered tools verified — 2026-10-29

The payment-tool instruction had not yet been applied when work resumed. Codex
added [payment_status.py](payment_status.py), registered its schema/function/input
model in [tool_registry.py](tool_registry.py), and added
[test_payment_status.py](test_payment_status.py). The fixture returns PO-1001 as
unpaid, with amount paid 0 INR. Unknown PO IDs raise locally and are converted
to generic execution errors by the registry. Both tools use the same strict
`po_id` input model. No external payment service is contacted.

The loop did not change. A new test in
[test_agent_limits.py](test_agent_limits.py) supplies a mocked response requesting
both registered functions, verifies both are actually executed locally, and
checks that their successful results carry distinct matching IDs in the next
request. The final answer is mocked, so this validates orchestration, not live
model routing or answer quality. Direct function and registration tests were
added as well.

Validation: `python -m pytest -q -p no:cacheprovider` — **30 passed in 4.24s**.
No failures reported in this step. No live API call, credential access, or new
dependency was needed. Usage, latency, and cost for a live two-tool Phase 3 run
remain unmeasured. Reported cumulative estimated spend remains USD 0.00033100.
Adding a schema has context overhead; no optimization savings are claimed.

Learner experiment: run `execute_tool('get_payment_status', {'po_id': 'PO-1001'})`
locally, then inspect `test_two_registered_tools_in_one_round`. It demonstrates
two Python function executions between two mocked LLM requests. Next: prepare
the live runner and usage/latency/cost reporting before a paid trial. Phase 3
remains in progress; Phase 4 is not approved.

### Phase 3 runner and usage reporting — 2026-10-29

The learner created [agent_runner.py](agent_runner.py) and
[test_agent_runner.py](test_agent_runner.py): the runner loads local configuration,
opens one SDK client with retries disabled and a 30-second timeout, and calls
`run_agent` with four iterations and a 3,000-token soft budget. It asks for
PO-1001's supplier, total amount, and payment status, then prints the answer and
whole-run latency. The startup tests mock the loop and configuration, including
the missing-key path. Live execution has not been reported.

At the learner's explicit request, Codex added per-request `perf_counter` timing
and cost reporting in [agent_loop.py](agent_loop.py). Cost is printed after usage
is reported and before the budget guard, so a request that reaches the threshold
is still accounted for. Each uncached request estimates USD cost using the
short-prompt Haiku 5.5 rates checked on 2026-10-29 against the linked Anthropic
model documentation above: USD 0.10 per million input and USD 0.50 per million
output tokens. Estimated cumulative cost is maintained within a run only.

The basic estimator deliberately reports cost unavailable for cached usage rather
than applying ordinary input rates. Once that happens, subsequent uncached
request costs can still print, but a partial amount is not presented as the full
run total. Longer-prompt pricing tiers, taxes, conversion, persisted spending,
and failed API requests without reported usage are outside this estimator.

Tests use controlled clock values to verify separate 1.25-second and 0.75-second
mock request latencies and fixture-derived costs of USD 0.00000350 and
USD 0.00000700, totaling USD 0.00001050. Additional assertions verify cached
usage does not produce an incomplete run-cost estimate. These values are test
fixtures, not measured API performance or spending.

Validation: `python -m pytest -q -p no:cacheprovider` — **33 passed in 3.34s**;
`git diff --check` passed. No test failures, live API calls, or credential reads
occurred in this step. The source's broad error handler and soft-budget limits
remain as previously documented. Reported cumulative estimated live spend is
still USD 0.00033100. No optimization benchmark or savings claim is added.

Next learner experiment: run `python agent_runner.py` once, inspect the iteration
stop reasons, tool results through the mocked tests, returned answer, per-call
usage/cost, and total runtime. Record actual output before declaring Phase 3
complete; Phase 4 remains unapproved.

### Phase 3 live validation and completion — 2026-10-29

**Status:** Phase 3 complete: implementation, 33 offline tests, and one successful
learner-run live trial. GitHub commit/push is the next learner checkpoint. Phase 4
requires explicit approval. This entry supersedes earlier in-progress notes.

The learner ran `python agent_runner.py` and supplied the terminal output:

| Iteration | Stop reason | Input tokens | Output tokens | LLM latency | Estimated USD |
| --- | --- | --- | --- | --- | --- |
| 1 | tool_use | 632 | 129 | 3.08 seconds | 0.00012770 |
| 2 | end_turn | 945 | 74 | 1.08 seconds | 0.00013150 |
| Total | Completed | 1577 | 203 | 4.16 seconds summed LLM time | 0.00025920 |

Both requests reported zero cache creation/read and thinking tokens. The run used
**1,780 tokens** against its 3,000-token soft threshold and finished in **4.34
seconds** overall. The roughly 0.18-second difference from summed request times
includes client setup/teardown, local execution, printing, and other processing;
these timings are rounded, and the difference is not a measurement of tool time
alone. The four-iteration cap was not reached.

The reported final answer correctly states the fictional fixture values:
supplier Demo Office Supplies, total INR 15,000, unpaid, amount paid INR 0.
The expected user question and both schemas were sent; after the first assistant
tool-use response, the loop appended linked tool results and obtained this final
answer on the next request. Terminal logs do not expose individual live tool
names, arguments, or results, so exact live routing cannot be independently
reconstructed from this excerpt; the earlier offline tests verify two-tool
execution and protocol construction. Persistent per-tool tracing belongs later.

Cost check: `(1577 * 0.10 + 203 * 0.50) / 1,000,000 = USD 0.00025920`.
Across seven distinct reported API requests from all phases, cumulative estimated
live spend is now **USD 0.00059020** (prior USD 0.00033100 plus this run). Unreported
activity, taxes, and currency conversion remain unknown. Codex made no live call.

No failure occurred in this live trial. The soft budget can overshoot after a
request and rejects answers at its threshold; cached-cost estimation and detailed
tool-error diagnostics remain limited as documented. No before/after experiment
has run, and no optimization claim or benchmark row is added.

The learner experiment for Phase 3 is complete: inspect the two stop reasons,
per-request usage, final fixture values, and whole-run time. A further exercise
can debug the existing mocked repeated-tool test, observing history growth
without spending credits. Commit/push this phase before beginning integrations.

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
