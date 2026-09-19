from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import evaluate_file, report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic command-line agent evaluations")
    parser.add_argument("task_file", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    payload = report(evaluate_file(args.task_file))
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")

    return 0 if payload["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
