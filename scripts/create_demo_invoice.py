"""Generate the fictional invoice fixture without overwriting an existing file."""

from pathlib import Path

import pymupdf
from dotenv import load_dotenv

from po_agent.tools.invoice import invoice_directory

DEMO_INVOICE_TEXT = """DEMO INVOICE - fictional learning data
Invoice ID: INV-2001
PO ID: PO-1001
Supplier: Demo Office Supplies
Currency: INR
Total Amount: 15500.00
"""


def create_demo_invoice(output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with pymupdf.open() as document:
        page = document.new_page()
        page.insert_text((72, 72), DEMO_INVOICE_TEXT, fontsize=11)
        content = document.tobytes(garbage=4, deflate=True)
    with output_path.open("xb") as output:
        output.write(content)
    return output_path


def main() -> None:
    load_dotenv()
    path = create_demo_invoice(invoice_directory() / "INV-2001.pdf")
    print(f"Created fictional invoice: {path.name}")


if __name__ == "__main__":
    main()
