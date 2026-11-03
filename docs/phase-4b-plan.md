# Phase 4B–4C: combined PDF and payment HTTP milestone

The learner requested implementing PDF extraction and the mock payment service
together. This supersedes the earlier sequential plan, remains on
`phase-4-real-integrations`, and does not start Phase 5 or introduce RAG.

## Implemented sources

| Source | Implementation | Demo values |
| --- | --- | --- |
| Purchase order | PostgreSQL, read-only connection | PO-1001, INR 15000.00, invoice INV-2001 |
| Invoice | PyMuPDF reads `data/invoices/INV-2001.pdf` | PO-1001, INR 15500.00, page 1 |
| Payment | HTTPX calls the local FastAPI mock service | PO-1001, unpaid, INR 0.00 paid |

The combined no-LLM check calculated **INR 500.00** above the PO amount and
confirmed the supplier matches. This is a functional fixture result, not an
optimization benchmark or live LLM-quality evaluation.

## Code map

- `src/po_agent/tools/invoice.py`: validates invoice IDs, confines file access to
  the invoice directory, extracts labelled fields, and returns exact amount
  strings plus source filename/page numbers. It does not return raw PDF text.
- `scripts/create_demo_invoice.py`: creates the fictional text-based PDF and
  refuses to overwrite existing files. The 972-byte sample is included.
- `src/po_agent/models.py`: strict payment response contract shared by the HTTP
  client and server.
- `src/po_agent/services/mock_payments.py`: GET `/payments/{po_id}` and `/health`.
  Data remains fictional; there is no payment initiation endpoint.
- `src/po_agent/integrations/payments.py`: bounded GET response, five-second HTTP
  timeouts, response-model/PO-ID validation, no redirects, and explicit failures.
- `scripts/check_integrations.py`: registry-based PostgreSQL/PDF/HTTP check and
  Decimal comparison without Claude.
- Registry: three schemas and strict argument models. The live runner selects
  PostgreSQL and HTTP implementations; the invoice function reads the PDF.

## Scope and bounds

PDF extraction supports the controlled labelled demo format, not arbitrary
invoices. Missing/ambiguous fields, mismatched IDs, corrupt/encrypted files,
image-only pages, or unsupported amount/currency formats fail explicitly. It has
5 MiB file, 5-page, and 6,000-character extracted-text limits. These are bounded
input/output controls, not a complete defense against hostile PDF resource usage.
OCR is not implemented.

Payment responses are limited to 4,096 bytes and validated before being returned
to the agent. HTTP timeouts are per network phase, not a total wall-clock budget.
Low-level failures become generic registry errors; detailed per-tool tracing is
still future work. The local service deliberately has no external payment account
or real transaction data.

The runner retains four LLM iterations and a 768-token per-response cap (raised
after a live response was truncated at 256). Its soft
token threshold is now 6,000 to allow the additional schema/results and dependent
invoice lookup; this is an engineering allowance, not a measured improvement or
hard spending guarantee. Each new iteration resends accumulated context.

## Validation and next live trial

**93 offline tests passed**, including actual temporary PDF extraction, FastAPI
TestClient service behavior, HTTPX mock transports, PostgreSQL mocks, and a
three-request mocked agent flow with linked tool-use results. The mock answer
does not establish model correctness; tests independently verify the returned
source fields, source pages, and exact arithmetic.

A separate local check used real PostgreSQL, the generated PDF, and real loopback
HTTP to a temporary Uvicorn service. All three tools succeeded and the difference
was INR 500.00. The temporary server was stopped after verification. No Claude
request was made.

To repeat against a persistent local service, start Docker and run:

```powershell
docker compose up --wait db
python -m uvicorn po_agent.services.mock_payments:app --host 127.0.0.1 --port 8001
```

In another activated terminal:

```powershell
python -m scripts.check_integrations
```

After that check passes, one paid live trial is:

```powershell
python -m po_agent
```

Expected behavior: retrieve the PO, follow its linked invoice ID, get payment
status, explain the INR 500.00 mismatch, and cite `INV-2001.pdf`, page 1. Earlier
partial/failed live trials and their measurements are recorded in LEARNING.md.
The learner supplied the successful request-logging transcript: three Claude
calls, three successful tools, no tool failures, 4,024 tokens, USD 0.00066040
estimated cost, and 6.53 seconds overall. The final answer correctly identified
the INR 500.00 discrepancy, unpaid status, and invoice page reference. Phase 4
is complete. BENCHMARKS.csv remains header-only; this is a functional trial.

Library references: [PyMuPDF text extraction](https://pymupdf.readthedocs.io/en/latest/recipes-text.html),
[FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/),
[HTTPX transports](https://www.python-httpx.org/advanced/transports/).
