from unittest.mock import patch

from agent_runner import main


def test_runner_success(capsys):
    with (
        patch("agent_runner.load_dotenv"),
        patch("agent_runner.os.getenv", return_value="fake-test-key"),
        patch("agent_runner.Anthropic") as constructor,
        patch("agent_runner.run_agent", return_value="PO-1001 is unpaid.") as run,
        patch("agent_runner.perf_counter", side_effect=[10.0, 12.0]),
    ):
        client = constructor.return_value.__enter__.return_value

        main()

        constructor.assert_called_once_with(
            api_key="fake-test-key",
            max_retries=0,
            timeout=30.0,
        )
        run.assert_called_once_with(
            client=client,
            question=(
                "For PO-1001, retrieve its supplier, total amount, "
                "and whether it has been paid. Use the available tools."
            ),
            max_iterations=4,
            max_total_tokens=3000,
        )

    output = capsys.readouterr().out
    assert "PO-1001 is unpaid." in output
    assert "Total run latency: 2.00 seconds" in output


def test_missing_key_does_not_create_client(capsys):
    with (
        patch("agent_runner.load_dotenv"),
        patch("agent_runner.os.getenv", return_value=None),
        patch("agent_runner.Anthropic") as constructor,
    ):
        main()

        constructor.assert_not_called()

    assert "ANTHROPIC_API_KEY is missing." in capsys.readouterr().out