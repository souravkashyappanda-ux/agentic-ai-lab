import os

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row


def get_purchase_order_from_db(po_id: str) -> dict[str, str]:
    load_dotenv()

    with psycopg.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        connect_timeout=5,
        options="-c statement_timeout=5000",
        row_factory=dict_row,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    po_id,
                    supplier,
                    total_amount,
                    currency,
                    status,
                    invoice_id
                FROM public.purchase_orders
                WHERE po_id = %s
                """,
                (po_id,),
            )

            row = cursor.fetchone()

    if row is None:
        raise ValueError(f"Purchase order not found: {po_id}")

    return {
        "po_id": row["po_id"],
        "supplier": row["supplier"],
        "total_amount": format(row["total_amount"], ".2f"),
        "currency": row["currency"],
        "status": row["status"],
        "invoice_id": row["invoice_id"],
    }