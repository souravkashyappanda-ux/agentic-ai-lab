"""Check PostgreSQL, invoice PDF, and mock payment HTTP without calling Claude."""

import argparse
import json
from decimal import Decimal

from dotenv import load_dotenv

from po_agent.agent.registry import TOOL_FUNCTIONS, execute_tool
from po_agent.db.purchase_orders import get_purchase_order_from_db
from po_agent.integrations.payments import get_payment_status_from_api


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("po_id", nargs="?", default="PO-1001")
    args = parser.parse_args(argv)
    load_dotenv()

    functions = {
        **TOOL_FUNCTIONS,
        "get_purchase_order": get_purchase_order_from_db,
        "get_payment_status": get_payment_status_from_api,
    }
    purchase_order = execute_tool(
        "get_purchase_order", {"po_id": args.po_id}, tool_functions=functions,
    )
    results = {"purchase_order": purchase_order}
    if not purchase_order["ok"]:
        print(json.dumps(results, indent=2))
        return 1

    po = purchase_order["data"]
    invoice = execute_tool(
        "read_invoice", {"invoice_id": po["invoice_id"]}, tool_functions=functions,
    )
    payment = execute_tool(
        "get_payment_status", {"po_id": args.po_id}, tool_functions=functions,
    )
    results.update(invoice=invoice, payment=payment)

    if not invoice["ok"] or not payment["ok"]:
        print(json.dumps(results, indent=2))
        return 1

    invoice_data = invoice["data"]
    if invoice_data["po_id"] != po["po_id"] or invoice_data["currency"] != po["currency"]:
        results["comparison"] = {"error": "Invoice PO or currency does not match the order."}
        print(json.dumps(results, indent=2))
        return 1

    results["comparison"] = {
        "currency": po["currency"],
        "invoice_minus_po": format(
            Decimal(invoice_data["total_amount"]) - Decimal(po["total_amount"]), ".2f",
        ),
        "supplier_matches": invoice_data["supplier"] == po["supplier"],
    }
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
