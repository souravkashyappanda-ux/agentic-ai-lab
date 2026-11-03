import json
from unittest.mock import patch

import pytest

from scripts.check_integrations import main

PO = {
    "po_id": "PO-1001", "invoice_id": "INV-2001", "supplier": "Demo Office Supplies",
    "total_amount": "15000.00", "currency": "INR",
}
INVOICE = {
    **PO, "total_amount": "15500.00", "source_file": "INV-2001.pdf", "source_pages": [1],
}
PAYMENT = {"po_id": "PO-1001", "payment_status": "unpaid", "amount_paid": "0.00", "currency": "INR"}


def test_combined_check_reports_exact_discrepancy(capsys):
    with patch("scripts.check_integrations.load_dotenv"), patch("scripts.check_integrations.execute_tool") as execute:
        execute.side_effect = [{"ok": True, "data": data} for data in [PO, INVOICE, PAYMENT]]
        assert main([]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["comparison"] == {
        "currency": "INR", "invoice_minus_po": "500.00", "supplier_matches": True,
    }
    assert execute.call_args_list[1].args[1] == {"invoice_id": "INV-2001"}


def test_combined_check_stops_after_database_error(capsys):
    with patch("scripts.check_integrations.load_dotenv"), patch("scripts.check_integrations.execute_tool") as execute:
        execute.return_value = {"ok": False, "error": "Tool execution failed."}
        assert main([]) == 1
        execute.assert_called_once()
    assert "comparison" not in json.loads(capsys.readouterr().out)


@pytest.mark.parametrize("field,value", [("po_id", "PO-9999"), ("currency", "USD")])
def test_combined_check_rejects_unrelated_invoice(field, value, capsys):
    with patch("scripts.check_integrations.load_dotenv"), patch("scripts.check_integrations.execute_tool") as execute:
        execute.side_effect = [
            {"ok": True, "data": PO},
            {"ok": True, "data": {**INVOICE, field: value}},
            {"ok": True, "data": PAYMENT},
        ]
        assert main([]) == 1
    assert "error" in json.loads(capsys.readouterr().out)["comparison"]
