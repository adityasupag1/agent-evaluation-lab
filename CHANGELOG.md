# Changelog

All notable changes to Agent Evaluation Lab are documented here.

## [Unreleased]

## [0.7.0] - 2026-09-19

### Added

- Secure PyPI Trusted Publishing workflow using GitHub OIDC, release-tag/version verification, separated build/publish jobs, and a protected `pypi` environment.
- Exact one-time Pending Publisher and GitHub environment setup guide for first-time PyPI publication.
- Distribution build workflow that creates wheel/source archives, validates metadata, installs the wheel in a clean environment, smoke-tests the CLIs, and uploads the built files as an artifact.
- PyPI-facing package metadata including project URLs, keywords, and classifiers.
- Credential-free end-to-end prompt-agent demo with deterministic reference and intentionally partial fixture adapters.
- GitHub Actions demo workflow that generates JSON, HTML, and JUnit reports, verifies expected scores, compares matching benchmark fingerprints, and uploads the reports as an artifact.

### Release goal

- First package release successfully published to PyPI through Trusted Publishing.
- Runtime behavior remains compatible with v0.6.0; this release focuses on reproducible demos, distribution validation, and secure publishing infrastructure.

## [0.6.0] - 2026-09-19

First public release candidate of the project as a reusable AI-agent evaluation harness.

### Added

- Deterministic command evaluation using exit codes, stdout, stderr, generated files, and timeouts.
- Input-file fixtures with workspace path-safety checks.
- Repeated benchmark runs with per-task reliability metrics.
- Tag-based benchmark filtering.
- Deterministic parallel execution with isolated temporary workspaces.
- Generic JSON-configured adapters for prompt-driven command-line agents.
- Benchmark labels and multi-report comparison.
- Standalone HTML benchmark and comparison reports.
- JUnit XML output for CI-native test reporting.
- No-execution benchmark validation through `agent-eval-validate`.
- Draft 2020-12 JSON Schema for benchmark definitions.
- A reusable composite GitHub Action for running benchmarks in other repositories.
- A five-task starter benchmark covering stdout, stderr, exit codes, fixtures, tags, and nested artifacts.
- Optional benchmark metadata: name, version, and description.
- Canonical SHA-256 task fingerprints for reproducibility and provenance-aware comparisons.

### CLI

```bash
agent-eval-validate examples/starter-benchmark.json

agent-eval examples/starter-benchmark.json \
  --runs 3 \
  --parallel 2 \
  --output reports/results.json \
  --html-output reports/results.html \
  --junit-output reports/results.xml

agent-eval-compare \
  reports/agent-a.json \
  reports/agent-b.json \
  --html-output reports/comparison.html
```

### Compatibility

- Python 3.10, 3.11, and 3.12 are covered by CI.
- Runtime dependencies remain standard-library only.
- Existing single-run command-based benchmark files remain supported.
