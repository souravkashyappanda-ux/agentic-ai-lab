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
