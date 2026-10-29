import os
from time import perf_counter

from anthropic import Anthropic
from dotenv import load_dotenv

from agent_loop import run_agent


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
        )

    elapsed = perf_counter() - start

    print("\nFinal answer:")
    print(answer)
    print(f"Total run latency: {elapsed:.2f} seconds")


if __name__ == "__main__":
    main()