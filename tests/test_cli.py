import json
import subprocess
import sys


def test_cli_writes_report_and_returns_success(tmp_path):
    task_file = tmp_path / "tasks.json"
    report_file = tmp_path / "reports" / "result.json"
    task_file.write_text(json.dumps({
        "tasks": [{
            "id": "ok",
            "command": [sys.executable, "-c", "print('ok')"],
            "expected_stdout": "ok\n",
        }]
    }))

    completed = subprocess.run(
        [sys.executable, "-m", "agent_eval.cli", str(task_file), "--output", str(report_file)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    assert completed.stdout == ""
    payload = json.loads(report_file.read_text())
    assert payload["summary"] == {"total": 1, "passed": 1, "failed": 0}


def test_cli_returns_failure_for_failed_task(tmp_path):
    task_file = tmp_path / "tasks.json"
    task_file.write_text(json.dumps({
        "tasks": [{
            "id": "bad",
            "command": [sys.executable, "-c", "print('actual')"],
            "expected_stdout": "expected\n",
        }]
    }))

    completed = subprocess.run(
        [sys.executable, "-m", "agent_eval.cli", str(task_file)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 1
    payload = json.loads(completed.stdout)
    assert payload["summary"] == {"total": 1, "passed": 0, "failed": 1}


def test_cli_supports_repeated_runs_tags_and_html_output(tmp_path):
    task_file = tmp_path / "tasks.json"
    json_report = tmp_path / "result.json"
    html_report = tmp_path / "result.html"
    task_file.write_text(json.dumps({
        "tasks": [
            {
                "id": "selected",
                "tags": ["smoke"],
                "command": [sys.executable, "-c", "print('ok')"],
                "expected_stdout": "ok\\n",
            },
            {
                "id": "other",
                "tags": ["slow"],
                "command": [sys.executable, "-c", "raise SystemExit(1)"],
            },
        ]
    }))

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_eval.cli",
            str(task_file),
            "--tag",
            "smoke",
            "--runs",
            "2",
            "--output",
            str(json_report),
            "--html-output",
            str(html_report),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    assert completed.stdout == ""
    payload = json.loads(json_report.read_text())
    assert payload["summary"] == {"total": 2, "passed": 2, "failed": 0}
    assert [result["run_index"] for result in payload["results"]] == [1, 2]
    assert "Agent Evaluation Report" in html_report.read_text()
