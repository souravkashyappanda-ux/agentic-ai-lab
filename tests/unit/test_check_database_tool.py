import json
from decimal import Decimal
from unittest.mock import patch

import psycopg
import pytest

from scripts.check_database_tool import main


@pytest.fixture
def database(monkeypatch):
    for name, value in {
        "DB_HOST": "127.0.0.1",
        "DB_PORT": "5433",
        "DB_NAME": "po_agent",
        "DB_USER": "agent_reader",
        "DB_PASSWORD": "fake-test-password",
    }.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr("po_agent.db.purchase_orders.load_dotenv", lambda: None)

    with patch("po_agent.db.purchase_orders.psycopg.connect") as connect:
        connection = connect.return_value.__enter__.return_value
        cursor = connection.cursor.return_value.__enter__.return_value
        yield connect, cursor


def test_registry_check_queries_database_and_prints_json(database, capsys):
    connect, cursor = database
    cursor.fetchone.return_value = {
        "po_id": "PO-1001",
        "supplier": "Demo Office Supplies",
        "total_amount": Decimal("15000.00"),
        "currency": "INR",
        "status": "approved",
        "invoice_id": "INV-2001",
    }

    assert main([]) == 0

    result = json.loads(capsys.readouterr().out)
    assert result["ok"] is True
    assert result["data"]["total_amount"] == "15000.00"
    assert result["data"]["invoice_id"] == "INV-2001"
    assert connect.call_args.kwargs["user"] == "agent_reader"
    query, arguments = cursor.execute.call_args.args
    assert "WHERE po_id = %s" in query
    assert arguments == ("PO-1001",)


def test_registry_check_returns_error_for_missing_record(database, capsys):
    _, cursor = database
    cursor.fetchone.return_value = None

    assert main(["PO-9999"]) == 1

    assert cursor.execute.call_args.args[1] == ("PO-9999",)
    assert json.loads(capsys.readouterr().out) == {
        "ok": False,
        "error": "Tool execution failed.",
    }


def test_registry_check_does_not_expose_connection_error_details(database, capsys):
    connect, _ = database
    connect.side_effect = psycopg.OperationalError("private connection diagnostic")

    assert main([]) == 1

    output = capsys.readouterr().out
    assert "private connection diagnostic" not in output
    assert "fake-test-password" not in output
    assert json.loads(output) == {"ok": False, "error": "Tool execution failed."}
