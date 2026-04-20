"""CLI: fetch last N messages from a Tchap/Matrix room.

Usage:
    python fetch_tchap.py <room_id> [-n 200] [-o output.json]

Env vars required:
    TCHAP_BOT_SSPHUB_MATRIX_ID
    TCHAP_BOT_SSPHUB_PWD
"""

import argparse
import json
import sys

from src.tchap_agent import fetch_messages


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch the last N messages from a Tchap/Matrix room and export as JSON."
    )
    parser.add_argument("room_id", help="Matrix room ID")
    parser.add_argument("-n", "--limit", type=int, default=300)
    parser.add_argument("-o", "--output", help="Output file (default: export)")
    args = parser.parse_args()

    print(
        f"Fetching last {args.limit} messages from {args.room_id}...", file=sys.stderr
    )
    messages = fetch_messages(args.room_id, args.limit)
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
