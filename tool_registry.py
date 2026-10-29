from pydantic import BaseModel, ConfigDict, ValidationError

from payment_status import PAYMENT_STATUS_TOOL, get_payment_status
from purchase_order import PURCHASE_ORDER_TOOL, get_purchase_order


class PurchaseOrderInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    po_id: str


TOOL_SCHEMAS = [
    PURCHASE_ORDER_TOOL,
    PAYMENT_STATUS_TOOL,
]

TOOL_FUNCTIONS = {
    "get_purchase_order": get_purchase_order,
    "get_payment_status": get_payment_status,
}

TOOL_INPUT_MODELS = {
    "get_purchase_order": PurchaseOrderInput,
    "get_payment_status": PurchaseOrderInput,
}


def execute_tool(name: str, arguments: object) -> dict[str, object]:
    if name not in TOOL_FUNCTIONS:
        return {
            "ok": False,
            "error": "Unknown tool.",
        }

    input_model = TOOL_INPUT_MODELS[name]

    try:
        validated = input_model.model_validate(arguments)
    except ValidationError:
        return {
            "ok": False,
            "error": "Invalid tool arguments.",
        }

    function = TOOL_FUNCTIONS[name]

    try:
        result = function(**validated.model_dump())
    except Exception:
        # Do not expose internal exception details to the model.
        return {
            "ok": False,
            "error": "Tool execution failed.",
        }

    return {
        "ok": True,
        "data": result,
    }
