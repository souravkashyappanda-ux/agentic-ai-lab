from unittest.mock import MagicMock

import pytest

from po_agent.agent.registry import TOOL_FUNCTIONS, execute_tool


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


def test_custom_function_mapping():
    original_function = TOOL_FUNCTIONS["get_purchase_order"]
    database_lookup = MagicMock(
        return_value={
            "po_id": "PO-1001",
            "total_amount": "15000.00",
            "invoice_id": "INV-2001",
        }
    )

    result = execute_tool(
        "get_purchase_order",
        {"po_id": "PO-1001"},
        tool_functions={"get_purchase_order": database_lookup},
    )

    assert result == {"ok": True, "data": database_lookup.return_value}
    database_lookup.assert_called_once_with(po_id="PO-1001")
    assert TOOL_FUNCTIONS["get_purchase_order"] is original_function


def test_empty_mapping_does_not_fall_back_to_defaults():
    result = execute_tool(
        "get_purchase_order",
        {"po_id": "PO-1001"},
        tool_functions={},
    )

    assert result == {"ok": False, "error": "Unknown tool."}
