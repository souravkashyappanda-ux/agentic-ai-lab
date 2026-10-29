BEGIN;

CREATE ROLE agent_reader
    LOGIN
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE;

GRANT CONNECT ON DATABASE po_agent TO agent_reader;

GRANT USAGE ON SCHEMA public TO agent_reader;

GRANT SELECT ON TABLE public.purchase_orders TO agent_reader;

COMMIT;BEGIN;

CREATE ROLE agent_reader
    LOGIN
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE;

GRANT CONNECT ON DATABASE po_agent TO agent_reader;

GRANT USAGE ON SCHEMA public TO agent_reader;

GRANT SELECT ON TABLE public.purchase_orders TO agent_reader;

COMMIT;