# Agent Evaluation Lab

[![CI](https://github.com/adityasupag1/agent-evaluation-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/adityasupag1/agent-evaluation-lab/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A lightweight, deterministic benchmark harness for evaluating command-line coding agents by what they actually do: exit codes, terminal output, generated files, and execution time.

Agent Evaluation Lab is useful when you want repeatable agent tests without tying the benchmark to a specific model, framework, or implementation detail.

## Why this project?

AI coding agents can produce plausible-looking solutions while still failing on observable behavior. This project turns those behaviors into explicit, reproducible checks.

- **Model-agnostic:** evaluate direct commands or prompt-driven CLI agents through a small adapter.
- **Deterministic:** define expected exit codes, stdout/stderr, files, and timeouts.
- **Isolated per task:** every evaluation runs in a fresh temporary workspace.
- **Portable:** run locally, in Docker, or in CI.
- **Machine-readable:** receive structured JSON reports suitable for automation.

## Use cases

- Regression testing for coding agents
- Small benchmark suites for agent experiments
- Reproducible evaluation of CLI-based solutions
- CI checks for agent-generated artifacts
- Teaching and prototyping deterministic AI-evaluation workflows

## What can a task verify?

| Capability | Example |
| --- | --- |
| Exit status | command must exit with code `0` |
| Standard output | stdout must exactly match expected text |
| Standard error | stderr must exactly match expected text |
| Input fixtures | create deterministic files before execution |
| Generated files | verify required files and exact contents |
| Timeouts | fail tasks that exceed their allowed runtime |
| Path safety | reject fixture/output paths that escape the workspace |

## Quick start

```bash
git clone https://github.com/adityasupag1/agent-evaluation-lab.git
cd agent-evaluation-lab
python -m pip install -e ".[dev]"
agent-eval examples/tasks.json --output report.json
pytest -q
```

A successful evaluation exits with status `0`; a report containing failed tasks exits with status `1`.

## Benchmark mode

Repeat every selected task to measure reliability across multiple runs:

```bash
agent-eval examples/tasks.json --runs 5 --output results.json
```

Tasks can define optional tags and the CLI can filter by one or more tags. When multiple `--tag` flags are supplied, a task is selected if it matches any of them.

```bash
agent-eval examples/tasks.json --tag python --tag filesystem --runs 3
```

Generate a standalone HTML dashboard alongside the machine-readable JSON report:

```bash
agent-eval examples/tasks.json \
  --runs 5 \
  --output reports/results.json \
  --html-output reports/results.html
```

Repeated runs add a `run_index` to each result and the report includes aggregate pass-rate and average-duration metrics for every task.

Independent task executions can also run concurrently while results remain in deterministic run/task order:

```bash
agent-eval examples/tasks.json --runs 5 --parallel 4 --output results.json
```

Each execution still receives its own fresh temporary workspace.

## Agent adapter mode

For prompt-driven coding agents, define a small JSON adapter that describes how the local CLI should receive the prompt. Commands are executed directly as argument lists; the evaluator does not invoke a shell.

```json
{
  "name": "my-coding-agent",
  "command": ["my-agent", "--prompt", "{prompt}"]
}
```

Prompt-based benchmark tasks can then omit `command` and provide a `prompt` instead:

```json
{
  "tasks": [
    {
      "id": "write-answer",
      "prompt": "Read question.txt and write the answer to answer.txt.",
      "input_files": {
        "question.txt": "What is 6 * 7?"
      },
      "expected_files": {
        "answer.txt": "42"
      }
    }
  ]
}
```

Run the same benchmark through any compatible command-line agent by changing only the adapter:

```bash
agent-eval prompt_tasks.json \
  --agent-config agents/my-agent.json \
  --runs 3 \
  --label my-agent-v1 \
  --output reports/my-agent.json
```

The adapter name and optional label are stored in the JSON report so runs can be compared later. Authentication, model selection, and provider-specific flags remain the responsibility of the local agent CLI.

## Compare benchmark reports

Compare two or more benchmark reports without rerunning the tasks:

```bash
agent-eval-compare \
  reports/agent-a.json \
  reports/agent-b.json \
  --output reports/comparison.json \
  --html-output reports/comparison.html
```

The comparison summarizes pass rate, average duration, and task counts. It also reports whether every input report used the same task set; comparisons across different task sets are explicitly flagged.

## CI-friendly JUnit output

Generate JUnit XML alongside JSON or HTML so CI systems can display benchmark failures as test results:

```bash
agent-eval examples/tasks.json \
  --parallel 4 \
  --output reports/results.json \
  --junit-output reports/results.xml
```

Each task/run pair becomes a JUnit test case. Failed evaluations include the failure reason, stdout, and stderr when available.

## Docker

```bash
docker build -t agent-evaluation-lab .
docker run --rm agent-evaluation-lab
```

## Task format

```json
{
  "tasks": [
    {
      "id": "write-answer",
      "tags": ["python", "filesystem"],
      "input_files": {
        "question.txt": "What is 6 * 7?"
      },
      "command": [
        "python",
        "-c",
        "from pathlib import Path; text = Path('question.txt').read_text(); Path('answer.txt').write_text('42'); print('done')"
      ],
      "expected_exit_code": 0,
      "expected_stdout": "done\n",
      "expected_stderr": "",
      "expected_files": {
        "answer.txt": "42"
      },
      "timeout_seconds": 5
    }
  ]
}
```

Each task runs in a fresh temporary directory. `input_files` are materialized before the command starts, nested directories are created automatically, and paths that escape the task workspace are rejected. Optional `tags` support benchmark filtering without changing task behavior. Checks target externally visible behavior rather than source-code structure or implementation-specific names.

## Report format

JSON reports keep the original pass/fail summary and add benchmark-level metrics plus per-task reliability statistics:

```json
{
  "summary": {
    "total": 3,
    "passed": 3,
    "failed": 0
  },
  "metrics": {
    "pass_rate": 1.0,
    "total_duration_seconds": 0.06,
    "average_duration_seconds": 0.02
  },
  "tasks": [
    {
      "task_id": "write-answer",
      "runs": 3,
      "passed": 3,
      "failed": 0,
      "pass_rate": 1.0,
      "average_duration_seconds": 0.02
    }
  ],
  "results": [
    {
      "task_id": "write-answer",
      "passed": true,
      "exit_code": 0,
      "stdout": "done\\n",
      "stderr": "",
      "duration_seconds": 0.02,
      "reason": null,
      "run_index": 1
    }
  ]
}
```

## Design decisions

**Deterministic checks.** Assertions compare explicit observable outputs, making failures straightforward to reproduce.

**Workspace isolation.** Every command receives its own temporary working directory so tasks do not accidentally share state. This is filesystem workspace separation, not an OS-level security sandbox.

**Failure visibility.** Timeout, exit-code, stream, missing-file, and file-content failures are represented in the report rather than hidden behind a single score.

**Small dependency surface.** The runtime uses only the Python standard library; pytest is a development dependency.

## Project structure

```text
agent-evaluation-lab/
├── .github/workflows/ci.yml
├── examples/tasks.json
├── src/agent_eval/
│   ├── __init__.py
│   ├── agent.py
│   ├── cli.py
│   ├── compare_cli.py
│   ├── comparison.py
│   ├── core.py
│   ├── html_report.py
│   └── junit_report.py
├── tests/
│   ├── test_agent.py
│   ├── test_cli.py
│   ├── test_comparison.py
│   ├── test_core.py
│   ├── test_html_report.py
│   └── test_junit_report.py
├── Dockerfile
├── pyproject.toml
└── README.md
```

## Development

```bash
python -m pip install -e ".[dev]"
pytest -q
```

CI runs the same test suite against all supported Python versions.

## Troubleshooting

- If `agent-eval` is not found after installation, try `python -m agent_eval.cli` or reinstall the project with `python -m pip install -e ".[dev]"`.
- If a task fails unexpectedly, validate the task JSON and confirm that `command`, expected streams, and file paths match the documented task format.
- For Docker-related issues, make sure Docker is running and rebuild the image after dependency or source changes.

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for the development workflow and use [GitHub Discussions](https://github.com/adityasupag1/agent-evaluation-lab/discussions) for questions or ideas.

If you find a reproducible bug or have a concrete feature request, open an issue with a minimal example.

## Scope

This repository is intentionally a small evaluation harness, not a security sandbox. Commands supplied in task files are trusted input and execute with the permissions of the process running the evaluator. Docker can be used to add an external isolation boundary when evaluating untrusted workloads.

## License

MIT
