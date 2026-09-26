"""Command-line wrapper for the scripts in this repository."""

import argparse
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
SCRAPY_PROJECT = ROOT / "scraping" / "scrapy_scrape"
POSTS = SCRAPY_PROJECT / "posts.jsonl"
CHUNKS = ROOT / "cleaning" / "cleaned_chunks.jsonl"
DATABASE = ROOT / "chroma_db"


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="dgcr_llm",
        description="Scrape DGCR posts, clean chunks, index them, and ask questions.",
        epilog="Default paths refer to this checkout; custom paths refer to your current folder.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    defaults = argparse.ArgumentDefaultsHelpFormatter

    scrape = commands.add_parser(
        "scrape", help="Run the existing single-thread spider", formatter_class=defaults
    )
    scrape.add_argument(
        "--output", type=Path, default=POSTS,
        help="JSONL output file (replaces an existing file)",
    )

    clean = commands.add_parser(
        "clean", help="Convert scraped posts into text chunks", formatter_class=defaults
    )
    clean.add_argument("--input", type=Path, default=POSTS, help="Scraped posts JSONL")
    clean.add_argument("--output", type=Path, default=CHUNKS, help="Cleaned chunks JSONL")

    index = commands.add_parser(
        "index", help="Embed chunks and store them in Chroma", formatter_class=defaults
    )
    index.add_argument("--input", type=Path, default=CHUNKS, help="Cleaned chunks JSONL")
    index.add_argument("--db", type=Path, default=DATABASE, help="Chroma database directory")

    query = commands.add_parser(
        "query", help="Start the interactive Ollama question loop", formatter_class=defaults
    )
    query.add_argument("--db", type=Path, default=DATABASE, help="Chroma database directory")

    args = parser.parse_args(argv)
    # Resolve user paths before switching to the Scrapy project directory.
    for name in ("input", "output", "db"):
        if hasattr(args, name):
            setattr(args, name, getattr(args, name).expanduser().resolve())

    if hasattr(args, "input") and not args.input.is_file():
        parser.error(f"Input file does not exist: {args.input}")
    if args.command == "clean" and args.input == args.output:
        parser.error("Input and output must be different files.")
    if args.command == "query" and not args.db.is_dir():
        parser.error(f"Database directory does not exist: {args.db}. Run dgcr_llm index first.")

    cwd = ROOT
    if args.command == "scrape":
        command = ["-m", "scrapy", "crawl", "spider1", "-O", str(args.output)]
        cwd = SCRAPY_PROJECT
    elif args.command == "clean":
        command = [str(ROOT / "cleaning" / "clean_data.py"), str(args.input), str(args.output)]
    elif args.command == "index":
        command = [str(ROOT / "rag_setup" / "build_index.py"), str(args.input), str(args.db)]
    else:
        command = [str(ROOT / "rag_setup" / "rag_query.py"), str(args.db)]

    try:
        # Inherit the terminal so interactive input and script output work normally.
        return subprocess.run([sys.executable, "-u", *command], cwd=cwd).returncode
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
