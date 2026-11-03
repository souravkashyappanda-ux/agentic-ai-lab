import os
from time import perf_counter

from anthropic import Anthropic
from dotenv import load_dotenv

from po_agent.agent.loop import run_agent
from po_agent.db.purchase_orders import get_purchase_order_from_db
from po_agent.integrations.payments import get_payment_status_from_api
from po_agent.agent.registry import TOOL_FUNCTIONS


def main(*, log_requests: bool = False) -> None:
    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY is missing.")
        return

    question = (
        "Check PO-1001. Retrieve the purchase order, read its linked invoice PDF, "
        "and get payment status. Compare the PO and invoice totals, identify "
        "discrepancies, and cite the invoice source. Use the available tools."
    )

    live_functions = {
        **TOOL_FUNCTIONS,
        "get_purchase_order": get_purchase_order_from_db,
        "get_payment_status": get_payment_status_from_api,
    }

    print("PURCHASE ORDER INTELLIGENCE AGENT")
    print(f"\nQuestion: {question}")
    print("\nData sources:")
    print("  get_purchase_order -> PostgreSQL (local seeded purchase orders)")
    print("  read_invoice       -> Local PDF (extracted fields and page references)")
    print("  get_payment_status -> Local mock payment service over real HTTP")
    print("Demo data is fictional. Claude chooses which tools to request.")
    print("Limits: 4 Claude calls; 768 output tokens/call; 6000-token soft stop threshold.")
    print("Cost estimates use configured USD rates; they are not billing totals.")
    if log_requests:
        print("Request logging ON: full prompts and tool data will appear below (no auth headers).")

    start = perf_counter()

    with Anthropic(
        api_key=api_key,
        max_retries=0,
        timeout=30.0,
    ) as client:
        try:
            answer = run_agent(
                client=client,
                question=question,
                max_iterations=4,
                max_total_tokens=6000,
                tool_functions=live_functions,
                max_output_tokens=768,
                log_requests=log_requests,
            )
        except RuntimeError as error:
            print(f"\nRUN STOPPED: {error}")
            print("No complete final answer was produced. Review the usage above before rerunning.")
            print(f"Total run latency: {perf_counter() - start:.2f} seconds")
            raise SystemExit(1) from None

    elapsed = perf_counter() - start

    print(f"\n{'=' * 60}\nFinal answer:")
    print(answer)
    print(f"Total run latency: {elapsed:.2f} seconds")


if __name__ == "__main__":
    main()
