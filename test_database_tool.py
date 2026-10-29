from decimal import Decimal
from unittest.mock import patch

import pytest

from database_tool import get_purchase_order_from_db


@pytest.fixture
def database_cursor(monkeypatch):
    settings = {
        "DB_HOST": "127.0.0.1",
        "DB_PORT": "5433",
        "DB_NAME": "po_agent",
        "DB_USER": "agent_reader",
        "DB_PASSWORD": "fake-test-password",
    }

    for name, value in settings.items():
        monkeypatch.setenv(name, value)

    with (
        patch("database_tool.load_dotenv"),
        patch("database_tool.psycopg.connect") as connect,
    ):
        connection = connect.return_value.__enter__.return_value
        cursor = connection.cursor.return_value.__enter__.return_value
        yield cursor


def test_purchase_order_from_database(database_cursor):
    database_cursor.fetchone.return_value = {
        "po_id": "PO-1001",
        "supplier": "Demo Office Supplies",
        "total_amount": Decimal("15000.00"),
        "currency": "INR",
        "status": "approved",
        "invoice_id": "INV-2001",
    }

    result = get_purchase_order_from_db("PO-1001")

    assert result == {
        "po_id": "PO-1001",
        "supplier": "Demo Office Supplies",
        "total_amount": "15000.00",
        "currency": "INR",
        "status": "approved",
        "invoice_id": "INV-2001",
    }


def test_missing_purchase_order(database_cursor):
    database_cursor.fetchone.return_value = None

    with pytest.raises(ValueError, match="Purchase order not found"):
        get_purchase_order_from_db("PO-9999")


def test_po_id_is_bound_as_data(database_cursor):
    suspicious_id = "PO-1001' OR '1'='1"
    database_cursor.fetchone.return_value = None

    with pytest.raises(ValueError):
        get_purchase_order_from_db(suspicious_id)

    query, parameters = database_cursor.execute.call_args.args

    assert "WHERE po_id = %s" in query
    assert suspicious_id not in query
    assert parameters == (suspicious_id,)