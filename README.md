# Agent Evaluation Lab

[![CI](https://github.com/adityasupag1/agent-evaluation-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/adityasupag1/agent-evaluation-lab/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A deterministic benchmark harness for evaluating command-line coding agents through observable behavior.

It provides a compact example of the engineering behind AI evaluation: reproducible task definitions, isolated execution, resource limits, behavioral assertions, automated tests, and machine-readable reports.

## Features

- JSON-defined evaluation tasks
- Exact exit-code, stdout, and stderr assertions
- Expected output-file verification
- Per-task execution timeouts
- Fresh temporary working directory for every task
- Path-safety checks for expected artifacts
- Structured JSON reports and CLI exit status
- Pytest coverage for success and failure paths
- Docker-based reproducible execution
- GitHub Actions matrix CI on Python 3.10, 3.11, and 3.12

## Quick start

```bash
git clone https://github.com/adityasupag1/agent-evaluation-lab.git
cd agent-evaluation-lab
python -m pip install -e ".[dev]"
agent-eval examples/tasks.json --output report.json
pytest -q
```

A successful evaluation exits with status `0`; a report containing failed tasks exits with status `1`.

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
      "command": [
        "python",
        "-c",
        "from pathlib import Path; Path('answer.txt').write_text('42'); print('done')"
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

Each task runs in a fresh temporary directory. Checks target externally visible behavior rather than source-code structure or implementation-specific names.

## Report format

```json
{
  "summary": {
    "total": 1,
    "passed": 1,
    "failed": 0
  },
  "results": [
    {
      "task_id": "write-answer",
      "passed": true,
      "exit_code": 0,
      "stdout": "done\n",
      "stderr": "",
      "duration_seconds": 0.02,
      "reason": null
    }
  ]
}
```

## Design decisions

**Deterministic checks.** Assertions compare explicit observable outputs, making failures straightforward to reproduce.

**Isolation.** Every command receives its own temporary working directory so tasks do not accidentally share state.

**Failure visibility.** Timeout, exit-code, stream, missing-file, and file-content failures are represented in the report rather than hidden behind a single score.

**Small dependency surface.** The runtime uses only the Python standard library; pytest is a development dependency.

## Project structure

```text
agent-evaluation-lab/
├── .github/workflows/ci.yml
├── examples/tasks.json
├── src/agent_eval/
│   ├── __init__.py
│   ├── cli.py
│   └── core.py
├── tests/test_core.py
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

## Scope

This repository is intentionally a small evaluation harness, not a security sandbox. Commands supplied in task files are trusted input and execute with the permissions of the process running the evaluator. Docker can be used to add an external isolation boundary when evaluating untrusted workloads.

## License

MIT
