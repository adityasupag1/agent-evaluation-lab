from __future__ import annotations

import json
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


def validate_benchmark_file(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("input must be a JSON object")

    tasks = payload.get("tasks")
    if not isinstance(tasks, list):
        raise ValueError("input must contain a 'tasks' list")

    seen_ids: set[str] = set()
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            raise ValueError(f"task at index {index} must be a JSON object")

        task_id = task.get("id")
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError(f"task at index {index}: id must be a non-empty string")
        if task_id in seen_ids:
            raise ValueError(f"duplicate task id: {task_id}")
        seen_ids.add(task_id)

        command = task.get("command")
        prompt = task.get("prompt")
        if command is None and prompt is None:
            raise ValueError(f"{task_id}: must define command or prompt")
        if command is not None and (
            not isinstance(command, list)
            or not command
            or not all(isinstance(part, str) and part for part in command)
        ):
            raise ValueError(f"{task_id}: command must be a non-empty list of non-empty strings")
        if prompt is not None and (not isinstance(prompt, str) or not prompt.strip()):
            raise ValueError(f"{task_id}: prompt must be a non-empty string")

        tags = task.get("tags", [])
        if not isinstance(tags, list) or not all(
            isinstance(tag, str) and tag.strip() for tag in tags
        ):
            raise ValueError(f"{task_id}: tags must be a list of non-empty strings")

        timeout = task.get("timeout_seconds", 10)
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ValueError(f"{task_id}: timeout_seconds must be a positive number")

        expected_exit = task.get("expected_exit_code", 0)
        if isinstance(expected_exit, bool) or not isinstance(expected_exit, int):
            raise ValueError(f"{task_id}: expected_exit_code must be an integer")

        for field in ("expected_stdout", "expected_stderr"):
            value = task.get(field)
            if value is not None and not isinstance(value, str):
                raise ValueError(f"{task_id}: {field} must be a string")

        for field in ("input_files", "expected_files"):
            value = task.get(field, {})
            if not isinstance(value, dict) or not all(
                isinstance(relative, str)
                and relative
                and isinstance(file_content, str)
                for relative, file_content in value.items()
            ):
                raise ValueError(
                    f"{task_id}: {field} must map non-empty paths to text contents"
                )
            for relative in value:
                if not _is_safe_relative_path(relative):
                    raise ValueError(f"{task_id}: unsafe {field} path: {relative}")

    return {
        "valid": True,
        "task_count": len(tasks),
        "task_ids": [task["id"] for task in tasks],
    }


def _is_safe_relative_path(value: str) -> bool:
    for path_type in (PurePosixPath, PureWindowsPath):
        path = path_type(value)
        if path.is_absolute() or getattr(path, "drive", ""):
            return False

        depth = 0
        for part in path.parts:
            if part in ("", "."):
                continue
            if part == "..":
                depth -= 1
                if depth < 0:
                    return False
            else:
                depth += 1
        if depth == 0:
            return False

    return True
