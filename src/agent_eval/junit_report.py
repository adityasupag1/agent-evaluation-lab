from __future__ import annotations

from xml.etree import ElementTree as ET

from .core import EvaluationResult


def render_junit(results: list[EvaluationResult]) -> str:
    total = len(results)
    failures = sum(not result.passed for result in results)
    duration = sum(result.duration_seconds for result in results)

    suite = ET.Element(
        "testsuite",
        {
            "name": "agent-evaluation-lab",
            "tests": str(total),
            "failures": str(failures),
            "errors": "0",
            "time": f"{duration:.6f}",
        },
    )

    for result in results:
        case = ET.SubElement(
            suite,
            "testcase",
            {
                "classname": "agent_eval",
                "name": f"{result.task_id}[run={result.run_index}]",
                "time": f"{result.duration_seconds:.6f}",
            },
        )
        if not result.passed:
            failure = ET.SubElement(
                case,
                "failure",
                {
                    "message": result.reason or "evaluation failed",
                    "type": "EvaluationFailure",
                },
            )
            failure.text = result.reason or "evaluation failed"

        if result.stdout:
            stdout = ET.SubElement(case, "system-out")
            stdout.text = result.stdout
        if result.stderr:
            stderr = ET.SubElement(case, "system-err")
            stderr.text = result.stderr

    tree = ET.ElementTree(suite)
    ET.indent(tree, space="  ")
    return ET.tostring(suite, encoding="unicode", xml_declaration=False) + "\n"
