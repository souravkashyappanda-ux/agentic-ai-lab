def get_payment_status(po_id: str) -> dict[str, str | int]:
    """Return fictional payment data without contacting a service."""
    if po_id != "PO-1001":
        raise ValueError(f"Payment record not found: {po_id}")

    return {
        "po_id": po_id,
        "payment_status": "unpaid",
        "amount_paid": 0,
        "currency": "INR",
    }


PAYMENT_STATUS_TOOL = {
    "name": "get_payment_status",
    "description": (
        "Look up fictional payment status for a purchase order. "
        "Returns payment status, amount paid, and currency. "
        "Only PO-1001 exists in this demo. Does not make payments."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "po_id": {
                "type": "string",
                "description": "Purchase order identifier, such as PO-1001.",
            }
        },
        "required": ["po_id"],
        "additionalProperties": False,
    },
}
