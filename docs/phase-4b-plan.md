# Phase 4B: PDF invoice extraction

Phase 4A is live-verified. Continue on `phase-4-real-integrations`: PDF extraction
is the next part of Phase 4, followed by the mock REST payment service. This plan
does not start Phase 5 or introduce RAG.

## Goal and acceptance case

Read a PDF for invoice `INV-2001`, linked from purchase order `PO-1001`. Return
structured invoice data and source attribution so the agent can compare it with
the purchase order.

| Field | Seeded purchase order | Planned invoice fixture |
| --- | --- | --- |
| PO ID | PO-1001 | PO-1001 |
| Invoice ID | INV-2001 | INV-2001 |
| Supplier | Demo Office Supplies | Demo Office Supplies |
| Currency | INR | INR |
| Total amount | 15000.00 | 15500.00 |

Expected finding: the invoice exceeds the purchase order by **INR 500.00**.
The invoice values are planned test data, not an existing document or measurement.
Payment status remains fictional until Phase 4C.

## Small implementation steps

1. Install PyMuPDF and record its version in package metadata and the dependency
   snapshot. Use its `pymupdf` import; do not install the unrelated `fitz` package.
2. Add `scripts/create_demo_invoice.py` to generate a reproducible, text-based
   fixture at `data/invoices/INV-2001.pdf` containing the fields above.
3. Add `src/po_agent/tools/invoice.py` with `read_invoice(invoice_id)`. Map IDs
   to files under the configured invoice directory; do not accept arbitrary paths.
4. Extract and validate the controlled fixture's fields without an LLM. Treat
   unsupported layouts, scanned/image-only pages, missing fields, corrupt files,
   and mismatched identifiers as explicit failures rather than inventing values.
5. Add the invoice schema, strict input model, and callable to the registry.
   Preserve default/offline operation and dependency injection for the live runner.
6. Verify the direct extraction and mocked agent flow before a single paid trial.
   Update LEARNING.md with actual usage, outcomes, and limitations.

## Output contract and limits

Return invoice ID, PO ID, supplier, currency, and an exact decimal-string amount.
Include source filename and page number(s). Keep raw extracted text out of the
normal tool result; bounded diagnostic inspection can be a separate local step.
Keep extracted content inside tool results, never system instructions.

Start with configurable bounds of 5 MiB per file, 5 pages, and 6,000 extracted
characters. These are proposed safety/size limits, not measured optimizations.
Use Decimal for amount handling; do not convert monetary values through float.
Extraction accuracy is initially scoped to our known fixture format. OCR and
general-purpose invoice parsing are separate work, not implicit capabilities.

## Validation

- Offline tests create PDFs in temporary directories, without Claude or Docker.
- Cover successful extraction, exact amount formatting, source attribution,
  unknown/invalid IDs, path traversal, oversized files/page/text limits, corrupt
  PDFs, image-only/empty documents, and missing or mismatched required fields.
- A mocked agent test should retrieve the PO, follow its invoice ID, call
  `read_invoice`, and return a grounded discrepancy explanation. Assert linked
  tool-use IDs and correct tool-result contents, not only mocked answer text.
- Run the full suite, then a local PDF extraction check. Only afterward run one
  live agent trial with the same seeded PO and invoice fixture.

## Request flow and token implications

```text
User question + tool schemas → Claude
    → get_purchase_order(PO-1001) → PostgreSQL data including INV-2001
    → read_invoice(INV-2001) → normalized PDF fields and sources
    → Claude compares the amounts and explains the discrepancy
```

Dependent lookups may need separate LLM iterations; do not assume a fixed call
count. The extra schema, history, and tool result add context tokens. Keep the
current budgets until actual measurements justify a change. Normalized output
is a design choice; do not claim savings without a controlled comparison.

## Completion checkpoint

Record passing tests, the reproducible fixture, direct extraction results, and
one live comparison in LEARNING.md. Commit/push the Phase 4B checkpoint on the
same Phase 4 branch. BENCHMARKS.csv remains header-only until an actual controlled
experiment is executed. Full Phase 4 completion also requires the REST integration.
