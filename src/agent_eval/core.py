from __future__ import annotations

import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .agent import AgentSpec, apply_agent


@dataclass(frozen=True)
class EvaluationResult:
    task_id: str
    passed: bool
    exit_code: int | None
    stdout: str
    stderr: str
    duration_seconds: float
    reason: str | None = None
    run_index: int = 1


def evaluate_task(task: dict[str, Any], *, run_index: int = 1) -> EvaluationResult:
    task_id, command, timeout, expected_exit, expected_stdout, expected_stderr, expected_files, input_files = _validate_task(task)

    started = time.monotonic()
    try:
        with tempfile.TemporaryDirectory(prefix="agent-eval-") as workdir:
            _write_input_files(Path(workdir), input_files)
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
            run_index=run_index,
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
        run_index=run_index,
    )


def evaluate_file(path: Path, *, runs: int = 1, tags: list[str] | None = None, agent: AgentSpec | None = None, parallel: int = 1) -> list[EvaluationResult]:
    if isinstance(runs, bool) or not isinstance(runs, int) or runs <= 0:
        raise ValueError("runs must be a positive integer")
    if isinstance(parallel, bool) or not isinstance(parallel, int) or parallel <= 0:
        raise ValueError("parallel must be a positive integer")

    requested_tags = _normalize_tags(tags)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("input must be a JSON object")
    tasks = payload.get("tasks")
    if not isinstance(tasks, list):
        raise ValueError("input must contain a 'tasks' list")

    seen_ids: set[str] = set()
    validated_tasks: list[dict[str, Any]] = []
    for task in tasks:
        prepared = apply_agent(task, agent) if agent is not None else task
        task_id, *_ = _validate_task(prepared)
        if task_id in seen_ids:
            raise ValueError(f"duplicate task id: {task_id}")
        seen_ids.add(task_id)
        validated_tasks.append(prepared)

    if requested_tags:
        validated_tasks = [
            task
            for task in validated_tasks
            if requested_tags.intersection(task.get("tags", []))
        ]

    jobs = [
        (order, task, run_index)
        for order, (run_index, task) in enumerate(
            (run_index, task)
            for run_index in range(1, runs + 1)
            for task in validated_tasks
        )
    ]
    if parallel == 1:
        return [
            evaluate_task(task, run_index=run_index)
            for _, task, run_index in jobs
        ]

    completed_results: dict[int, EvaluationResult] = {}
    with ThreadPoolExecutor(max_workers=parallel) as executor:
        futures = {
            executor.submit(evaluate_task, task, run_index=run_index): order
            for order, task, run_index in jobs
        }
        for future in as_completed(futures):
            completed_results[futures[future]] = future.result()

    return [completed_results[index] for index in range(len(jobs))]


def report(
    results: list[EvaluationResult],
    *,
    agent_name: str | None = None,
    label: str | None = None,
    suite_name: str | None = None,
    suite_version: str | None = None,
    suite_description: str | None = None,
    fingerprint: str | None = None,
) -> dict[str, Any]:
    passed = sum(result.passed for result in results)
    total = len(results)
    duration = sum(result.duration_seconds for result in results)

    grouped: dict[str, list[EvaluationResult]] = {}
    for result in results:
        grouped.setdefault(result.task_id, []).append(result)

    task_summaries = []
    for task_id, task_results in grouped.items():
        task_passed = sum(result.passed for result in task_results)
        task_duration = sum(result.duration_seconds for result in task_results)
        task_summaries.append({
            "task_id": task_id,
            "runs": len(task_results),
            "passed": task_passed,
            "failed": len(task_results) - task_passed,
            "pass_rate": task_passed / len(task_results),
            "average_duration_seconds": task_duration / len(task_results),
        })

    payload: dict[str, Any] = {
        "summary": {"total": total, "passed": passed, "failed": total - passed},
        "metrics": {
            "pass_rate": passed / total if total else 0.0,
            "total_duration_seconds": duration,
            "average_duration_seconds": duration / total if total else 0.0,
        },
        "tasks": task_summaries,
        "results": [asdict(result) for result in results],
    }
    if any(
        value is not None
        for value in (
            agent_name,
            label,
            suite_name,
            suite_version,
            suite_description,
            fingerprint,
        )
    ):
        payload["benchmark"] = {}
        if agent_name is not None:
            payload["benchmark"]["agent"] = agent_name
        if label is not None:
            payload["benchmark"]["label"] = label
        if suite_name is not None:
            payload["benchmark"]["name"] = suite_name
        if suite_version is not None:
            payload["benchmark"]["version"] = suite_version
        if suite_description is not None:
            payload["benchmark"]["description"] = suite_description
        if fingerprint is not None:
            payload["benchmark"]["fingerprint"] = fingerprint
    return payload


