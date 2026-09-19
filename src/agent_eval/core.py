from __future__ import annotations

import json
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class EvaluationResult:
    task_id: str
    passed: bool
    exit_code: int | None
    stdout: str
    stderr: str
    duration_seconds: float
    reason: str | None = None


def evaluate_task(task: dict[str, Any]) -> EvaluationResult:
    task_id = str(task["id"])
    command = task["command"]
    timeout = float(task.get("timeout_seconds", 10))
    expected_exit = int(task.get("expected_exit_code", 0))
    expected_stdout = task.get("expected_stdout")
    expected_stderr = task.get("expected_stderr")
    expected_files = task.get("expected_files", {})

    if not isinstance(command, list) or not command or not all(isinstance(x, str) for x in command):
        raise ValueError(f"{task_id}: command must be a non-empty list of strings")
    if timeout <= 0:
        raise ValueError(f"{task_id}: timeout_seconds must be positive")
    if not isinstance(expected_files, dict) or not all(
        isinstance(path, str) and isinstance(content, str)
        for path, content in expected_files.items()
    ):
        raise ValueError(f"{task_id}: expected_files must map paths to text contents")

    started = time.monotonic()
    try:
        with tempfile.TemporaryDirectory(prefix="agent-eval-") as workdir:
            completed = subprocess.run(
                command,
                cwd=workdir,
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
            file_failures = _check_expected_files(Path(workdir), expected_files)
        duration = time.monotonic() - started
    except subprocess.TimeoutExpired as exc:
        return EvaluationResult(
            task_id=task_id,
            passed=False,
            exit_code=None,
            stdout=_to_text(exc.stdout),
            stderr=_to_text(exc.stderr),
            duration_seconds=time.monotonic() - started,
            reason=f"timeout after {timeout:g}s",
        )

    failures: list[str] = []
    if completed.returncode != expected_exit:
        failures.append(f"exit code {completed.returncode}, expected {expected_exit}")
    if expected_stdout is not None and completed.stdout != expected_stdout:
        failures.append("stdout mismatch")
    if expected_stderr is not None and completed.stderr != expected_stderr:
        failures.append("stderr mismatch")
    failures.extend(file_failures)

    return EvaluationResult(
        task_id=task_id,
        passed=not failures,
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        duration_seconds=duration,
        reason="; ".join(failures) or None,
    )


def evaluate_file(path: Path) -> list[EvaluationResult]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    tasks = payload.get("tasks")
    if not isinstance(tasks, list):
        raise ValueError("input must contain a 'tasks' list")
    return [evaluate_task(task) for task in tasks]


def report(results: list[EvaluationResult]) -> dict[str, Any]:
    passed = sum(result.passed for result in results)
    return {
        "summary": {"total": len(results), "passed": passed, "failed": len(results) - passed},
        "results": [asdict(result) for result in results],
    }


def _check_expected_files(workdir: Path, expected_files: dict[str, str]) -> list[str]:
    failures: list[str] = []
    root = workdir.resolve()
    for relative, expected_content in expected_files.items():
        target = (root / relative).resolve()
        if root not in target.parents:
            failures.append(f"unsafe expected file path: {relative}")
            continue
        if not target.is_file():
            failures.append(f"missing file: {relative}")
            continue
        if target.read_text(encoding="utf-8") != expected_content:
            failures.append(f"file content mismatch: {relative}")
    return failures


def _to_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    return value.decode(errors="replace") if isinstance(value, bytes) else value
