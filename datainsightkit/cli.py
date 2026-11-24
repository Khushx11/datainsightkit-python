import argparse
from pathlib import Path
from .export_html import render_html
from .export_json import render_json
from .ingest import read_csv
from .report import analyse

def main(argv=None):
    parser = argparse.ArgumentParser(description="Profile a local CSV and write an HTML or JSON report.")
    parser.add_argument("csv", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    renderers = {".html": render_html, ".json": render_json}
    if args.output.suffix.lower() not in renderers:
        parser.error("output must end in .html or .json")
    if args.csv.resolve() == args.output.resolve():
        parser.error("input and output must be different files")
    try:
        report = analyse(*read_csv(args.csv))
        rendered = renderers[args.output.suffix.lower()](report)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(rendered)
    except (OSError, ValueError) as error:
        parser.exit(1, f"datainsightkit: {error}\n")
    print(f"Wrote {args.output}")
