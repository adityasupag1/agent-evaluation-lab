import json
import sys

import pytest

from agent_eval.agent import AgentSpec, apply_agent, load_agent_spec


def test_load_agent_spec_and_build_command(tmp_path):
    path = tmp_path / "agent.json"
    path.write_text(json.dumps({
        "name": "demo-agent",
        "command": [sys.executable, "-c", "print({prompt!r})"],
    }).replace("{prompt!r}", "{prompt}"))

    spec = load_agent_spec(path)

    assert spec.name == "demo-agent"
    assert spec.build_command("hello")[-1] == "print(hello)"


def test_agent_spec_requires_prompt_placeholder(tmp_path):
    path = tmp_path / "agent.json"
    path.write_text(json.dumps({
        "name": "demo-agent",
        "command": ["demo-agent", "--run"],
    }))

    with pytest.raises(ValueError, match="prompt"):
        load_agent_spec(path)


def test_apply_agent_replaces_task_command():
    spec = AgentSpec(name="demo", command=("agent", "--prompt", "{prompt}"))
    task = {
        "id": "task-1",
        "prompt": "Create answer.txt",
        "command": ["old-command"],
    }

    prepared = apply_agent(task, spec)

    assert prepared["command"] == ["agent", "--prompt", "Create answer.txt"]
    assert task["command"] == ["old-command"]


def test_apply_agent_requires_non_empty_prompt():
    spec = AgentSpec(name="demo", command=("agent", "{prompt}"))

    with pytest.raises(ValueError, match="prompt"):
        apply_agent({"id": "missing"}, spec)
