import os
from time import perf_counter

from anthropic import Anthropic
from dotenv import load_dotenv

from po_agent.agent.loop import run_agent
from po_agent.db.purchase_orders import get_purchase_order_from_db
from po_agent.agent.registry import TOOL_FUNCTIONS


def main() -> None:
    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY is missing.")
        return

    question = (
        "For PO-1001, retrieve its supplier, total amount, "
        "and whether it has been paid. Use the available tools."
    )

    live_functions = {
        **TOOL_FUNCTIONS,
        "get_purchase_order": get_purchase_order_from_db,
    }

    start = perf_counter()

    with Anthropic(
        api_key=api_key,
        max_retries=0,
        timeout=30.0,
    ) as client:
        answer = run_agent(
            client=client,
            question=question,
            max_iterations=4,
            max_total_tokens=3000,
            tool_functions=live_functions,
        )

    elapsed = perf_counter() - start

    print("\nFinal answer:")
    print(answer)
    print(f"Total run latency: {elapsed:.2f} seconds")


if __name__ == "__main__":
    main()
