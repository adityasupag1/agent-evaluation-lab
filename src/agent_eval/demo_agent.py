from __future__ import annotations

import argparse
import sys
from pathlib import Path


def run_demo_agent(profile: str, prompt: str) -> int:
    if profile not in {"reference", "partial"}:
        raise ValueError("profile must be 'reference' or 'partial'")

    if prompt == "stdout-answer":
        print("42")
        return 0

    if prompt == "write-answer-file":
        Path("answer.txt").write_text("42", encoding="utf-8")
        return 0

    if prompt == "uppercase-fixture":
        source = Path("data/input.txt").read_text(encoding="utf-8")
        Path("output.txt").write_text(source.upper(), encoding="utf-8")
        return 0

    if prompt == "nested-artifact":
        if profile == "reference":
            target = Path("reports/result.txt")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("ready", encoding="utf-8")
        return 0

    if prompt == "stderr-diagnostic":
        if profile == "reference":
            print("diagnostic", file=sys.stderr)
        return 0

    print(f"unknown demo prompt: {prompt}", file=sys.stderr)
    return 2


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic fixture agent used by Agent Evaluation Lab examples"
    )
    parser.add_argument("--profile", choices=["reference", "partial"], required=True)
    parser.add_argument("--prompt", required=True)
    args = parser.parse_args()
    return run_demo_agent(args.profile, args.prompt)


if __name__ == "__main__":
    raise SystemExit(main())
