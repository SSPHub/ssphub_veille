"""
Unified entry point for the SSPHub veille pipeline.

    uv run veille.py extract              -f export.json -t Veille   # Tchap -> table
    uv run veille.py complete             -t Veille                  # rows -> LLM
    uv run veille.py extract-and-complete -t Veille                  # both, in order

A single, discoverable front door for the pipeline, with one `--help`.

Imports are done lazily inside each handler so that, e.g., running `complete`
does not require the extraction dependencies and vice-versa.
"""

import argparse


# --------------------------------------------------------------------------- #
# Shared argument helpers (keep the subcommands from drifting apart)
# --------------------------------------------------------------------------- #
def _add_file_arg(parser):
    parser.add_argument(
        "-f", "--file", default="export.json",
        help="Tchap json export to read (default: export.json).",
    )


def _add_table_arg(parser):
    parser.add_argument(
        "-t", "--table", default="Test",
        help="Grist table id (default: Test).",
    )


def _add_complete_args(parser):
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Cap the number of rows completed (handy for testing).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Completion step only: compute the updates and log them, but do not "
        "write them back to Grist.",
    )
    parser.add_argument(
        "--n-examples", type=int, default=15,
        help="Number of example category assignments sent to the LLM (default: 15).",
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
        limit=args.limit,
        dry_run=args.dry_run,
        n_examples=args.n_examples,
    )


def cmd_extract_and_complete(args):
    """Extract from a Tchap export, then complete the (new) rows in one go."""
    from src.veille_function import extract_and_add_to_veille
    from src.data.complete_veille import complete_veille

    extract_and_add_to_veille(input_conv_file_path=args.file, target_table=args.table)
    complete_veille(
        table_id=args.table,
        limit=args.limit,
        dry_run=args.dry_run,
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
    _add_file_arg(pe)
    _add_table_arg(pe)
    pe.set_defaults(func=cmd_extract)

    # ----- complete -----
    pc = sub.add_parser("complete", help="Complete existing Grist rows with an LLM.")
    _add_table_arg(pc)
    _add_complete_args(pc)
    pc.set_defaults(func=cmd_complete)

    # ----- extract-and-complete -----
    pa = sub.add_parser(
        "extract-and-complete",
        help="Extract from a Tchap export, then complete the rows with an LLM.",
        description="Runs `extract` then `complete` against the same table. "
        "Extraction always writes the new rows; --dry-run only affects the "
        "completion step.",
    )
    _add_file_arg(pa)
    _add_table_arg(pa)
    _add_complete_args(pa)
    pa.set_defaults(func=cmd_extract_and_complete)

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