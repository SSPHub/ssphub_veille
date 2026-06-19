"""
Unified entry point for the SSPHub veille pipeline.

    uv run veille.py extract  -f export.json -t Veille      # Tchap -> fill table
    uv run veille.py complete -t Veille --only-empty        # complete rows w/ LLM

Each subcommand is also still available through its own script (`main.py` for
extraction); this just gives one discoverable front door with one `--help`.

Imports are done lazily inside each handler so that, e.g., running `complete`
does not require the extraction dependencies and vice-versa.
"""

import argparse
from datetime import datetime


def _parse_since(value):
    if value is None:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(
        f"Date invalide '{value}'. Formats acceptes : YYYY-MM-DD[ HH:MM[:SS]]"
    )


# --------------------------------------------------------------------------- #
# Subcommand handlers
# --------------------------------------------------------------------------- #
def cmd_extract(args):
    """Extract links from a Tchap export and add new rows to the Grist table."""
    from src.veille_function import extract_and_add_to_veille

    extract_and_add_to_veille(input_conv_file_path=args.file, target_table=args.table)


def cmd_complete(args):
    """Complete existing Grist rows (title, summary, category) with the LLM."""
    from src.data.complete_veille import complete_veille

    complete_veille(
        table_id=args.table,
        since=args.since,
        date_column=args.date_column,
        limit=args.limit,
        force=args.force,
        dry_run=args.dry_run,
        only_empty=args.only_empty,
        n_examples=args.n_examples,
    )


# --------------------------------------------------------------------------- #
# Parser
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="veille", description="SSPHub veille pipeline (extract + complete)."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ----- extract -----
    pe = sub.add_parser(
        "extract", help="Extract links from a Tchap export and add them to Grist."
    )
    pe.add_argument("-f", "--file", default="export.json", help="Tchap json export.")
    pe.add_argument("-t", "--table", default="Test", help="Grist table id.")
    pe.set_defaults(func=cmd_extract)

    # ----- complete -----
    pc = sub.add_parser(
        "complete", help="Complete existing Grist rows with an LLM."
    )
    pc.add_argument("-t", "--table", default="Test", help="Grist table id (default: Test).")
    pc.add_argument(
        "--since",
        type=_parse_since,
        default=None,
        help="Only process rows whose date column is on/after this date "
        "(YYYY-MM-DD[ HH:MM[:SS]]).",
    )
    pc.add_argument(
        "--date-column",
        default="Date",
        help="Column compared against --since (default: Date).",
    )
    pc.add_argument(
        "--limit", type=int, default=None, help="Cap the number of rows processed."
    )
    pc.add_argument(
        "--force",
        action="store_true",
        help="Reprocess rows that already have a Traitement value.",
    )
    pc.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute updates but do not write back to Grist.",
    )
    pc.add_argument(
        "--only-empty",
        action="store_true",
        help="Only fill empty cells; never overwrite an existing title/summary/"
        "category, and skip rows already complete (no LLM call).",
    )
    pc.add_argument(
        "--n-examples",
        type=int,
        default=15,
        help="Number of example category assignments sent to the LLM (default: 15).",
    )
    pc.set_defaults(func=cmd_complete)

    return parser


def main():
    args = build_parser().parse_args()
    try:
        args.func(args)
    except Exception as e:
        print(f"Fatal error in pipeline: {e}")
        raise


if __name__ == "__main__":
    main()