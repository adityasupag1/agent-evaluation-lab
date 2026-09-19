import sys

import pytest

from agent_eval.core import evaluate_task, report


def test_passing_task():
    result = evaluate_task({
        "id": "pass",
        "command": [sys.executable, "-c", "print('ok')"],
        "expected_stdout": "ok\n",
        "expected_exit_code": 0,
    })
    assert result.passed
    assert result.reason is None


def test_stdout_mismatch_is_reported():
    result = evaluate_task({
        "id": "wrong-output",
        "command": [sys.executable, "-c", "print('actual')"],
        "expected_stdout": "expected\n",
    })
    assert not result.passed
    assert result.reason == "stdout mismatch"


def test_nonzero_exit_code_is_reported():
    result = evaluate_task({
        "id": "bad-exit",
        "command": [sys.executable, "-c", "raise SystemExit(3)"],
        "expected_exit_code": 0,
    })
    assert not result.passed
    assert "exit code 3" in result.reason


def test_stderr_assertion():
    result = evaluate_task({
        "id": "stderr",
        "command": [sys.executable, "-c", "import sys; print('warning', file=sys.stderr)"],
        "expected_stderr": "warning\n",
    })
    assert result.passed


def test_expected_file_content():
    result = evaluate_task({
        "id": "file",
        "command": [sys.executable, "-c", "from pathlib import Path; Path('answer.txt').write_text('42')"],
        "expected_files": {"answer.txt": "42"},
    })
    assert result.passed


def test_missing_file_is_reported():
    result = evaluate_task({
        "id": "missing-file",
        "command": [sys.executable, "-c", "pass"],
        "expected_files": {"answer.txt": "42"},
    })
    assert not result.passed
    assert result.reason == "missing file: answer.txt"


def test_path_escape_is_rejected():
    result = evaluate_task({
        "id": "unsafe-file",
        "command": [sys.executable, "-c", "pass"],
        "expected_files": {"../outside.txt": "nope"},
    })
    assert not result.passed
    assert "unsafe expected file path" in result.reason


def test_invalid_command_is_rejected():
    with pytest.raises(ValueError, match="command"):
        evaluate_task({"id": "invalid", "command": "echo hi"})


def test_nonpositive_timeout_is_rejected():
    with pytest.raises(ValueError, match="timeout_seconds"):
        evaluate_task({"id": "invalid-timeout", "command": ["echo", "hi"], "timeout_seconds": 0})


def test_report_summary():
    good = evaluate_task({"id": "good", "command": [sys.executable, "-c", "print('x')"]})
    bad = evaluate_task({"id": "bad", "command": [sys.executable, "-c", "raise SystemExit(2)"]})
    payload = report([good, bad])
    assert payload["summary"] == {"total": 2, "passed": 1, "failed": 1}
