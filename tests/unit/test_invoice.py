from pathlib import Path

import pymupdf
import pytest

from po_agent.tools import invoice
from scripts.create_demo_invoice import DEMO_INVOICE_TEXT, create_demo_invoice


def write_pdf(path: Path, texts: list[str]) -> Path:
    with pymupdf.open() as document:
        for text in texts:
            document.new_page().insert_text((72, 72), text, fontsize=11)
        document.save(path)
    return path


def test_extract_invoice_fields_and_page_sources(tmp_path):
    text = DEMO_INVOICE_TEXT.replace("Supplier: Demo Office Supplies\n", "")
    write_pdf(tmp_path / "INV-2001.pdf", [text, "Supplier: Demo Office Supplies"])

    result = invoice.read_invoice("INV-2001", invoice_dir=tmp_path)

    assert result == {
        "invoice_id": "INV-2001",
        "po_id": "PO-1001",
        "supplier": "Demo Office Supplies",
        "currency": "INR",
        "total_amount": "15500.00",
        "source_file": "INV-2001.pdf",
        "source_pages": [1, 2],
    }
    assert "DEMO INVOICE" not in str(result)


def test_demo_generator_refuses_to_overwrite_existing_document(tmp_path):
    path = create_demo_invoice(tmp_path / "INV-2001.pdf")
    original = path.read_bytes()
    assert invoice.read_invoice("INV-2001", invoice_dir=tmp_path)["total_amount"] == "15500.00"
    with pytest.raises(FileExistsError):
        create_demo_invoice(path)
    assert path.read_bytes() == original


@pytest.mark.parametrize("invoice_id", ["../INV-2001", "INV-2001/other", "INV-2001?x=1", "", 2001])
def test_invalid_invoice_id_rejected(tmp_path, invoice_id):
    with pytest.raises(ValueError, match="Invalid invoice ID"):
        invoice.read_invoice(invoice_id, invoice_dir=tmp_path)


def test_missing_invoice(tmp_path):
    with pytest.raises(FileNotFoundError):
        invoice.read_invoice("INV-9999", invoice_dir=tmp_path)


@pytest.mark.parametrize(
    "old,new,error",
    [
        ("Invoice ID: INV-2001", "Invoice ID: INV-2002", "does not match"),
        ("Supplier: Demo Office Supplies", "", "missing required"),
        ("PO ID: PO-1001", "PO ID: arbitrary", "invalid PO"),
        ("Currency: INR", "Currency: inr", "invalid currency"),
        ("Total Amount: 15500.00", "Total Amount: NaN", "nonnegative decimal"),
        ("Total Amount: 15500.00", "Total Amount: -50.00", "nonnegative decimal"),
        ("Total Amount: 15500.00", "Total Amount: 15500.001", "nonnegative decimal"),
        ("Supplier: Demo Office Supplies", "Supplier: A\nSupplier: B", "Ambiguous"),
    ],
)
def test_invalid_or_ambiguous_fields(tmp_path, old, new, error):
    write_pdf(tmp_path / "INV-2001.pdf", [DEMO_INVOICE_TEXT.replace(old, new)])
    with pytest.raises(ValueError, match=error):
        invoice.read_invoice("INV-2001", invoice_dir=tmp_path)


def test_blank_pdf_requires_ocr_or_supported_text(tmp_path):
    write_pdf(tmp_path / "INV-2001.pdf", [""])
    with pytest.raises(ValueError, match="no readable text"):
        invoice.read_invoice("INV-2001", invoice_dir=tmp_path)


def test_corrupt_pdf(tmp_path):
    (tmp_path / "INV-2001.pdf").write_bytes(b"not a PDF")
    with pytest.raises(pymupdf.FileDataError):
        invoice.read_invoice("INV-2001", invoice_dir=tmp_path)


def test_password_protected_pdf_is_rejected(tmp_path):
    with pymupdf.open() as document:
        document.new_page().insert_text((72, 72), DEMO_INVOICE_TEXT)
        document.save(
            tmp_path / "INV-2001.pdf",
            encryption=pymupdf.PDF_ENCRYPT_AES_256,
            owner_pw="test-owner", user_pw="test-reader",
        )
    with pytest.raises(ValueError, match="unencrypted PDF"):
        invoice.read_invoice("INV-2001", invoice_dir=tmp_path)


def test_file_size_bound(tmp_path, monkeypatch):
    monkeypatch.setattr(invoice, "MAX_FILE_BYTES", 10)
    (tmp_path / "INV-2001.pdf").write_bytes(b"x" * 11)
    with pytest.raises(ValueError, match="file-size limit"):
        invoice.read_invoice("INV-2001", invoice_dir=tmp_path)


def test_page_count_bound(tmp_path, monkeypatch):
    monkeypatch.setattr(invoice, "MAX_PAGES", 1)
    write_pdf(tmp_path / "INV-2001.pdf", [DEMO_INVOICE_TEXT, "extra page"])
    with pytest.raises(ValueError, match="page limit"):
        invoice.read_invoice("INV-2001", invoice_dir=tmp_path)


def test_extracted_text_bound(tmp_path, monkeypatch):
    monkeypatch.setattr(invoice, "MAX_TEXT_CHARACTERS", 10)
    write_pdf(tmp_path / "INV-2001.pdf", [DEMO_INVOICE_TEXT])
    with pytest.raises(ValueError, match="extracted-text limit"):
        invoice.read_invoice("INV-2001", invoice_dir=tmp_path)


def test_configured_invoice_directory(tmp_path, monkeypatch):
    monkeypatch.setenv("INVOICE_DIR", str(tmp_path))
    write_pdf(tmp_path / "INV-2001.pdf", [DEMO_INVOICE_TEXT])
    assert invoice.read_invoice("INV-2001")["source_pages"] == [1]
