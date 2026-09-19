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


def test_invalid_command_is_rejected():
    with pytest.raises(ValueError, match="command"):
        evaluate_task({"id": "invalid", "command": "echo hi"})


def test_report_summary():
    good = evaluate_task({"id": "good", "command": [sys.executable, "-c", "print('x')"]})
    bad = evaluate_task({"id": "bad", "command": [sys.executable, "-c", "raise SystemExit(2)"]})
    payload = report([good, bad])
    assert payload["summary"] == {"total": 2, "passed": 1, "failed": 1}
