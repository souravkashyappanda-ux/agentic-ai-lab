import pytest

from tool_registry import execute_tool


def test_execute_known_tool():
    result = execute_tool("get_purchase_order", {"po_id": "PO-1001"})

    assert result == {
        "ok": True,
        "data": {
            "po_id": "PO-1001",
            "supplier": "Demo Office Supplies",
            "total_amount": 15000,
            "currency": "INR",
            "status": "approved",
        },
    }


@pytest.mark.parametrize(
    "name,arguments,expected_error",
    [
        ("unknown", {}, "Unknown tool."),
        ("get_purchase_order", "PO-1001", "Invalid tool arguments."),
        ("get_purchase_order", {}, "Invalid tool arguments."),
        (
            "get_purchase_order",
            {"po_id": "PO-1001", "extra": True},
            "Invalid tool arguments.",
        ),
        ("get_purchase_order", {"po_id": 1001}, "Invalid tool arguments."),
        ("get_purchase_order", {"po_id": "PO-9999"}, "Tool execution failed."),
    ],
)
def test_execute_tool_failure(name, arguments, expected_error):
    result = execute_tool(name, arguments)

    assert result == {"ok": False, "error": expected_error}