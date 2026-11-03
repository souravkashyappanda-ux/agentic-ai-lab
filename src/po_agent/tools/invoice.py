"""Bounded extraction for the labelled, text-based demo invoice format."""

import os
import re
from decimal import Decimal
from pathlib import Path

import pymupdf

INVOICE_ID_PATTERN = r"^INV-[0-9]{1,12}$"
MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_PAGES = 5
MAX_TEXT_CHARACTERS = 6000
LABELS = {
    "Invoice ID": "invoice_id",
    "PO ID": "po_id",
    "Supplier": "supplier",
    "Currency": "currency",
    "Total Amount": "total_amount",
}


def invoice_directory() -> Path:
    return Path(os.getenv("INVOICE_DIR", "data/invoices")).resolve()


def read_invoice(invoice_id: str, *, invoice_dir: Path | None = None) -> dict:
    if not isinstance(invoice_id, str) or not re.fullmatch(INVOICE_ID_PATTERN, invoice_id):
        raise ValueError("Invalid invoice ID.")

    directory = invoice_directory() if invoice_dir is None else invoice_dir.resolve()
    path = (directory / f"{invoice_id}.pdf").resolve()
    if not path.is_relative_to(directory):
        raise ValueError("Invoice file must remain inside the invoice directory.")

    with path.open("rb") as stream:
        content = stream.read(MAX_FILE_BYTES + 1)
    if len(content) > MAX_FILE_BYTES:
        raise ValueError("Invoice exceeds the file-size limit.")

    fields = {}
    source_pages = set()
    character_count = 0
    with pymupdf.open(stream=content, filetype="pdf") as document:
        if not document.is_pdf or document.needs_pass:
            raise ValueError("Invoice must be an unencrypted PDF.")
        if not 1 <= document.page_count <= MAX_PAGES:
            raise ValueError("Invoice exceeds the page limit or has no pages.")

        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text", sort=True)
            character_count += len(text)
            if character_count > MAX_TEXT_CHARACTERS:
                raise ValueError("Invoice exceeds the extracted-text limit.")

            for line in text.splitlines():
                label, separator, value = line.partition(":")
                key = LABELS.get(label.strip())
                if separator and key:
                    if key in fields:
                        raise ValueError(f"Ambiguous invoice field: {key}")
                    fields[key] = value.strip()
                    source_pages.add(page_number)

    if not character_count:
        raise ValueError("Invoice has no readable text; OCR is not supported.")
    if any(not fields.get(key) for key in LABELS.values()):
        raise ValueError("Invoice is missing required labelled fields.")
    if fields["invoice_id"] != invoice_id:
        raise ValueError("Invoice ID does not match the requested document.")
    if not re.fullmatch(r"PO-[0-9]{1,12}", fields["po_id"]):
        raise ValueError("Invoice contains an invalid PO ID.")
    if not re.fullmatch(r"[A-Z]{3}", fields["currency"]):
        raise ValueError("Invoice contains an invalid currency.")
    if not re.fullmatch(r"[0-9]{1,10}\.[0-9]{2}", fields["total_amount"]):
        raise ValueError("Invoice amount must be a nonnegative decimal with two places.")
    if len(fields["supplier"]) > 200:
        raise ValueError("Invoice supplier field is too long.")

    fields["total_amount"] = format(Decimal(fields["total_amount"]), ".2f")
    return {
        **fields,
        "source_file": path.name,
        "source_pages": sorted(source_pages),
    }


INVOICE_TOOL = {
    "name": "read_invoice",
    "description": (
        "Extract invoice ID, PO ID, supplier, currency, total amount, and source "
        "pages from a local PDF by invoice ID. Supports labelled demo invoices; "
        "does not perform OCR. Use the invoice ID returned by a purchase-order lookup."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "invoice_id": {"type": "string", "pattern": INVOICE_ID_PATTERN},
        },
        "required": ["invoice_id"],
        "additionalProperties": False,
    },
}
