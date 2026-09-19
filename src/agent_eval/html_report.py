from __future__ import annotations

from html import escape
from typing import Any


def render_html_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    metrics = payload.get("metrics", {})
    pass_rate = float(metrics.get("pass_rate", 0.0)) * 100
    benchmark = payload.get("benchmark") if isinstance(payload.get("benchmark"), dict) else {}
    benchmark_name = escape(str(benchmark.get("name") or "Unnamed benchmark"))
    benchmark_version = escape(str(benchmark.get("version") or "—"))
    benchmark_fingerprint = escape(str(benchmark.get("fingerprint") or "unavailable"))

    rows = []
    for task in payload.get("tasks", []):
        rows.append(
            "<tr>"
            f"<td>{escape(str(task['task_id']))}</td>"
            f"<td>{task['runs']}</td>"
            f"<td>{task['passed']}</td>"
            f"<td>{task['failed']}</td>"
            f"<td>{float(task['pass_rate']) * 100:.1f}%</td>"
            f"<td>{float(task['average_duration_seconds']):.3f}s</td>"
            "</tr>"
        )

    failure_rows = []
    for result in payload.get("results", []):
        if result.get("passed"):
            continue
        failure_rows.append(
            "<tr>"
            f"<td>{escape(str(result.get('task_id', '')))}</td>"
            f"<td>{result.get('run_index', 1)}</td>"
            f"<td>{escape(str(result.get('reason') or 'unknown failure'))}</td>"
            "</tr>"
        )

    task_table = "".join(rows) or '<tr><td colspan="6">No tasks selected.</td></tr>'
    failure_table = "".join(failure_rows) or '<tr><td colspan="3">No failures.</td></tr>'

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Agent Evaluation Report</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.5; }}
    .cards {{ display: flex; gap: 1rem; flex-wrap: wrap; margin: 1.5rem 0; }}
    .card {{ border: 1px solid #d0d7de; border-radius: 8px; padding: 1rem; min-width: 9rem; }}
    table {{ width: 100%; border-collapse: collapse; margin: 1rem 0 2rem; }}
    th, td {{ border-bottom: 1px solid #d0d7de; padding: 0.65rem; text-align: left; }}
    th {{ font-weight: 600; }}
    code {{ background: #f6f8fa; padding: 0.1rem 0.3rem; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>Agent Evaluation Report</h1>
  <p><strong>Benchmark:</strong> {benchmark_name} &nbsp; <strong>Version:</strong> {benchmark_version}<br><strong>Fingerprint:</strong> <code>{benchmark_fingerprint}</code></p>
  <div class="cards">
    <div class="card"><strong>Total runs</strong><br>{summary['total']}</div>
    <div class="card"><strong>Passed</strong><br>{summary['passed']}</div>
    <div class="card"><strong>Failed</strong><br>{summary['failed']}</div>
    <div class="card"><strong>Pass rate</strong><br>{pass_rate:.1f}%</div>
  </div>

  <h2>Task reliability</h2>
  <table>
    <thead><tr><th>Task</th><th>Runs</th><th>Passed</th><th>Failed</th><th>Pass rate</th><th>Avg duration</th></tr></thead>
    <tbody>{task_table}</tbody>
  </table>

  <h2>Failures</h2>
  <table>
    <thead><tr><th>Task</th><th>Run</th><th>Reason</th></tr></thead>
    <tbody>{failure_table}</tbody>
  </table>
</body>
</html>
"""
