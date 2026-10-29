import pytest

from payment_status import get_payment_status
from tool_registry import execute_tool


def test_payment_status():
    assert get_payment_status("PO-1001") == {
        "po_id": "PO-1001",
        "payment_status": "unpaid",
        "amount_paid": 0,
        "currency": "INR",
    }


def test_unknown_payment_record():
    with pytest.raises(ValueError, match="Payment record not found"):
        get_payment_status("PO-9999")


def test_payment_tool_is_registered():
    assert execute_tool("get_payment_status", {"po_id": "PO-1001"}) == {
        "ok": True,
        "data": get_payment_status("PO-1001"),
    }
