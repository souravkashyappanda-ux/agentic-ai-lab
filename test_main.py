from unittest.mock import MagicMock, patch

from main import main


def test_main_success(capsys):
    response = MagicMock()
    response.content = [
        MagicMock(type="text", text="A purchase order requests goods.")
    ]
    response.model = "claude-haiku-5-5"
    response.stop_reason = "end_turn"
    response.usage.input_tokens = 21
    response.usage.output_tokens = 40

    with (
        patch("main.load_dotenv"),
        patch("main.os.getenv", return_value="fake-test-key"),
        patch("main.Anthropic") as mock_anthropic,
    ):
        client = mock_anthropic.return_value.__enter__.return_value
        client.messages.create.return_value = response

        main()

    output = capsys.readouterr().out

    assert "A purchase order requests goods." in output
    assert "Estimated request cost: $0.00002210" in output

    client.messages.create.assert_called_once_with(
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