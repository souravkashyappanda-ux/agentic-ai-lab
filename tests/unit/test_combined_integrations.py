import json
from copy import deepcopy
from decimal import Decimal
from functools import partial
from unittest.mock import MagicMock, patch

import httpx
from anthropic.types import Message
from fastapi.testclient import TestClient

from po_agent.agent.loop import run_agent
from po_agent.agent.registry import TOOL_FUNCTIONS
from po_agent.db.purchase_orders import get_purchase_order_from_db
from po_agent.integrations.payments import get_payment_status_from_api
from po_agent.services.mock_payments import app
from scripts.create_demo_invoice import create_demo_invoice


def response(content, stop_reason="tool_use"):
    return Message(
        id="msg_test", type="message", role="assistant", model="claude-haiku-5-5",
        content=content, stop_reason=stop_reason,
        usage={"input_tokens": 10, "output_tokens": 5},
    )


def call(call_id, name, arguments):
    return {"type": "tool_use", "id": call_id, "name": name, "input": arguments}


def test_agent_combines_database_pdf_and_payment_http(tmp_path, monkeypatch):
    create_demo_invoice(tmp_path / "INV-2001.pdf")
    monkeypatch.setenv("INVOICE_DIR", str(tmp_path))
    for key, value in {
        "DB_HOST": "127.0.0.1", "DB_PORT": "5433", "DB_NAME": "po_agent",
        "DB_USER": "agent_reader", "DB_PASSWORD": "fake-password",
    }.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr("po_agent.db.purchase_orders.load_dotenv", lambda: None)

    responses = iter([
        response([
            call("call_order", "get_purchase_order", {"po_id": "PO-1001"}),
            call("call_payment", "get_payment_status", {"po_id": "PO-1001"}),
        ]),
        response([call("call_invoice", "read_invoice", {"invoice_id": "INV-2001"})]),
        response([{
            "type": "text",
            "text": "Invoice INV-2001 exceeds the PO by INR 500.00; unpaid. Source: INV-2001.pdf, page 1.",
        }], "end_turn"),
    ])
    requests = []
    http_requests = []
    client = MagicMock()

    def respond(**kwargs):
        requests.append(deepcopy(kwargs))
        return next(responses)

    client.messages.create.side_effect = respond

    with (
        TestClient(app) as service,
        patch("po_agent.db.purchase_orders.psycopg.connect") as connect,
    ):
        cursor = connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = {
            "po_id": "PO-1001", "supplier": "Demo Office Supplies",
            "total_amount": Decimal("15000.00"), "currency": "INR",
            "status": "approved", "invoice_id": "INV-2001",
        }

        def send_http(request):
            http_requests.append(request)
            result = service.get(request.url.path)
            return httpx.Response(result.status_code, content=result.content)

        with httpx.Client(
            base_url="http://payments.test/", transport=httpx.MockTransport(send_http),
        ) as http_client:
            functions = {
                **TOOL_FUNCTIONS,
                "get_purchase_order": get_purchase_order_from_db,
                "get_payment_status": partial(get_payment_status_from_api, client=http_client),
            }
            answer = run_agent(
                client, "Compare PO-1001 with its invoice and payment status.",
                max_total_tokens=6000, tool_functions=functions,
            )

    assert len(requests) == 3
    assert [len(request["messages"]) for request in requests] == [1, 3, 5]
    po_result, payment_result = requests[1]["messages"][2]["content"]
    invoice_result = requests[2]["messages"][4]["content"][0]
    assert [po_result["tool_use_id"], payment_result["tool_use_id"], invoice_result["tool_use_id"]] == [
        "call_order", "call_payment", "call_invoice",
    ]
    assert all(not result["is_error"] for result in [po_result, payment_result, invoice_result])
    po = json.loads(po_result["content"])["data"]
    payment = json.loads(payment_result["content"])["data"]
    invoice = json.loads(invoice_result["content"])["data"]
    assert po["invoice_id"] == invoice["invoice_id"] == "INV-2001"
    assert Decimal(invoice["total_amount"]) - Decimal(po["total_amount"]) == Decimal("500.00")
    assert invoice["source_file"] == "INV-2001.pdf"
    assert invoice["source_pages"] == [1]
    assert payment["payment_status"] == "unpaid"
    assert payment["amount_paid"] == "0.00"
    assert http_requests[0].url.path == "/payments/PO-1001"
    assert cursor.execute.call_args.args[1] == ("PO-1001",)
    # Answer text is mocked; the independent source/result assertions above matter.
    assert "500.00" in answer


def test_http_failure_is_returned_to_model_as_linked_error():
    client = MagicMock()
    client.messages.create.side_effect = [
        response([call("call_payment", "get_payment_status", {"po_id": "PO-1001"})]),
        response([{"type": "text", "text": "Payment status could not be retrieved."}], "end_turn"),
    ]
    with httpx.Client(
        base_url="http://payments.test/",
        transport=httpx.MockTransport(lambda request: httpx.Response(503)),
    ) as http_client:
        functions = {
            "get_payment_status": partial(get_payment_status_from_api, client=http_client),
        }
        run_agent(client, "Has PO-1001 been paid?", tool_functions=functions)

    result = client.messages.create.call_args_list[1].kwargs["messages"][2]["content"][0]
    assert result["tool_use_id"] == "call_payment"
    assert result["is_error"] is True
    assert json.loads(result["content"]) == {"ok": False, "error": "Tool execution failed."}
