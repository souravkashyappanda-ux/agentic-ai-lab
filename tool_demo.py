import json
import os
from time import perf_counter

from anthropic import Anthropic
from dotenv import load_dotenv

from purchase_order import PURCHASE_ORDER_TOOL, get_purchase_order


def main() -> None:
    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY is missing.")
        return

    messages = [
        {
            "role": "user",
            "content": (
                "Use get_purchase_order to retrieve PO-1001. "
                "What are its supplier and total amount?"
            ),
        }
    ]
    with Anthropic(
        api_key=api_key,
        max_retries=0,
        timeout=30.0,
    ) as client:
        start = perf_counter()

        response = client.messages.create(
            model="claude-haiku-5-5",
            max_tokens=256,
            thinking={"type": "disabled"},
            tools=[PURCHASE_ORDER_TOOL],
            messages=messages,
        )

        elapsed = perf_counter() - start

    if response.stop_reason not in ("tool_use", "end_turn"):
        raise RuntimeError(
            f"Unexpected stop reason: {response.stop_reason}"
        )
    
    tool_results = []
 
    print(f"Model: {response.model}")
    print(f"Stop reason: {response.stop_reason}")

    for block in response.content:
        if block.type == "text":
            print(f"Text: {block.text}")
        elif block.type == "tool_use":
            print(f"Tool name: {block.name}")
            print(f"Arguments: {block.input}")
            print(f"Tool-use ID: {block.id}")
            if block.name != "get_purchase_order":
                raise ValueError(f"Unknown tool: {block.name}")

            arguments = block.input

            if not isinstance(arguments, dict):
                raise ValueError("Tool arguments must be a dictionary.")

            if set(arguments) != {"po_id"}:
                raise ValueError("Tool requires exactly one argument: po_id.")

            if not isinstance(arguments["po_id"], str):
                raise ValueError("po_id must be a string.")

            result = get_purchase_order(po_id=arguments["po_id"])
            print(f"Local tool result: {result}")

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                }
            )

    usage = response.usage
    print(f"Usage: {usage.model_dump()}")
    print(f"Request latency: {elapsed:.2f} seconds")

    # Same short-prompt pricing assumptions as the Phase 1 example.
    estimated_cost = (
        usage.input_tokens * 0.10
        + usage.output_tokens * 0.50
    ) / 1_000_000
    print(f"Estimated request cost: ${estimated_cost:.8f}")


    if response.stop_reason != "tool_use":
        return

    messages.append(
        {
            "role": "assistant",
            "content": response.content,
        }
    )
    messages.append(
        {
            "role": "user",
            "content": tool_results,
        }
    )
    with Anthropic(
        api_key=api_key,
        max_retries=0,
        timeout=30.0,
    ) as client:
        start = perf_counter()

        final_response = client.messages.create(
            model="claude-haiku-5-5",
            max_tokens=256,
            thinking={"type": "disabled"},
            tools=[PURCHASE_ORDER_TOOL],
            tool_choice={"type": "none"},
            messages=messages,
        )

        final_elapsed = perf_counter() - start

    print("\nFinal answer:")
    for block in final_response.content:
        if block.type == "text":
            print(block.text)

    print(f"Final stop reason: {final_response.stop_reason}")
    print(f"Second request usage: {final_response.usage.model_dump()}")
    print(f"Second request latency: {final_elapsed:.2f} seconds")

    second_cost = (
        final_response.usage.input_tokens * 0.10
        + final_response.usage.output_tokens * 0.50
    ) / 1_000_000

    print(f"Second request estimated cost: ${second_cost:.8f}")
    print(f"Total estimated run cost: ${estimated_cost + second_cost:.8f}")

    if final_response.stop_reason != "end_turn":
        print("The final response did not finish normally; inspect its stop reason.")


if __name__ == "__main__":
    main()
