from pydantic import BaseModel, ConfigDict, Field, ValidationError

from po_agent.tools.invoice import INVOICE_ID_PATTERN, INVOICE_TOOL, read_invoice
from po_agent.tools.payment_status import PAYMENT_STATUS_TOOL, get_payment_status
from po_agent.tools.purchase_order import PURCHASE_ORDER_TOOL, get_purchase_order


class PurchaseOrderInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    po_id: str


class InvoiceInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    invoice_id: str = Field(pattern=INVOICE_ID_PATTERN)


TOOL_SCHEMAS = [
    PURCHASE_ORDER_TOOL,
    PAYMENT_STATUS_TOOL,
    INVOICE_TOOL,
]

TOOL_FUNCTIONS = {
    "get_purchase_order": get_purchase_order,
    "get_payment_status": get_payment_status,
    "read_invoice": read_invoice,
}

TOOL_INPUT_MODELS = {
    "get_purchase_order": PurchaseOrderInput,
    "get_payment_status": PurchaseOrderInput,
    "read_invoice": InvoiceInput,
}


def execute_tool(
    name: str,
    arguments: object,
    *,
    tool_functions: dict | None = None,
) -> dict[str, object]:
    functions = (
        TOOL_FUNCTIONS
        if tool_functions is None
        else tool_functions
    )

    if name not in functions or name not in TOOL_INPUT_MODELS:
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

    function = functions[name]

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
