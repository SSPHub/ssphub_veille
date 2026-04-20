"""CLI entry point: fetch last N messages from a Tchap/Matrix room.

Usage:
    python fetch_tchap.py <room_id> [-n 200] [-o output.json] [--store /path/to/store]

Required environment variables:
    TCHAP_BOT_SSPHUB_MATRIX_ID  - bot Matrix user ID (e.g. @bot:matrix.agent.finances.tchap.gouv.fr)
    TCHAP_BOT_SSPHUB_PWD        - bot password

Note on E2E encryption:
    Tchap rooms are end-to-end encrypted. The crypto key store (--store) is
    persisted across runs so that session keys accumulate over time, enabling
    decryption of an increasing range of past messages.
"""

import argparse
import json
import sys
from pathlib import Path

from src.tchap_agent import fetch_messages
from src.tchap_agent.fetcher import _DEFAULT_STORE


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch the last N messages from a Tchap/Matrix room and export as JSON."
    )
    parser.add_argument(
        "room_id",
        help="Matrix room ID, e.g. !abc123:matrix.agent.finances.tchap.gouv.fr",
    )
    parser.add_argument(
        "-n",
        "--limit",
        type=int,
        default=100,
        help="Number of messages to fetch (default: 100)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Write JSON to this file path instead of stdout",
    )
    parser.add_argument(
        "--store",
        type=Path,
        default=_DEFAULT_STORE,
        help=f"Path for the E2E crypto key store (default: {_DEFAULT_STORE})",
    )
    args = parser.parse_args()

    print(
        f"Fetching last {args.limit} messages from {args.room_id}...", file=sys.stderr
    )
    messages = fetch_messages(args.room_id, args.limit, store_path=args.store)
    print(f"Retrieved {len(messages)} messages.", file=sys.stderr)

    payload = json.dumps(messages, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(payload)
        print(f"Saved to {args.output}", file=sys.stderr)
    else:
        print(payload)


if __name__ == "__main__":
    main()
