from agent_eval.core import EvaluationResult
from agent_eval.junit_report import render_junit


def test_render_junit_contains_pass_and_failure_details():
    results = [
        EvaluationResult(
            task_id="pass",
            passed=True,
            exit_code=0,
            stdout="ok\n",
            stderr="",
            duration_seconds=0.1,
            run_index=1,
        ),
        EvaluationResult(
            task_id="fail",
            passed=False,
            exit_code=1,
            stdout="",
            stderr="boom\n",
            duration_seconds=0.2,
            reason="exit code 1, expected 0",
            run_index=2,
        ),
    ]

    rendered = render_junit(results)

    assert '<testsuite name="agent-evaluation-lab" tests="2" failures="1"' in rendered
    assert 'name="pass[run=1]"' in rendered
    assert 'name="fail[run=2]"' in rendered
    assert 'message="exit code 1, expected 0"' in rendered
    assert "<system-out>ok" in rendered
    assert "<system-err>boom" in rendered
