import json

import pytest

from agent_eval.validation import validate_benchmark_file


def test_validate_benchmark_file_accepts_command_and_prompt_tasks(tmp_path):
    path = tmp_path / "benchmark.json"
    path.write_text(json.dumps({
        "tasks": [
            {
                "id": "direct",
                "tags": ["smoke"],
                "command": ["python", "-c", "print('ok')"],
                "expected_stdout": "ok\n",
            },
            {
                "id": "prompted",
                "prompt": "Create answer.txt.",
                "expected_files": {"answer.txt": "42"},
            },
        ]
    }))

    result = validate_benchmark_file(path)

    assert result["valid"] is True
    assert result["task_count"] == 2
    assert result["task_ids"] == ["direct", "prompted"]
    assert result["benchmark"]["fingerprint"].startswith("sha256:")


def test_validate_benchmark_file_rejects_duplicate_ids(tmp_path):
    path = tmp_path / "benchmark.json"
    path.write_text(json.dumps({
        "tasks": [
            {"id": "same", "command": ["echo", "one"]},
            {"id": "same", "command": ["echo", "two"]},
        ]
    }))

    with pytest.raises(ValueError, match="duplicate task id: same"):
        validate_benchmark_file(path)


@pytest.mark.parametrize(
    "task, message",
    [
        ({"id": "missing-executor"}, "command or prompt"),
        ({"id": "bad-command", "command": "echo ok"}, "command"),
        ({"id": "bad-prompt", "prompt": ""}, "prompt"),
        ({"id": "bad-tags", "command": ["echo", "ok"], "tags": "smoke"}, "tags"),
        ({"id": "bad-timeout", "command": ["echo", "ok"], "timeout_seconds": 0}, "timeout_seconds"),
        ({"id": "bad-exit", "command": ["echo", "ok"], "expected_exit_code": True}, "expected_exit_code"),
        ({"id": "bad-files", "command": ["echo", "ok"], "expected_files": []}, "expected_files"),
    ],
)
def test_validate_benchmark_file_rejects_invalid_task_fields(tmp_path, task, message):
    path = tmp_path / "benchmark.json"
    path.write_text(json.dumps({"tasks": [task]}))

    with pytest.raises(ValueError, match=message):
        validate_benchmark_file(path)


def test_published_schema_is_valid_json():
    from pathlib import Path

    schema_path = Path(__file__).parents[1] / "docs" / "benchmark.schema.json"
    payload = json.loads(schema_path.read_text())

    assert payload["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert payload["title"] == "Agent Evaluation Lab benchmark"


@pytest.mark.parametrize("path_value", ["../escape.txt", "/absolute.txt", ".", "nested/../..", "C:\\temp\\escape.txt"])
def test_validate_benchmark_file_rejects_unsafe_paths(tmp_path, path_value):
    path = tmp_path / "benchmark.json"
    path.write_text(json.dumps({
        "tasks": [
            {
                "id": "unsafe-path",
                "command": ["echo", "ok"],
                "expected_files": {path_value: "x"},
            }
        ]
    }))

    with pytest.raises(ValueError, match="unsafe expected_files path"):
        validate_benchmark_file(path)


def test_benchmark_metadata_and_fingerprint_are_reported(tmp_path):
    path = tmp_path / "benchmark.json"
    path.write_text(json.dumps({
        "name": "coding-smoke",
        "version": "2.1.0",
        "description": "Small reproducible coding benchmark.",
        "tasks": [
            {
                "id": "one",
                "command": ["python", "-c", "print(1)"],
                "expected_stdout": "1\n",
            }
        ],
    }))

    result = validate_benchmark_file(path)

    assert result["benchmark"]["name"] == "coding-smoke"
    assert result["benchmark"]["version"] == "2.1.0"
    assert result["benchmark"]["description"] == "Small reproducible coding benchmark."
    assert len(result["benchmark"]["fingerprint"]) == len("sha256:") + 64


def test_fingerprint_ignores_json_key_order_and_suite_description(tmp_path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    task = {
        "id": "stable",
        "command": ["python", "-c", "print('ok')"],
        "expected_stdout": "ok\n",
    }
    first.write_text(json.dumps({
        "name": "suite",
        "description": "first description",
        "tasks": [task],
    }))
    second.write_text(json.dumps({
        "tasks": [{
            "expected_stdout": "ok\n",
            "command": ["python", "-c", "print('ok')"],
            "id": "stable",
        }],
        "name": "suite",
        "description": "changed documentation only",
    }))

    first_result = validate_benchmark_file(first)
    second_result = validate_benchmark_file(second)

    assert first_result["benchmark"]["fingerprint"] == second_result["benchmark"]["fingerprint"]


@pytest.mark.parametrize("field", ["name", "version", "description"])
def test_empty_benchmark_metadata_is_rejected(tmp_path, field):
    path = tmp_path / "benchmark.json"
    payload = {
        "tasks": [{"id": "one", "command": ["echo", "ok"]}],
        field: "   ",
    }
    path.write_text(json.dumps(payload))

    with pytest.raises(ValueError, match=f"benchmark {field}"):
        validate_benchmark_file(path)
