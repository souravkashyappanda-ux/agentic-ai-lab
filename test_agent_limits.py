import json
from unittest.mock import MagicMock, patch

import pytest
from anthropic.types import Message

from agent_loop import run_agent


def make_response(content, stop_reason="tool_use", **usage):
    """Construct a fake SDK response without contacting Claude."""
    return Message(
        id="msg_test",
        type="message",
        role="assistant",
        model="claude-haiku-5-5",
        stop_reason=stop_reason,
        content=content,
        usage={"input_tokens": 10, "output_tokens": 5, **usage},
    )


def tool_call(call_id, name="get_purchase_order"):
    return {
        "type": "tool_use",
        "id": call_id,
        "name": name,
        "input": {"po_id": "PO-1001"},
    }


def test_iteration_limit_does_not_execute_unusable_tool():
    client = MagicMock()
    client.messages.create.return_value = make_response([tool_call("call_1")])

    with patch("agent_loop.execute_tool") as execute:
        with pytest.raises(RuntimeError, match="Maximum agent iterations"):
            run_agent(client, "Get PO-1001.", max_iterations=1)
        execute.assert_not_called()

    client.messages.create.assert_called_once()


def test_token_budget_accumulates_across_requests():
    client = MagicMock()
    client.messages.create.side_effect = [
        make_response([tool_call("call_1")]),
        make_response([tool_call("call_2")]),
    ]

    with patch("agent_loop.execute_tool") as execute:
        execute.return_value = {"ok": True, "data": {"po_id": "PO-1001"}}
        with pytest.raises(RuntimeError, match="Agent token budget reached"):
            run_agent(client, "Get PO-1001.", max_total_tokens=30)
        execute.assert_called_once_with("get_purchase_order", {"po_id": "PO-1001"})

    # Each mock response consumes 15 tokens. The second reaches the threshold.
    assert client.messages.create.call_count == 2
    calls = client.messages.create.call_args_list
    assert calls[0].kwargs["max_tokens"] == 30
    assert calls[1].kwargs["max_tokens"] == 15


def test_cache_tokens_are_included_in_budget(capsys):
    client = MagicMock()
    client.messages.create.return_value = make_response(
        [tool_call("call_1")],
        cache_creation_input_tokens=7,
        cache_read_input_tokens=8,
    )

    with patch("agent_loop.execute_tool") as execute:
        with pytest.raises(RuntimeError, match="Agent token budget reached"):
            run_agent(client, "Get PO-1001.", max_total_tokens=30)
        execute.assert_not_called()

    # 10 base input + 5 output + 7 cache creation + 8 cache read = 30.
    client.messages.create.assert_called_once()
    output = capsys.readouterr().out
    assert "Cost estimate unavailable: cached usage detected." in output
    assert "Estimated run cost so far:" not in output


def test_cached_request_prevents_partial_run_cost_from_being_reported(capsys):
    client = MagicMock()
    client.messages.create.side_effect = [
        make_response([tool_call("call_cached")], cache_read_input_tokens=10),
        make_response([{"type": "text", "text": "Done."}], stop_reason="end_turn"),
    ]

    assert run_agent(client, "Get PO-1001.") == "Done."

    output = capsys.readouterr().out
    assert "Cost estimate unavailable: cached usage detected." in output
    assert "Estimated request cost: $0.00000350" in output
    assert "Estimated run cost so far:" not in output


def test_multiple_calls_return_success_and_error_together():
    client = MagicMock()
    first = make_response([
        tool_call("call_success"),
        tool_call("call_failure", name="unknown_tool"),
    ])
    final = make_response(
        [{"type": "text", "text": "One lookup succeeded; the other tool is unavailable."}],
        stop_reason="end_turn",
    )
    client.messages.create.side_effect = [first, final]

    answer = run_agent(client, "Perform these lookups.")

    assert "One lookup succeeded" in answer
    assert client.messages.create.call_count == 2
    history = client.messages.create.call_args_list[1].kwargs["messages"]
    assert [message["role"] for message in history] == ["user", "assistant", "user"]
    assert history[1]["content"] == first.content
    success, failure = history[2]["content"]
    assert success["tool_use_id"] == "call_success"
    assert success["is_error"] is False
    assert json.loads(success["content"])["data"]["supplier"] == "Demo Office Supplies"
    assert failure["tool_use_id"] == "call_failure"
    assert failure["is_error"] is True
    assert json.loads(failure["content"]) == {"ok": False, "error": "Unknown tool."}


def test_two_registered_tools_in_one_round():
    client = MagicMock()
    client.messages.create.side_effect = [
        make_response([
            tool_call("call_order"),
            tool_call("call_payment", name="get_payment_status"),
        ]),
        make_response(
            [{"type": "text", "text": "Demo Office Supplies: INR 15000, unpaid."}],
            stop_reason="end_turn",
        ),
    ]

    answer = run_agent(client, "Get the supplier, total, and payment status for PO-1001.")

    assert answer == "Demo Office Supplies: INR 15000, unpaid."
    assert client.messages.create.call_count == 2
    history = client.messages.create.call_args_list[1].kwargs["messages"]
    order_result, payment_result = history[2]["content"]
    assert order_result["tool_use_id"] == "call_order"
    assert payment_result["tool_use_id"] == "call_payment"
    assert order_result["is_error"] is False
    assert payment_result["is_error"] is False
    assert json.loads(order_result["content"])["data"]["total_amount"] == 15000
    assert json.loads(payment_result["content"])["data"]["payment_status"] == "unpaid"
    schemas = client.messages.create.call_args_list[0].kwargs["tools"]
    assert {schema["name"] for schema in schemas} == {
        "get_purchase_order", "get_payment_status",
    }


def test_repeated_tool_rounds_preserve_one_original_question():
    client = MagicMock()
    client.messages.create.side_effect = [
        make_response([tool_call("call_1")]),
        make_response([tool_call("call_2")]),
        make_response([{"type": "text", "text": "Done."}], stop_reason="end_turn"),
    ]

    assert run_agent(client, "Check PO-1001 twice.") == "Done."

    assert client.messages.create.call_count == 3
    history = client.messages.create.call_args_list[2].kwargs["messages"]
    assert len(history) == 5
    assert [message["role"] for message in history] == [
        "user", "assistant", "user", "assistant", "user",
    ]
    assert sum(message["content"] == "Check PO-1001 twice." for message in history) == 1
    assert history[2]["content"][0]["tool_use_id"] == "call_1"
    assert history[4]["content"][0]["tool_use_id"] == "call_2"


def test_truncated_response_does_not_execute_tools():
    client = MagicMock()
    client.messages.create.return_value = make_response(
        [tool_call("call_partial")], stop_reason="max_tokens",
    )

    with patch("agent_loop.execute_tool") as execute:
        with pytest.raises(RuntimeError, match="Unexpected stop reason: max_tokens"):
            run_agent(client, "Get PO-1001.")
        execute.assert_not_called()

    client.messages.create.assert_called_once()


def test_missing_tool_blocks_stops_instead_of_looping():
    client = MagicMock()
    client.messages.create.return_value = make_response([])

    with pytest.raises(RuntimeError, match="contained no tool calls"):
        run_agent(client, "Get PO-1001.")

    client.messages.create.assert_called_once()


@pytest.mark.parametrize("limits", [{"max_iterations": 0}, {"max_total_tokens": 0}])
def test_invalid_limits_rejected_before_request(limits):
    client = MagicMock()

    with pytest.raises(ValueError):
        run_agent(client, "Get PO-1001.", **limits)

    client.messages.create.assert_not_called()
