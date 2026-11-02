import os
from time import perf_counter

from anthropic import Anthropic
from dotenv import load_dotenv


def main() -> None:
    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        print("ANTHROPIC_API_KEY is missing.")
        return

    # USD per million tokens for this model's short-prompt tier.
    input_rate = 0.10
    output_rate = 0.50

    with Anthropic(
        api_key=api_key,
        max_retries=0,
        timeout=30.0,
    ) as client:
        start = perf_counter()

        response = client.messages.create(
            model="claude-haiku-5-5",
            max_tokens=128,
            thinking={"type": "disabled"},
            messages=[
                {
                    "role": "user",
                    "content": "Explain a purchase order in one short sentence.",
                }
            ],
        )

        elapsed = perf_counter() - start

    print("\nClaude's response:")
    print(response)
    print("\nClaude's answer:")
    for block in response.content:
        if block.type == "text":
            print(block.text)

    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens

    estimated_cost = (
        input_tokens * input_rate
        + output_tokens * output_rate
    ) / 1_000_000

    print(f"\nModel: {response.model}")
    print(f"Stop reason: {response.stop_reason}")
    print(f"Usage: {response.usage.model_dump()}")
    print(f"Request latency: {elapsed:.2f} seconds")
    print(f"Estimated request cost: ${estimated_cost:.8f}")


if __name__ == "__main__":
    main()