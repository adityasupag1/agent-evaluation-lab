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
