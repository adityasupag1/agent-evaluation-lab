from __future__ import annotations

import argparse
import json
from pathlib import Path

from .comparison import compare_report_files, render_comparison_html


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare Agent Evaluation Lab benchmark reports")
    parser.add_argument("reports", nargs="+", type=Path, help="JSON benchmark reports to compare")
    parser.add_argument("--output", type=Path, help="write comparison JSON to this path")
    parser.add_argument("--html-output", type=Path, help="write comparison HTML to this path")
    args = parser.parse_args()

    payload = compare_report_files(args.reports)
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")

    if args.html_output:
        args.html_output.parent.mkdir(parents=True, exist_ok=True)
        args.html_output.write_text(render_comparison_html(payload), encoding="utf-8")

    if not args.output and not args.html_output:
        print(rendered, end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
