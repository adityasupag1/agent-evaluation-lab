import json
import sys

import pytest

from agent_eval.core import evaluate_file, evaluate_task, report


def test_passing_task():
    result = evaluate_task({"id": "pass", "command": [sys.executable, "-c", "print('ok')"], "expected_stdout": "ok\n"})
    assert result.passed
    assert result.reason is None


def test_stdout_mismatch_is_reported():
    result = evaluate_task({"id": "wrong-output", "command": [sys.executable, "-c", "print('actual')"], "expected_stdout": "expected\n"})
    assert not result.passed
    assert result.reason == "stdout mismatch"


def test_nonzero_exit_code_is_reported():
    result = evaluate_task({"id": "bad-exit", "command": [sys.executable, "-c", "raise SystemExit(3)"]})
    assert not result.passed
    assert "exit code 3" in result.reason


def test_stderr_assertion():
    result = evaluate_task({"id": "stderr", "command": [sys.executable, "-c", "import sys; print('warning', file=sys.stderr)"], "expected_stderr": "warning\n"})
    assert result.passed


def test_expected_file_content():
    result = evaluate_task({"id": "file", "command": [sys.executable, "-c", "from pathlib import Path; Path('answer.txt').write_text('42')"], "expected_files": {"answer.txt": "42"}})
    assert result.passed


def test_missing_file_is_reported():
    result = evaluate_task({"id": "missing-file", "command": [sys.executable, "-c", "pass"], "expected_files": {"answer.txt": "42"}})
    assert not result.passed
    assert result.reason == "missing file: answer.txt"


def test_path_escape_is_rejected():
    result = evaluate_task({"id": "unsafe-file", "command": [sys.executable, "-c", "pass"], "expected_files": {"../outside.txt": "nope"}})
    assert not result.passed
    assert "unsafe expected file path" in result.reason


@pytest.mark.parametrize("task", [
    {},
    {"id": "", "command": ["echo", "hi"]},
    {"id": "bad", "command": "echo hi"},
    {"id": "bad", "command": [""]},
])
def test_invalid_task_shape_is_rejected(task):
    with pytest.raises(ValueError):
        evaluate_task(task)


@pytest.mark.parametrize("timeout", [0, -1, True, "5"])
def test_invalid_timeout_is_rejected(timeout):
    with pytest.raises(ValueError, match="timeout_seconds"):
        evaluate_task({"id": "invalid-timeout", "command": ["echo", "hi"], "timeout_seconds": timeout})


def test_invalid_expected_exit_code_is_rejected():
    with pytest.raises(ValueError, match="expected_exit_code"):
        evaluate_task({"id": "bad-exit-type", "command": ["echo", "hi"], "expected_exit_code": "0"})


def test_evaluate_file_rejects_non_object_json(tmp_path):
    path = tmp_path / "tasks.json"
    path.write_text(json.dumps([]))
    with pytest.raises(ValueError, match="JSON object"):
        evaluate_file(path)


def test_evaluate_file_rejects_missing_tasks(tmp_path):
    path = tmp_path / "tasks.json"
    path.write_text("{}")
    with pytest.raises(ValueError, match="tasks"):
        evaluate_file(path)


def test_evaluate_file_rejects_duplicate_task_ids_before_execution(tmp_path):
    marker_file = tmp_path / "executed.txt"
    path = tmp_path / "tasks.json"
    path.write_text(json.dumps({
        "tasks": [
            {
                "id": "duplicate",
                "command": [sys.executable, "-c", f"from pathlib import Path; Path({str(marker_file)!r}).write_text('ran')"],
            },
            {
                "id": "duplicate",
                "command": [sys.executable, "-c", "pass"],
            },
        ]
    }))

    with pytest.raises(ValueError, match="duplicate task id: duplicate"):
        evaluate_file(path)

    assert not marker_file.exists()


def test_report_summary():
    good = evaluate_task({"id": "good", "command": [sys.executable, "-c", "print('x')"]})
    bad = evaluate_task({"id": "bad", "command": [sys.executable, "-c", "raise SystemExit(2)"]})
    payload = report([good, bad])
    assert payload["summary"] == {"total": 2, "passed": 1, "failed": 1}


