"""Small shared data contracts for service boundaries."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PaymentStatus(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    po_id: str = Field(pattern=r"^PO-[0-9]{1,12}$")
    payment_status: Literal["unpaid", "partial", "paid"]
    amount_paid: str = Field(pattern=r"^[0-9]{1,10}\.[0-9]{2}$")
    currency: str = Field(pattern=r"^[A-Z]{3}$")