def _normalize_tags(tags: list[str] | None) -> set[str]:
    if tags is None:
        return set()
    if not isinstance(tags, list) or not all(isinstance(tag, str) and tag.strip() for tag in tags):
        raise ValueError("tags must be a list of non-empty strings")
    return {tag.strip() for tag in tags}


def _validate_task(task: dict[str, Any]) -> tuple[str, list[str], float, int, str | None, str | None, dict[str, str], dict[str, str]]:
    if not isinstance(task, dict):
        raise ValueError("each task must be a JSON object")
    if "id" not in task or not isinstance(task["id"], str) or not task["id"].strip():
        raise ValueError("task id must be a non-empty string")
    if "command" not in task:
        raise ValueError(f"{task['id']}: missing command")

    task_id = task["id"]
    command = task["command"]
    if not isinstance(command, list) or not command or not all(isinstance(x, str) and x for x in command):
        raise ValueError(f"{task_id}: command must be a non-empty list of non-empty strings")

    tags = task.get("tags", [])
    if not isinstance(tags, list) or not all(isinstance(tag, str) and tag.strip() for tag in tags):
        raise ValueError(f"{task_id}: tags must be a list of non-empty strings")

    timeout_raw = task.get("timeout_seconds", 10)
    if isinstance(timeout_raw, bool) or not isinstance(timeout_raw, (int, float)) or timeout_raw <= 0:
        raise ValueError(f"{task_id}: timeout_seconds must be a positive number")
    timeout = float(timeout_raw)

    exit_raw = task.get("expected_exit_code", 0)
    if isinstance(exit_raw, bool) or not isinstance(exit_raw, int):
        raise ValueError(f"{task_id}: expected_exit_code must be an integer")

    expected_stdout = task.get("expected_stdout")
    expected_stderr = task.get("expected_stderr")
    if expected_stdout is not None and not isinstance(expected_stdout, str):
        raise ValueError(f"{task_id}: expected_stdout must be a string")
    if expected_stderr is not None and not isinstance(expected_stderr, str):
        raise ValueError(f"{task_id}: expected_stderr must be a string")

    input_files = task.get("input_files", {})
    if not isinstance(input_files, dict) or not all(
        isinstance(path, str) and path and isinstance(content, str)
        for path, content in input_files.items()
    ):
        raise ValueError(f"{task_id}: input_files must map non-empty paths to text contents")

    expected_files = task.get("expected_files", {})
    if not isinstance(expected_files, dict) or not all(
        isinstance(path, str) and path and isinstance(content, str)
        for path, content in expected_files.items()
    ):
        raise ValueError(f"{task_id}: expected_files must map non-empty paths to text contents")

    return task_id, command, timeout, exit_raw, expected_stdout, expected_stderr, expected_files, input_files


def _safe_target(root: Path, relative: str) -> Path:
    target = (root / relative).resolve()
    if root == target or root not in target.parents:
        raise ValueError(f"unsafe file path: {relative}")
    return target


def _write_input_files(workdir: Path, input_files: dict[str, str]) -> None:
    root = workdir.resolve()
    for relative, content in input_files.items():
        target = _safe_target(root, relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def _check_expected_files(workdir: Path, expected_files: dict[str, str]) -> list[str]:
    failures: list[str] = []
    root = workdir.resolve()
    for relative, expected_content in expected_files.items():
        try:
            target = _safe_target(root, relative)
        except ValueError:
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
