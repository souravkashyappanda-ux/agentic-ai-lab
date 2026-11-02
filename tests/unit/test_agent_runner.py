from unittest.mock import patch

from po_agent.cli import main
from po_agent.db.purchase_orders import get_purchase_order_from_db
from po_agent.agent.registry import TOOL_FUNCTIONS


def test_runner_success(capsys):
    with (
        patch("po_agent.cli.load_dotenv"),
        patch("po_agent.cli.os.getenv", return_value="fake-test-key"),
        patch("po_agent.cli.Anthropic") as constructor,
        patch("po_agent.cli.run_agent", return_value="PO-1001 is unpaid.") as run,
        patch("po_agent.cli.perf_counter", side_effect=[10.0, 12.0]),
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
            tool_functions={
                **TOOL_FUNCTIONS,
                "get_purchase_order": get_purchase_order_from_db,
            },
        )

    output = capsys.readouterr().out
    assert "PO-1001 is unpaid." in output
    assert "Total run latency: 2.00 seconds" in output


def test_missing_key_does_not_create_client(capsys):
    with (
        patch("po_agent.cli.load_dotenv"),
        patch("po_agent.cli.os.getenv", return_value=None),
        patch("po_agent.cli.Anthropic") as constructor,
    ):
        main()

        constructor.assert_not_called()

    assert "ANTHROPIC_API_KEY is missing." in capsys.readouterr().out
