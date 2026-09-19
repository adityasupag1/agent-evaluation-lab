# Agent Evaluation Lab

[![CI](https://github.com/adityasupag1/agent-evaluation-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/adityasupag1/agent-evaluation-lab/actions/workflows/ci.yml)
[![Demo](https://github.com/adityasupag1/agent-evaluation-lab/actions/workflows/demo.yml/badge.svg)](https://github.com/adityasupag1/agent-evaluation-lab/actions/workflows/demo.yml)
[![Package](https://github.com/adityasupag1/agent-evaluation-lab/actions/workflows/package.yml/badge.svg)](https://github.com/adityasupag1/agent-evaluation-lab/actions/workflows/package.yml)
[![Release](https://img.shields.io/github/v/release/adityasupag1/agent-evaluation-lab)](https://github.com/adityasupag1/agent-evaluation-lab/releases/latest)
[![PyPI](https://img.shields.io/pypi/v/agent-evaluation-lab)](https://pypi.org/project/agent-evaluation-lab/)
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

## End-to-end demo

A credential-free demo exercises the complete prompt-agent flow with two deterministic fixture adapters. It is designed to prove the plumbing—not to claim real LLM benchmark scores.

| Demo adapter | Expected result |
| --- | ---: |
| `demo-reference` | 5/5 (100%) |
| `demo-partial` | 3/5 (60%) |

Both adapters run against the exact same fingerprinted benchmark definition, then `agent-eval-compare` produces a JSON and HTML comparison.

See [docs/demo.md](docs/demo.md) for the commands and [the demo workflow](.github/workflows/demo.yml) for the CI implementation.

## Quick start

Install the published package from PyPI:

```bash
python -m pip install agent-evaluation-lab
agent-eval --help
```

For repository development:

```bash
git clone https://github.com/adityasupag1/agent-evaluation-lab.git
cd agent-evaluation-lab
python -m pip install -e ".[dev]"
agent-eval examples/tasks.json --output report.json
pytest -q
```

A successful evaluation exits with status `0`; a report containing failed tasks exits with status `1`.

Validate a benchmark without executing any task:

```bash
agent-eval-validate examples/starter-benchmark.json
```

A JSON Schema for editor/tooling integration is published at [`docs/benchmark.schema.json`](docs/benchmark.schema.json).

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

The comparison summarizes pass rate, average duration, and task counts. Reports produced by current versions also carry a SHA-256 benchmark fingerprint, so the comparison can distinguish a genuinely identical benchmark definition from two suites that merely reuse the same task IDs. Older reports without provenance remain readable and are marked as having unavailable fingerprint coverage.

## CI-friendly JUnit output

Generate JUnit XML alongside JSON or HTML so CI systems can display benchmark failures as test results:

```bash
agent-eval examples/tasks.json \
  --parallel 4 \
  --output reports/results.json \
  --junit-output reports/results.xml
```

Each task/run pair becomes a JUnit test case. Failed evaluations include the failure reason, stdout, and stderr when available.

## Starter benchmark suite

[`examples/starter-benchmark.json`](examples/starter-benchmark.json) contains a small deterministic suite covering stdout, stderr, exit-code contracts, input fixtures, nested output files, and tags.

```bash
agent-eval-validate examples/starter-benchmark.json
agent-eval examples/starter-benchmark.json \
  --runs 2 \
  --parallel 2 \
  --output reports/starter.json \
  --html-output reports/starter.html \
  --junit-output reports/starter.xml
```

This provides a known-good smoke test before authoring project-specific benchmarks.

## Reusable GitHub Action

The repository includes a composite action, so another repository can run a benchmark directly in CI:

```yaml
name: Agent benchmark

on:
  pull_request:

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: adityasupag1/agent-evaluation-lab@main
        with:
          task-file: benchmarks/tasks.json
          runs: "3"
          parallel: "2"
          label: ci-benchmark
```

By default the action writes:

```text
agent-eval-results/results.json
agent-eval-results/results.html
agent-eval-results/results.xml
```

It validates the benchmark before execution and supports optional `agent-config`, custom report paths, and a selectable Python version. For reproducible production workflows, pin the action to a commit SHA or a release tag instead of `main`.

## Docker

```bash
docker build -t agent-evaluation-lab .
docker run --rm agent-evaluation-lab
```

## Task format

A benchmark can include optional suite metadata. The metadata is recorded in reports, while the reproducibility fingerprint is computed from the task definitions themselves.

```json
{
  "name": "coding-smoke",
  "version": "1.0.0",
  "description": "Small deterministic coding-agent benchmark.",
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

## Benchmark provenance

Before execution, the CLI validates the benchmark and computes a canonical SHA-256 fingerprint from the complete `tasks` array. JSON key order and formatting do not change the fingerprint, while any change to a task definition does.

This makes comparison safer: two reports can have the same task IDs but still be flagged when the underlying benchmark definitions differ. Human-facing metadata such as the suite description is stored separately and does not change the task fingerprint.

## Report format

JSON reports keep the original pass/fail summary, provenance, benchmark-level metrics, and per-task reliability statistics:

```json
{
  "benchmark": {
    "name": "coding-smoke",
    "version": "1.0.0",
    "fingerprint": "sha256:..."
  },
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

**Reproducible provenance.** Reports carry canonical task fingerprints so cross-run and cross-agent comparisons can verify that the underlying benchmark definition is unchanged.

**Workspace isolation.** Every command receives its own temporary working directory so tasks do not accidentally share state. This is filesystem workspace separation, not an OS-level security sandbox.

**Failure visibility.** Timeout, exit-code, stream, missing-file, and file-content failures are represented in the report rather than hidden behind a single score.

**Small dependency surface.** The runtime uses only the Python standard library; pytest is a development dependency.

## Project structure

```text
agent-evaluation-lab/
├── .github/workflows/ci.yml
├── .github/workflows/demo.yml
├── .github/workflows/package.yml
├── .github/workflows/release.yml
├── action.yml
├── docs/benchmark.schema.json
├── docs/demo.md
├── docs/pypi-publishing.md
├── examples/agent-demo-benchmark.json
├── examples/agents/
├── examples/starter-benchmark.json
├── examples/tasks.json
├── src/agent_eval/
│   ├── __init__.py
│   ├── agent.py
│   ├── cli.py
│   ├── compare_cli.py
│   ├── comparison.py
│   ├── core.py
│   ├── demo_agent.py
│   ├── html_report.py
│   ├── junit_report.py
│   ├── validate_cli.py
│   └── validation.py
├── tests/
│   ├── test_agent.py
│   ├── test_cli.py
│   ├── test_comparison.py
│   ├── test_core.py
│   ├── test_demo_agent.py
│   ├── test_html_report.py
│   ├── test_junit_report.py
│   └── test_validation.py
├── Dockerfile
├── pyproject.toml
└── README.md
```

## Release notes

See [CHANGELOG.md](CHANGELOG.md) for version history, [v0.7.0 release notes](docs/releases/v0.7.0.md) for the current release, and [v0.6.0 release notes](docs/releases/v0.6.0.md) for the first public release overview.

## Distribution builds

The [Package workflow](.github/workflows/package.yml) builds both wheel and source distributions, validates their metadata with Twine, installs the wheel in a clean virtual environment, smoke-tests all three CLI entry points, and uploads the resulting `dist/` files as a workflow artifact.

The repository also contains a dedicated [PyPI release workflow](.github/workflows/release.yml) that uses GitHub OIDC Trusted Publishing instead of a long-lived API token. It verifies that the GitHub release tag matches the package version, builds distributions in a separate job, and grants `id-token: write` only to the final publish job.

PyPI Trusted Publishing is active and v0.7.0 was published through GitHub OIDC without a long-lived API token. See [docs/pypi-publishing.md](docs/pypi-publishing.md) for the release procedure.

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
