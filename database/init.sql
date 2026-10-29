BEGIN;

CREATE TABLE IF NOT EXISTS public.purchase_orders (
    po_id TEXT PRIMARY KEY,
    supplier TEXT NOT NULL,
    total_amount NUMERIC(12, 2) NOT NULL CHECK (total_amount >= 0),
    currency CHAR(3) NOT NULL,
    status TEXT NOT NULL,
    invoice_id TEXT NOT NULL
);

INSERT INTO public.purchase_orders (
    po_id,
    supplier,
    total_amount,
    currency,
    status,
    invoice_id
)
VALUES (
    'PO-1001',
    'Demo Office Supplies',
    15000.00,
    'INR',
    'approved',
    'INV-2001'
)
ON CONFLICT (po_id) DO NOTHING;

COMMIT;