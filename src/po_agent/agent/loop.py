import json
from time import perf_counter

from anthropic import Anthropic

from po_agent.agent.registry import TOOL_SCHEMAS, execute_tool


def run_agent(
    client: Anthropic,
    question: str,
    max_iterations: int = 4,
    max_total_tokens: int = 2000,
    tool_functions: dict | None = None,
    max_output_tokens: int = 256,
    log_requests: bool = False,
) -> str:
    if max_iterations < 1:
        raise ValueError("max_iterations must be at least 1.")
    if max_total_tokens < 1:
        raise ValueError("max_total_tokens must be at least 1.")
    if max_output_tokens < 1:
        raise ValueError("max_output_tokens must be at least 1.")

    total_tokens = 0
    total_estimated_cost: float | None = 0.0
    total_input = 0
    total_output = 0
    total_cache_creation = 0
    total_cache_read = 0
    cache_creation_reported = True
    cache_read_reported = True
    tool_count = 0
    tool_failures = 0
    total_llm_latency = 0.0

    messages = [{"role": "user", "content": question}]

    for iteration in range(1, max_iterations + 1):
        output_limit = min(max_output_tokens, max_total_tokens - total_tokens)
        print(f"\n{'=' * 60}\nCLAUDE CALL {iteration}/{max_iterations}")
        print(f"Sending: {len(messages)} conversation messages + {len(TOOL_SCHEMAS)} tool schemas")
        print("History includes the original question and any earlier tool requests/results.")
        print(f"Output limit: {output_limit} tokens | Waiting for Claude...", flush=True)
        request = {
            "model": "claude-haiku-5-5",
            "max_tokens": output_limit,
            "thinking": {"type": "disabled"},
            "tools": TOOL_SCHEMAS,
            "messages": messages,
        }
        if log_requests:
            print(f"\n--- CLAUDE REQUEST {iteration}: SDK arguments as JSON ---")
            print(json.dumps(
                request, indent=2, ensure_ascii=True,
                default=lambda block: block.model_dump(mode="json", exclude_unset=True),
            ))
            print("--- END REQUEST (authentication headers are not logged) ---", flush=True)
        request_start = perf_counter()
        response = client.messages.create(**request)
        request_latency = perf_counter() - request_start
        total_llm_latency += request_latency

        print(f"Model: {response.model}")
        explanations = {
            "tool_use": "Claude requested tools; Python executes them locally.",
            "end_turn": "Claude finished its answer.",
            "max_tokens": "The response reached its output limit; it may be incomplete.",
        }
        print(f"Stop reason: {response.stop_reason}")
        print(explanations.get(response.stop_reason, "The loop cannot continue with this stop reason."))

        usage = response.usage
        total_input += usage.input_tokens
        total_output += usage.output_tokens
        total_cache_creation += usage.cache_creation_input_tokens or 0
        total_cache_read += usage.cache_read_input_tokens or 0
        cache_creation_reported &= usage.cache_creation_input_tokens is not None
        cache_read_reported &= usage.cache_read_input_tokens is not None
        print(f"Tokens this call: input={usage.input_tokens}, output={usage.output_tokens}")
        creation = usage.cache_creation_input_tokens
        read = usage.cache_read_input_tokens
        print(
            "Cache tokens this call: "
            f"created={creation if creation is not None else 'not reported'}, "
            f"read={read if read is not None else 'not reported'}"
        )

        request_tokens = (
            usage.input_tokens
            + usage.output_tokens
            + (usage.cache_creation_input_tokens or 0)
            + (usage.cache_read_input_tokens or 0)
        )

        total_tokens += request_tokens

        print(f"Total run tokens: {total_tokens}/{max_total_tokens} (soft stop threshold)")
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
            print(f"\n{'=' * 60}\nRUN SUMMARY")
            print(f"Claude calls: {iteration} | Tools executed: {tool_count} | Tool failures: {tool_failures}")
            print(f"Total tokens: {total_tokens} (input={total_input}, output={total_output}, "
                  f"cache created={total_cache_creation if cache_creation_reported else 'not fully reported'}, "
                  f"cache read={total_cache_read if cache_read_reported else 'not fully reported'})")
            print(f"Total LLM latency: {total_llm_latency:.2f} seconds")
            if total_estimated_cost is not None:
                print(f"Estimated run cost: ${total_estimated_cost:.8f} USD")
            else:
                print("Estimated run cost: unavailable (cache pricing not configured)")
            return "\n".join(
                block.text
                for block in response.content
                if block.type == "text"
            )

        if response.stop_reason == "max_tokens":
            partial_text = "\n".join(
                block.text for block in response.content if block.type == "text"
            )
            if partial_text:
                print("\nINCOMPLETE RESPONSE (not a final answer):")
                print(partial_text)
            raise RuntimeError(
                "Claude reached the per-call output limit. No truncated tool calls "
                "were executed. Increase max_output_tokens or request a shorter answer; "
                "no automatic retry was made."
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
            print(f"\nTOOL: {block.name} | Request ID: {block.id}")
            print(f"Arguments: {json.dumps(block.input, ensure_ascii=True)}")
            print("Python is validating arguments and executing the registered function...", flush=True)
            if tool_functions is None:
                result = execute_tool(block.name, block.input)
            else:
                result = execute_tool(
                    block.name,
                    block.input,
                    tool_functions=tool_functions,
                )

            tool_count += 1
            tool_failures += int(not result["ok"])
            print(f"Result: {'SUCCESS' if result['ok'] else 'FAILED'}")
            print(json.dumps(result, indent=2, ensure_ascii=True))
            if not result["ok"] and block.name == "get_payment_status":
                print("Check the payment service and run: python -m scripts.check_integrations")
                print("Start the demo service in another terminal: python -m uvicorn "
                      "po_agent.services.mock_payments:app --host 127.0.0.1 --port 8001")
            print("This result will be sent to Claude with the matching request ID.")
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
        print(f"\nAdded Claude's tool request(s) and {len(tool_results)} result(s) to history.")

    raise RuntimeError("Maximum agent iterations reached.")
