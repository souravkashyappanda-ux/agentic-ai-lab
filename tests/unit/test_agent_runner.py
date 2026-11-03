from unittest.mock import patch

import pytest

from po_agent.cli import main
from po_agent.db.purchase_orders import get_purchase_order_from_db
from po_agent.integrations.payments import get_payment_status_from_api
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
                "Check PO-1001. Retrieve the purchase order, read its linked invoice PDF, "
                "and get payment status. Compare the PO and invoice totals, identify "
                "discrepancies, and cite the invoice source. Use the available tools."
            ),
            max_iterations=4,
            max_total_tokens=6000,
            max_output_tokens=768,
            log_requests=False,
            tool_functions={
                **TOOL_FUNCTIONS,
                "get_purchase_order": get_purchase_order_from_db,
                "get_payment_status": get_payment_status_from_api,
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


def test_runner_reports_loop_failure_without_final_answer(capsys):
    with (
        patch("po_agent.cli.load_dotenv"),
        patch("po_agent.cli.os.getenv", return_value="fake-test-key"),
        patch("po_agent.cli.Anthropic"),
        patch("po_agent.cli.run_agent", side_effect=RuntimeError("Output limit reached.")),
        patch("po_agent.cli.perf_counter", side_effect=[10.0, 12.0]),
        pytest.raises(SystemExit) as stopped,
    ):
        main()
    assert stopped.value.code == 1
    output = capsys.readouterr().out
    assert "RUN STOPPED: Output limit reached." in output
    assert "Final answer:" not in output
