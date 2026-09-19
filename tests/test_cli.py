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
                "expected_stdout": "ok\n",
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


def test_cli_runs_prompt_task_with_agent_config_and_label(tmp_path):
    task_file = tmp_path / "tasks.json"
    agent_file = tmp_path / "agent.json"
    report_file = tmp_path / "result.json"

    task_file.write_text(json.dumps({
        "tasks": [
            {
                "id": "prompt-task",
                "prompt": "Create answer.txt with the answer.",
                "expected_files": {"answer.txt": "42"},
            }
        ]
    }))
    agent_file.write_text(json.dumps({
        "name": "demo-agent",
        "command": [
            sys.executable,
            "-c",
            "from pathlib import Path; Path('answer.txt').write_text('42')",
            "{prompt}"
        ]
    }))

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_eval.cli",
            str(task_file),
            "--agent-config",
            str(agent_file),
            "--label",
            "demo-run",
            "--output",
            str(report_file),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    payload = json.loads(report_file.read_text())
    assert payload["benchmark"] == {"agent": "demo-agent", "label": "demo-run"}
    assert payload["summary"] == {"total": 1, "passed": 1, "failed": 0}


def test_compare_cli_writes_json_and_html(tmp_path):
    report_a = tmp_path / "a.json"
    report_b = tmp_path / "b.json"
    output = tmp_path / "comparison.json"
    html_output = tmp_path / "comparison.html"

    base = {
        "summary": {"total": 1, "passed": 1, "failed": 0},
        "metrics": {"pass_rate": 1.0, "average_duration_seconds": 0.2},
        "tasks": [{
            "task_id": "task-1",
            "runs": 1,
            "passed": 1,
            "failed": 0,
            "pass_rate": 1.0,
            "average_duration_seconds": 0.2,
        }],
        "results": [],
    }
    first = dict(base)
    first["benchmark"] = {"label": "first"}
    second = dict(base)
    second["benchmark"] = {"label": "second"}
    report_a.write_text(json.dumps(first))
    report_b.write_text(json.dumps(second))

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_eval.compare_cli",
            str(report_a),
            str(report_b),
            "--output",
            str(output),
            "--html-output",
            str(html_output),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    payload = json.loads(output.read_text())
    assert payload["comparison"]["report_count"] == 2
    assert "Agent Benchmark Comparison" in html_output.read_text()


def test_cli_supports_parallel_execution_and_junit_output(tmp_path):
    task_file = tmp_path / "tasks.json"
    json_report = tmp_path / "result.json"
    junit_report = tmp_path / "result.xml"
    task_file.write_text(json.dumps({
        "tasks": [
            {
                "id": "one",
                "command": [sys.executable, "-c", "print('one')"],
                "expected_stdout": "one\n",
            },
            {
                "id": "two",
                "command": [sys.executable, "-c", "print('two')"],
                "expected_stdout": "two\n",
            },
        ]
    }))

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_eval.cli",
            str(task_file),
            "--runs",
            "2",
            "--parallel",
            "2",
            "--output",
            str(json_report),
            "--junit-output",
            str(junit_report),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    payload = json.loads(json_report.read_text())
    assert payload["summary"] == {"total": 4, "passed": 4, "failed": 0}
    rendered = junit_report.read_text()
    assert 'tests="4"' in rendered
    assert 'failures="0"' in rendered
