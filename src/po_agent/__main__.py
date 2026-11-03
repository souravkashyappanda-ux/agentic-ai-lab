"""Module and console entry point for the live agent."""

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the purchase-order agent. Execution uses the paid Claude API."
    )
    parser.add_argument(
        "--log-requests", action="store_true",
        help="Print full Claude request payloads, including conversation and tool data.",
    )
    args = parser.parse_args()

    from po_agent.cli import main as run

    run(log_requests=args.log_requests)


if __name__ == "__main__":
    main()
