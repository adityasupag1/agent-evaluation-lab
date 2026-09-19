from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any


def compare_report_files(paths: list[Path]) -> dict[str, Any]:
    if len(paths) < 2:
        raise ValueError("comparison requires at least two report files")

    entries = [_load_report(path) for path in paths]
    labels = [entry["label"] for entry in entries]
    if len(labels) != len(set(labels)):
        raise ValueError("comparison report labels must be unique")

    task_sets = [set(entry["task_ids"]) for entry in entries]
    common_tasks = set.intersection(*task_sets) if task_sets else set()
    same_task_set = all(task_set == task_sets[0] for task_set in task_sets[1:])

    reports = sorted(
        (
            {
                "label": entry["label"],
                "source": entry["source"],
                "total": entry["summary"]["total"],
                "passed": entry["summary"]["passed"],
                "failed": entry["summary"]["failed"],
                "pass_rate": entry["metrics"]["pass_rate"],
                "average_duration_seconds": entry["metrics"]["average_duration_seconds"],
                "task_count": len(entry["task_ids"]),
            }
            for entry in entries
        ),
        key=lambda item: (-float(item["pass_rate"]), float(item["average_duration_seconds"]), str(item["label"])),
    )

    return {
        "comparison": {
            "report_count": len(reports),
            "same_task_set": same_task_set,
            "common_task_count": len(common_tasks),
        },
        "reports": reports,
    }


def render_comparison_html(payload: dict[str, Any]) -> str:
    comparison = payload["comparison"]
    rows = []
    for report in payload["reports"]:
        rows.append(
            "<tr>"
            f"<td>{escape(str(report['label']))}</td>"
            f"<td>{report['passed']}/{report['total']}</td>"
            f"<td>{float(report['pass_rate']) * 100:.1f}%</td>"
            f"<td>{float(report['average_duration_seconds']):.3f}s</td>"
            f"<td>{report['task_count']}</td>"
            "</tr>"
        )

    note = (
        "All reports contain the same task set."
        if comparison["same_task_set"]
        else f"Task sets differ; {comparison['common_task_count']} task(s) are shared by every report."
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Agent Benchmark Comparison</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.5; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
    th, td {{ border-bottom: 1px solid #d0d7de; padding: 0.65rem; text-align: left; }}
    th {{ font-weight: 600; }}
    .note {{ padding: 0.8rem 1rem; border: 1px solid #d0d7de; border-radius: 8px; }}
  </style>
</head>
<body>
  <h1>Agent Benchmark Comparison</h1>
  <p class="note">{escape(note)}</p>
  <table>
    <thead>
      <tr><th>Label</th><th>Passed</th><th>Pass rate</th><th>Avg duration</th><th>Tasks</th></tr>
    </thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</body>
</html>
"""


def _load_report(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: report must be a JSON object")

    summary = payload.get("summary")
    metrics = payload.get("metrics")
    tasks = payload.get("tasks")
    if not isinstance(summary, dict) or not isinstance(metrics, dict) or not isinstance(tasks, list):
        raise ValueError(f"{path}: invalid benchmark report")

    total = summary.get("total")
    passed = summary.get("passed")
    failed = summary.get("failed")
    pass_rate = metrics.get("pass_rate")
    average_duration = metrics.get("average_duration_seconds")
    if not all(isinstance(value, int) and not isinstance(value, bool) and value >= 0 for value in (total, passed, failed)):
        raise ValueError(f"{path}: invalid summary counts")
    if passed + failed != total:
        raise ValueError(f"{path}: summary counts are inconsistent")
    if isinstance(pass_rate, bool) or not isinstance(pass_rate, (int, float)) or not 0 <= pass_rate <= 1:
        raise ValueError(f"{path}: invalid pass_rate")
    if isinstance(average_duration, bool) or not isinstance(average_duration, (int, float)) or average_duration < 0:
        raise ValueError(f"{path}: invalid average_duration_seconds")

    task_ids: list[str] = []
    for task in tasks:
        if not isinstance(task, dict) or not isinstance(task.get("task_id"), str) or not task["task_id"]:
            raise ValueError(f"{path}: invalid task summary")
        task_ids.append(task["task_id"])

    benchmark = payload.get("benchmark")
    label = None
    if isinstance(benchmark, dict):
        candidate = benchmark.get("label") or benchmark.get("agent")
        if isinstance(candidate, str) and candidate.strip():
            label = candidate.strip()
    if label is None:
        label = path.stem

    return {
        "label": label,
        "source": str(path),
        "summary": {"total": total, "passed": passed, "failed": failed},
        "metrics": {
            "pass_rate": float(pass_rate),
            "average_duration_seconds": float(average_duration),
        },
        "task_ids": task_ids,
    }
