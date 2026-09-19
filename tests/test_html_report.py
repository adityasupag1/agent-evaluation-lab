from agent_eval.html_report import render_html_report


def test_html_report_renders_summary_and_escapes_content():
    payload = {
        "summary": {"total": 2, "passed": 1, "failed": 1},
        "metrics": {"pass_rate": 0.5},
        "tasks": [
            {
                "task_id": "<task>",
                "runs": 2,
                "passed": 1,
                "failed": 1,
                "pass_rate": 0.5,
                "average_duration_seconds": 0.125,
            }
        ],
        "results": [
            {
                "task_id": "<task>",
                "run_index": 2,
                "passed": False,
                "reason": "<mismatch>",
            }
        ],
    }

    rendered = render_html_report(payload)

    assert "Agent Evaluation Report" in rendered
    assert "50.0%" in rendered
    assert "&lt;task&gt;" in rendered
    assert "&lt;mismatch&gt;" in rendered
    assert "<task>" not in rendered


def test_html_report_shows_and_escapes_benchmark_provenance():
    payload = {
        "benchmark": {
            "name": "<suite>",
            "version": "1.0.0",
            "fingerprint": "sha256:" + "a" * 64,
        },
        "summary": {"total": 0, "passed": 0, "failed": 0},
        "metrics": {"pass_rate": 0.0},
        "tasks": [],
        "results": [],
    }

    rendered = render_html_report(payload)

    assert "&lt;suite&gt;" in rendered
    assert "1.0.0" in rendered
    assert "sha256:" + "a" * 64 in rendered
    assert "<suite>" not in rendered
