from __future__ import annotations

import argparse
import json
from pathlib import Path

from .validation import validate_benchmark_file


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate an Agent Evaluation Lab benchmark without executing tasks"
    )
    parser.add_argument("task_file", type=Path)
    parser.add_argument("--output", type=Path, help="write validation metadata as JSON")
    args = parser.parse_args()

    payload = validate_benchmark_file(args.task_file)
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
