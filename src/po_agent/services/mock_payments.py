"""A read-only mock service. Data is fictional even though transport is HTTP."""

from fastapi import FastAPI, HTTPException

from po_agent.models import PaymentStatus

app = FastAPI(title="Mock payment status service")

PAYMENTS = {
    "PO-1001": PaymentStatus(
        po_id="PO-1001",
        payment_status="unpaid",
        amount_paid="0.00",
        currency="INR",
    ),
}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/payments/{po_id}", response_model=PaymentStatus)
def payment_status(po_id: str) -> PaymentStatus:
    payment = PAYMENTS.get(po_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment record not found.")
    return payment
