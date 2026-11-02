"""Module and console entry point for the live agent."""

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the purchase-order agent. Execution uses the paid Claude API."
    )
    parser.parse_args()

    from po_agent.cli import main as run

    run()


if __name__ == "__main__":
    main()
