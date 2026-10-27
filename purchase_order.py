def get_purchase_order(po_id: str) -> dict[str, str|int]:
    """Return a fictional purchase order for this learning exercise"""
    if po_id != "PO-1001":
        raise ValueError(f"Purchase Order not found: {po_id}")
    
    return {
        "po_id": "PO-1001",
        "supplier":"Demo Office Supplies",
        "total_amount":15000,
        "currency": "INR",
        "status":"approved",
    }

PURCHASE_ORDER_TOOL = {
    "name": "get_purchase_order",
    "description": (
        "Look up a fictional purchase order by ID. "
        "Returns supplier, total amount, currency, and approval status. "
        "Only PO-1001 exists in this demo."
    ),
    "input_schema":{
        "type":"object",
        "properties":{
            "po_id":{
                "type":"string",
                "description":"Purchase order identifier, such as PO-1001"
            }
        },
        "required":["po_id"],
        "additionalProperties": False,
    },
    
}