def test_input_files_are_available_to_command():
    result = evaluate_task({
        "id": "fixture",
        "input_files": {"data/input.txt": "hello"},
        "command": [sys.executable, "-c", "from pathlib import Path; print(Path('data/input.txt').read_text().upper())"],
        "expected_stdout": "HELLO\n",
    })
    assert result.passed


def test_input_files_can_drive_output_file_assertions():
    result = evaluate_task({
        "id": "transform",
        "input_files": {"input.txt": "abc"},
        "command": [sys.executable, "-c", "from pathlib import Path; Path('output.txt').write_text(Path('input.txt').read_text()[::-1])"],
        "expected_files": {"output.txt": "cba"},
    })
    assert result.passed


def test_unsafe_input_file_path_is_rejected():
    with pytest.raises(ValueError, match="unsafe file path"):
        evaluate_task({
            "id": "unsafe-fixture",
            "input_files": {"../outside.txt": "nope"},
            "command": [sys.executable, "-c", "pass"],
        })


def test_input_file_dot_path_is_rejected():
    with pytest.raises(ValueError, match="unsafe file path"):
        evaluate_task({
            "id": "dot-fixture",
            "input_files": {".": "nope"},
            "command": [sys.executable, "-c", "pass"],
        })


def test_expected_file_dot_path_is_reported_unsafe():
    result = evaluate_task({
        "id": "dot-expected",
        "command": [sys.executable, "-c", "pass"],
        "expected_files": {".": "nope"},
    })
    assert not result.passed
    assert result.reason == "unsafe expected file path: ."


def test_timeout_is_reported():
    result = evaluate_task({
        "id": "timeout",
        "command": [sys.executable, "-c", "import time; time.sleep(0.2)"],
        "timeout_seconds": 0.05,
    })
    assert not result.passed
    assert result.exit_code is None
    assert result.reason == "timeout after 0.05s"


def test_evaluate_file_repeats_selected_tasks_and_tracks_run_index(tmp_path):
    path = tmp_path / "tasks.json"
    path.write_text(json.dumps({
        "tasks": [
            {
                "id": "python-task",
                "tags": ["python", "smoke"],
                "command": [sys.executable, "-c", "print('ok')"],
                "expected_stdout": "ok\n",
            },
            {
                "id": "docker-task",
                "tags": ["docker"],
                "command": [sys.executable, "-c", "print('skip')"],
            },
        ]
    }))

    results = evaluate_file(path, runs=3, tags=["python"])

    assert [result.task_id for result in results] == ["python-task"] * 3
    assert [result.run_index for result in results] == [1, 2, 3]
    assert all(result.passed for result in results)


@pytest.mark.parametrize("runs", [0, -1, True, 1.5])
def test_invalid_run_count_is_rejected(tmp_path, runs):
    path = tmp_path / "tasks.json"
    path.write_text(json.dumps({"tasks": []}))

    with pytest.raises(ValueError, match="runs"):
        evaluate_file(path, runs=runs)


def test_invalid_task_tags_are_rejected_before_execution(tmp_path):
    marker_file = tmp_path / "executed.txt"
    path = tmp_path / "tasks.json"
    path.write_text(json.dumps({
        "tasks": [
            {
                "id": "first",
                "command": [sys.executable, "-c", f"from pathlib import Path; Path({str(marker_file)!r}).write_text('ran')"],
            },
            {
                "id": "bad-tags",
                "tags": "python",
                "command": [sys.executable, "-c", "pass"],
            },
        ]
    }))

    with pytest.raises(ValueError, match="tags"):
        evaluate_file(path)

    assert not marker_file.exists()


def test_report_includes_reliability_metrics():
    results = [
        evaluate_task({"id": "same", "command": [sys.executable, "-c", "pass"]}, run_index=1),
        evaluate_task({"id": "same", "command": [sys.executable, "-c", "raise SystemExit(1)"]}, run_index=2),
    ]

    payload = report(results)

    assert payload["metrics"]["pass_rate"] == 0.5
    assert payload["tasks"][0]["task_id"] == "same"
    assert payload["tasks"][0]["runs"] == 2
    assert payload["tasks"][0]["passed"] == 1
    assert payload["tasks"][0]["failed"] == 1
    assert payload["tasks"][0]["pass_rate"] == 0.5
