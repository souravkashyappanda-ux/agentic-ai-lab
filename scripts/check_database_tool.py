"""Check the database-backed registry route without making an LLM request."""

import argparse
import json

from po_agent.db.purchase_orders import get_purchase_order_from_db
from po_agent.agent.registry import TOOL_FUNCTIONS, execute_tool


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("po_id", nargs="?", default="PO-1001")
    args = parser.parse_args(argv)

    live_functions = {
        **TOOL_FUNCTIONS,
        "get_purchase_order": get_purchase_order_from_db,
    }
    result = execute_tool(
        "get_purchase_order",
        {"po_id": args.po_id},
        tool_functions=live_functions,
    )

    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
