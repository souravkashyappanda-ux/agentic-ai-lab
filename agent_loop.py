import json
from time import perf_counter

from anthropic import Anthropic

from tool_registry import TOOL_SCHEMAS, execute_tool


def run_agent(
    client: Anthropic,
    question: str,
    max_iterations: int = 4,
    max_total_tokens: int = 2000,
) -> str:
    if max_iterations < 1:
        raise ValueError("max_iterations must be at least 1.")
    if max_total_tokens < 1:
        raise ValueError("max_total_tokens must be at least 1.")

    total_tokens = 0
    total_estimated_cost: float | None = 0.0

    messages = [{"role": "user", "content": question}]

    for iteration in range(1, max_iterations + 1):
        request_start = perf_counter()
        response = client.messages.create(
            model="claude-haiku-5-5",
            max_tokens=min(256, max_total_tokens - total_tokens),
            thinking={"type": "disabled"},
            tools=TOOL_SCHEMAS,
            messages=messages,
        )
        request_latency = perf_counter() - request_start

        print(f"Iteration {iteration}: {response.stop_reason}")
        print(f"Usage: {response.usage.model_dump()}")
        
        usage = response.usage

        request_tokens = (
            usage.input_tokens
            + usage.output_tokens
            + (usage.cache_creation_input_tokens or 0)
            + (usage.cache_read_input_tokens or 0)
        )

        total_tokens += request_tokens

        print(f"Total run tokens: {total_tokens}/{max_total_tokens}")
        print(f"LLM latency: {request_latency:.2f} seconds")

        cache_tokens = (
            (usage.cache_creation_input_tokens or 0)
            + (usage.cache_read_input_tokens or 0)
        )

        if cache_tokens:
            # Cache pricing needs separate accounting.
            total_estimated_cost = None
            print("Cost estimate unavailable: cached usage detected.")
        else:
            # Haiku 5.5 short-prompt standard USD rates, checked 2026-10-29.
            request_cost = (
                usage.input_tokens * 0.10
                + usage.output_tokens * 0.50
            ) / 1_000_000

            print(f"Estimated request cost: ${request_cost:.8f}")

            if total_estimated_cost is not None:
                total_estimated_cost += request_cost

        if total_estimated_cost is not None:
            print(
                f"Estimated run cost so far: "
                f"${total_estimated_cost:.8f}"
            )

        if total_tokens >= max_total_tokens:
            raise RuntimeError("Agent token budget reached.")

        if response.stop_reason == "end_turn":
            return "\n".join(
                block.text
                for block in response.content
                if block.type == "text"
            )

        if response.stop_reason != "tool_use":
            raise RuntimeError(
                f"Unexpected stop reason: {response.stop_reason}"
            )

        tool_calls = [
            block
            for block in response.content
            if block.type == "tool_use"
        ]

        if not tool_calls:
            raise RuntimeError("tool_use response contained no tool calls.")

        # No further request is allowed to consume results on the last iteration.
        if iteration == max_iterations:
            break

        messages.append(
            {"role": "assistant", "content": response.content}
        )

        tool_results = []

        for block in tool_calls:
            result = execute_tool(block.name, block.input)

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                    "is_error": not result["ok"],
                }
            )

        messages.append(
            {"role": "user", "content": tool_results}
        )

    raise RuntimeError("Maximum agent iterations reached.")
