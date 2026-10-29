import json
from unittest.mock import MagicMock, patch

from anthropic.types import Message

from agent_loop import run_agent


def test_agent_tool_round_trip(capsys):
    tool_request = Message(
        id="msg_tool",
        type="message",
        role="assistant",
        model="claude-haiku-5-5",
        stop_reason="tool_use",
        content=[
            {
                "type": "tool_use",
                "id": "toolu_test",
                "name": "get_purchase_order",
                "input": {"po_id": "PO-1001"},
            }
        ],
        usage={"input_tokens": 10, "output_tokens": 5},
    )

    final_response = Message(
        id="msg_final",
        type="message",
        role="assistant",
        model="claude-haiku-5-5",
        stop_reason="end_turn",
        content=[
            {"type": "text", "text": "The supplier is Demo Office Supplies."}
        ],
        usage={"input_tokens": 20, "output_tokens": 10},
    )

    client = MagicMock()
    client.messages.create.side_effect = [tool_request, final_response]

    with patch("agent_loop.perf_counter", side_effect=[10.0, 11.25, 12.0, 12.75]):
        answer = run_agent(client, "Who supplies PO-1001?")

    assert answer == "The supplier is Demo Office Supplies."
    assert client.messages.create.call_count == 2

    second_request = client.messages.create.call_args_list[1].kwargs
    history = second_request["messages"]

    assert [message["role"] for message in history] == [
        "user", "assistant", "user",
    ]

    tool_result = history[2]["content"][0]
    assert tool_result["tool_use_id"] == "toolu_test"
    assert tool_result["is_error"] is False
    assert json.loads(tool_result["content"])["data"]["po_id"] == "PO-1001"

    output = capsys.readouterr().out
    assert "Estimated request cost: $0.00000350" in output
    assert "Estimated request cost: $0.00000700" in output
    assert "Estimated run cost so far: $0.00001050" in output
    assert "LLM latency: 1.25 seconds" in output
    assert "LLM latency: 0.75 seconds" in output
