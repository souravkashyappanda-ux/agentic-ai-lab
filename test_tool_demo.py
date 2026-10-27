import json
from copy import deepcopy
from unittest.mock import MagicMock, patch

import pytest
from anthropic.types import Message

import tool_demo


def make_response(content, stop_reason):
    """Build an SDK response locally; no API request is made."""
    return Message(
        id="msg_test",
        type="message",
        role="assistant",
        model="claude-haiku-5-5",
        content=content,
        stop_reason=stop_reason,
        usage={"input_tokens": 10, "output_tokens": 5},
    )


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-test-key")
    monkeypatch.setattr(tool_demo, "load_dotenv", lambda: None)
    with patch("tool_demo.Anthropic") as constructor:
        mock_client = MagicMock()
        constructor.return_value.__enter__.return_value = mock_client
        yield mock_client


def test_tool_round_trip(client, capsys):
    first = make_response(
        [{"type": "tool_use", "id": "toolu_test",
          "name": "get_purchase_order", "input": {"po_id": "PO-1001"}}],
        "tool_use",
    )
    final = make_response(
        [{"type": "text", "text": "Demo Office Supplies: INR 15000."}],
        "end_turn",
    )
    responses = iter([first, final])
    requests = []

    def respond(**kwargs):
        # Snapshot history before the application appends more messages.
        requests.append(deepcopy(kwargs))
        return next(responses)

    client.messages.create.side_effect = respond

    tool_demo.main()

    assert len(requests) == 2
    assert len(requests[0]["messages"]) == 1
    history = requests[1]["messages"]
    assert [message["role"] for message in history] == [
        "user", "assistant", "user",
    ]
    assert history[1]["content"] == first.content
    result = history[2]["content"][0]
    assert result["type"] == "tool_result"
    assert result["tool_use_id"] == "toolu_test"
    assert json.loads(result["content"]) == {
        "po_id": "PO-1001",
        "supplier": "Demo Office Supplies",
        "total_amount": 15000,
        "currency": "INR",
        "status": "approved",
    }
    assert requests[1]["tool_choice"] == {"type": "none"}
    output = capsys.readouterr().out
    assert "Demo Office Supplies: INR 15000." in output
    assert "Total estimated run cost: $0.00000700" in output


def test_direct_answer_does_not_make_second_request(client):
    client.messages.create.return_value = make_response(
        [{"type": "text", "text": "No tool requested."}], "end_turn",
    )
    tool_demo.main()
    client.messages.create.assert_called_once()


@pytest.mark.parametrize(
    "name,arguments",
    [
        ("unknown_tool", {"po_id": "PO-1001"}),
        ("get_purchase_order", "PO-1001"),
        ("get_purchase_order", {}),
        ("get_purchase_order", {"po_id": "PO-1001", "extra": True}),
        ("get_purchase_order", {"po_id": 1001}),
    ],
)
def test_invalid_tool_request_does_not_execute(client, name, arguments):
    # A deliberately malformed response double tests defensive validation.
    block = MagicMock(type="tool_use", input=arguments, id="toolu_bad")
    block.name = name
    client.messages.create.return_value = MagicMock(
        stop_reason="tool_use", content=[block],
    )
    with patch("tool_demo.get_purchase_order") as execute:
        with pytest.raises(ValueError):
            tool_demo.main()
        execute.assert_not_called()
    client.messages.create.assert_called_once()


def test_truncated_response_does_not_execute(client):
    client.messages.create.return_value = make_response(
        [{"type": "tool_use", "id": "toolu_partial",
          "name": "get_purchase_order", "input": {"po_id": "PO-1001"}}],
        "max_tokens",
    )
    with patch("tool_demo.get_purchase_order") as execute:
        with pytest.raises(RuntimeError, match="Unexpected stop reason"):
            tool_demo.main()
        execute.assert_not_called()
    client.messages.create.assert_called_once()
