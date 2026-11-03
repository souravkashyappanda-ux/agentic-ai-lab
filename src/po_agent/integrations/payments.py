"""Read payment status over HTTP; never initiates payments."""

import json
import os
import re

import httpx
from pydantic import ValidationError

from po_agent.models import PaymentStatus

MAX_RESPONSE_BYTES = 4096


def _fetch_payment(client: httpx.Client, po_id: str) -> dict[str, str]:
    try:
        with client.stream("GET", f"payments/{po_id}") as response:
            if response.status_code == 404:
                raise ValueError("Payment record not found.")
            if response.status_code != 200:
                raise ValueError("Payment service returned an unsuccessful status.")

            content = bytearray()
            for chunk in response.iter_bytes(chunk_size=1024):
                if len(content) + len(chunk) > MAX_RESPONSE_BYTES:
                    raise ValueError("Payment response exceeds the size limit.")
                content.extend(chunk)
    except httpx.RequestError as error:
        raise ValueError("Payment service is unavailable.") from error

    try:
        payment = PaymentStatus.model_validate(json.loads(content))
    except (ValueError, ValidationError) as error:
        raise ValueError("Payment service returned invalid data.") from error
    if payment.po_id != po_id:
        raise ValueError("Payment response does not match the requested PO.")
    return payment.model_dump()


def get_payment_status_from_api(
    po_id: str, *, client: httpx.Client | None = None,
) -> dict[str, str]:
    if not isinstance(po_id, str) or not re.fullmatch(r"PO-[0-9]{1,12}", po_id):
        raise ValueError("Invalid purchase-order ID.")
    if client is not None:
        return _fetch_payment(client, po_id)

    base_url = os.getenv("PAYMENT_API_BASE_URL", "http://127.0.0.1:8001").rstrip("/") + "/"
    with httpx.Client(
        base_url=base_url,
        timeout=5.0,
        follow_redirects=False,
        trust_env=False,
    ) as http_client:
        return _fetch_payment(http_client, po_id)
