import json

import pytest

from agent_eval.comparison import compare_report_files, render_comparison_html


def _write_report(path, *, label, passed, total, avg_duration, task_ids, fingerprint=None, benchmark_name=None, benchmark_version=None):
    payload = {
        "benchmark": {"label": label},
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
        },
        "metrics": {
            "pass_rate": passed / total if total else 0.0,
            "average_duration_seconds": avg_duration,
        },
        "tasks": [
            {
                "task_id": task_id,
                "runs": 1,
                "passed": 1,
                "failed": 0,
                "pass_rate": 1.0,
                "average_duration_seconds": avg_duration,
            }
            for task_id in task_ids
        ],
        "results": [],
    }
    if fingerprint is not None:
        payload["benchmark"]["fingerprint"] = fingerprint
    if benchmark_name is not None:
        payload["benchmark"]["name"] = benchmark_name
    if benchmark_version is not None:
        payload["benchmark"]["version"] = benchmark_version
    path.write_text(json.dumps(payload))


def test_compare_reports_orders_by_pass_rate_then_duration(tmp_path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    third = tmp_path / "third.json"
    _write_report(first, label="Agent A", passed=8, total=10, avg_duration=1.0, task_ids=["a", "b"])
    _write_report(second, label="Agent B", passed=9, total=10, avg_duration=2.0, task_ids=["a", "b"])
    _write_report(third, label="Agent C", passed=9, total=10, avg_duration=1.5, task_ids=["a", "b"])

    payload = compare_report_files([first, second, third])

    assert [item["label"] for item in payload["reports"]] == ["Agent C", "Agent B", "Agent A"]
    assert payload["comparison"] == {
        "report_count": 3,
        "same_task_set": True,
        "common_task_count": 2,
        "same_benchmark": None,
        "fingerprint_coverage": 0,
    }


def test_compare_reports_flags_different_task_sets(tmp_path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    _write_report(first, label="A", passed=1, total=1, avg_duration=1.0, task_ids=["shared", "only-a"])
    _write_report(second, label="B", passed=1, total=1, avg_duration=1.0, task_ids=["shared", "only-b"])

    payload = compare_report_files([first, second])

    assert not payload["comparison"]["same_task_set"]
    assert payload["comparison"]["common_task_count"] == 1


def test_compare_reports_requires_unique_labels(tmp_path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    _write_report(first, label="same", passed=1, total=1, avg_duration=1.0, task_ids=["a"])
    _write_report(second, label="same", passed=1, total=1, avg_duration=1.0, task_ids=["a"])

    with pytest.raises(ValueError, match="unique"):
        compare_report_files([first, second])


def test_render_comparison_html_escapes_labels():
    payload = {
        "comparison": {"report_count": 2, "same_task_set": True, "common_task_count": 1, "same_benchmark": None, "fingerprint_coverage": 0},
        "reports": [
            {
                "label": "<Agent>",
                "source": "a.json",
                "total": 1,
                "passed": 1,
                "failed": 0,
                "pass_rate": 1.0,
                "average_duration_seconds": 0.5,
                "task_count": 1,
            }
        ],
    }

    rendered = render_comparison_html(payload)

    assert "Agent Benchmark Comparison" in rendered
    assert "&lt;Agent&gt;" in rendered
    assert "<Agent>" not in rendered


def test_compare_reports_confirms_matching_fingerprints(tmp_path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    fingerprint = "sha256:" + "a" * 64
    _write_report(
        first,
        label="A",
        passed=1,
        total=1,
        avg_duration=1.0,
        task_ids=["shared"],
        fingerprint=fingerprint,
        benchmark_name="suite",
        benchmark_version="1.0.0",
    )
    _write_report(
        second,
        label="B",
        passed=1,
        total=1,
        avg_duration=1.0,
        task_ids=["shared"],
        fingerprint=fingerprint,
        benchmark_name="suite",
        benchmark_version="1.0.0",
    )

    payload = compare_report_files([first, second])

    assert payload["comparison"]["same_benchmark"] is True
    assert payload["comparison"]["fingerprint_coverage"] == 2
    assert all(report["fingerprint"] == fingerprint for report in payload["reports"])
    assert all(report["benchmark_name"] == "suite" for report in payload["reports"])


def test_compare_reports_flags_same_ids_with_different_fingerprints(tmp_path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    _write_report(
        first,
        label="A",
        passed=1,
        total=1,
        avg_duration=1.0,
        task_ids=["same-id"],
        fingerprint="sha256:" + "a" * 64,
    )
    _write_report(
        second,
        label="B",
        passed=1,
        total=1,
        avg_duration=1.0,
        task_ids=["same-id"],
        fingerprint="sha256:" + "b" * 64,
    )

    payload = compare_report_files([first, second])

    assert payload["comparison"]["same_task_set"] is True
    assert payload["comparison"]["same_benchmark"] is False


def test_comparison_html_warns_when_fingerprints_differ():
    payload = {
        "comparison": {
            "report_count": 2,
            "same_task_set": True,
            "common_task_count": 1,
            "same_benchmark": False,
            "fingerprint_coverage": 2,
        },
        "reports": [
            {
                "label": "A",
                "source": "a.json",
                "total": 1,
                "passed": 1,
                "failed": 0,
                "pass_rate": 1.0,
                "average_duration_seconds": 0.5,
                "task_count": 1,
                "benchmark_name": "suite",
                "benchmark_version": "1.0.0",
                "fingerprint": "sha256:" + "a" * 64,
            }
        ],
    }

    rendered = render_comparison_html(payload)

    assert "Benchmark fingerprints differ" in rendered
    assert "suite" in rendered
