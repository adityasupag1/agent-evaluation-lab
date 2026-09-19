from __future__ import annotations

import argparse
import json
from pathlib import Path

from .agent import load_agent_spec
from .core import evaluate_file, report
from .html_report import render_html_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic command-line agent evaluations")
    parser.add_argument("task_file", type=Path)
    parser.add_argument("--output", type=Path, help="write the JSON report to this path")
    parser.add_argument("--html-output", type=Path, help="write a standalone HTML report to this path")
    parser.add_argument("--runs", type=int, default=1, help="repeat each selected task this many times")
    parser.add_argument("--agent-config", type=Path, help="run prompt-based tasks through this agent command template")
    parser.add_argument("--label", help="label this benchmark report for later comparison")
    parser.add_argument("--tag", action="append", dest="tags", default=[], help="run tasks matching this tag; repeat to match any selected tag")
    args = parser.parse_args()

    agent = load_agent_spec(args.agent_config) if args.agent_config else None
    results = evaluate_file(args.task_file, runs=args.runs, tags=args.tags, agent=agent)
    payload = report(results, agent_name=agent.name if agent else None, label=args.label)
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")

    if args.html_output:
        args.html_output.parent.mkdir(parents=True, exist_ok=True)
        args.html_output.write_text(render_html_report(payload), encoding="utf-8")

    if not args.output and not args.html_output:
        print(rendered, end="")

    return 0 if payload["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
