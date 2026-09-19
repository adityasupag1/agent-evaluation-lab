# Agent Evaluation Lab

A small, deterministic benchmark harness for evaluating command-line coding agents.

The project focuses on the engineering side of AI evaluation: defining reproducible tasks, executing candidate commands with resource limits, checking observable behavior, and producing machine-readable scores.

## Features

- JSON-defined evaluation tasks
- Deterministic stdout, exit-code, and file assertions
- Per-task execution timeouts
- Isolated temporary working directories
- Structured JSON reports
- Pytest test suite
- Docker-based reproducible execution
- GitHub Actions CI

## Quick start

```bash
python -m pip install -e ".[dev]"
agent-eval examples/tasks.json --output report.json
pytest
```

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
      "id": "hello-python",
      "command": ["python", "-c", "print('hello')"],
      "expected_exit_code": 0,
      "expected_stdout": "hello\n",
      "timeout_seconds": 5
    }
  ]
}
```

Each task is executed in a fresh temporary directory. Evaluation is based on observable behavior rather than implementation details.

## Design goals

The harness intentionally stays small and auditable. A benchmark should be easy to reproduce locally, produce stable results in CI, fail clearly when a process times out, and emit output that other tooling can consume.

## Development

```bash
python -m pip install -e ".[dev]"
pytest -q
```

## License

MIT
