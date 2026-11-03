import httpx
import pytest
from fastapi.testclient import TestClient

from po_agent.integrations import payments
from po_agent.services.mock_payments import app

PAYMENT = {
    "po_id": "PO-1001",
    "payment_status": "unpaid",
    "amount_paid": "0.00",
    "currency": "INR",
}


def test_mock_service_contract_and_missing_record():
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}
        response = client.get("/payments/PO-1001")
        assert response.status_code == 200
        assert response.json() == PAYMENT
        assert client.get("/payments/PO-9999").status_code == 404
        assert client.post("/payments/PO-1001").status_code == 405


def test_http_client_uses_expected_get_path():
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(200, json=PAYMENT)

    with httpx.Client(base_url="http://payments.test/", transport=httpx.MockTransport(respond)) as client:
        assert payments.get_payment_status_from_api("PO-1001", client=client) == PAYMENT

    assert len(requests) == 1
    assert requests[0].method == "GET"
    assert requests[0].url.path == "/payments/PO-1001"


@pytest.mark.parametrize("status", [302, 404, 500])
def test_http_errors_do_not_become_payment_data(status):
    with httpx.Client(
        base_url="http://payments.test/",
        transport=httpx.MockTransport(lambda request: httpx.Response(status)),
    ) as client:
        with pytest.raises(ValueError):
            payments.get_payment_status_from_api("PO-1001", client=client)


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {**PAYMENT, "amount_paid": 0},
        {**PAYMENT, "amount_paid": "NaN"},
        {**PAYMENT, "payment_status": "unknown"},
        {**PAYMENT, "po_id": "PO-9999"},
        {**PAYMENT, "extra": "unbounded data"},
    ],
)
def test_malformed_or_mismatched_payment_data(payload):
    with httpx.Client(
        base_url="http://payments.test/",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload)),
    ) as client:
        with pytest.raises(ValueError):
            payments.get_payment_status_from_api("PO-1001", client=client)


def test_invalid_json():
    with httpx.Client(
        base_url="http://payments.test/",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, content=b"not JSON")),
    ) as client:
        with pytest.raises(ValueError, match="invalid data"):
            payments.get_payment_status_from_api("PO-1001", client=client)


def test_oversized_response(monkeypatch):
    monkeypatch.setattr(payments, "MAX_RESPONSE_BYTES", 10)
    with httpx.Client(
        base_url="http://payments.test/",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, content=b"x" * 11)),
    ) as client:
        with pytest.raises(ValueError, match="size limit"):
            payments.get_payment_status_from_api("PO-1001", client=client)


def test_timeout_is_reported_as_tool_error():
    def fail(request):
        raise httpx.ReadTimeout("private network details", request=request)

    with httpx.Client(base_url="http://payments.test/", transport=httpx.MockTransport(fail)) as client:
        with pytest.raises(ValueError, match="unavailable"):
            payments.get_payment_status_from_api("PO-1001", client=client)


@pytest.mark.parametrize("po_id", ["../PO-1001", "PO-1001?x=1", "", 1001])
def test_invalid_id_never_reaches_http(po_id):
    def forbidden(request):
        pytest.fail("Invalid IDs must not trigger an HTTP request")

    with httpx.Client(base_url="http://payments.test/", transport=httpx.MockTransport(forbidden)) as client:
        with pytest.raises(ValueError, match="Invalid purchase-order"):
            payments.get_payment_status_from_api(po_id, client=client)
