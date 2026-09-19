import os
import subprocess
import sys
from pathlib import Path


def _run_demo(tmp_path, profile, prompt):
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_eval.demo_agent",
            "--profile",
            profile,
            "--prompt",
            prompt,
        ],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed


def test_reference_demo_agent_covers_all_contracts(tmp_path):
    completed = _run_demo(tmp_path, "reference", "stdout-answer")
    assert completed.returncode == 0
    assert completed.stdout == "42\n"

    completed = _run_demo(tmp_path, "reference", "write-answer-file")
    assert completed.returncode == 0
    assert (tmp_path / "answer.txt").read_text() == "42"

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "input.txt").write_text("agent evaluation")
    completed = _run_demo(tmp_path, "reference", "uppercase-fixture")
    assert completed.returncode == 0
    assert (tmp_path / "output.txt").read_text() == "AGENT EVALUATION"

    completed = _run_demo(tmp_path, "reference", "nested-artifact")
    assert completed.returncode == 0
    assert (tmp_path / "reports" / "result.txt").read_text() == "ready"

    completed = _run_demo(tmp_path, "reference", "stderr-diagnostic")
    assert completed.returncode == 0
    assert completed.stderr == "diagnostic\n"


def test_partial_demo_agent_intentionally_omits_two_behaviors(tmp_path):
    completed = _run_demo(tmp_path, "partial", "nested-artifact")
    assert completed.returncode == 0
    assert not (tmp_path / "reports" / "result.txt").exists()

    completed = _run_demo(tmp_path, "partial", "stderr-diagnostic")
    assert completed.returncode == 0
    assert completed.stderr == ""


def test_demo_agent_rejects_unknown_prompt(tmp_path):
    completed = _run_demo(tmp_path, "reference", "unknown")

    assert completed.returncode == 2
    assert "unknown demo prompt" in completed.stderr
