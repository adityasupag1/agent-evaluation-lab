from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AgentSpec:
    """A shell-free command template for invoking a command-line agent."""

    name: str
    command: tuple[str, ...]

    def build_command(self, prompt: str) -> list[str]:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("task prompt must be a non-empty string")
        return [part.replace("{prompt}", prompt) for part in self.command]


def load_agent_spec(path: Path) -> AgentSpec:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("agent config must be a JSON object")

    name = payload.get("name")
    command = payload.get("command")

    if not isinstance(name, str) or not name.strip():
        raise ValueError("agent config name must be a non-empty string")
    if not isinstance(command, list) or not command or not all(
        isinstance(part, str) and part for part in command
    ):
        raise ValueError("agent config command must be a non-empty list of non-empty strings")
    if not any("{prompt}" in part for part in command):
        raise ValueError("agent config command must contain a {prompt} placeholder")

    return AgentSpec(name=name.strip(), command=tuple(command))


def apply_agent(task: dict[str, Any], agent: AgentSpec) -> dict[str, Any]:
    if not isinstance(task, dict):
        raise ValueError("each task must be a JSON object")

    prompt = task.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        task_id = task.get("id", "<unknown>")
        raise ValueError(f"{task_id}: prompt must be a non-empty string in agent mode")

    prepared = dict(task)
    prepared["command"] = agent.build_command(prompt)
    return prepared
