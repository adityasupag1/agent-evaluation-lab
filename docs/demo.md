# End-to-end demo

This demo exercises the complete prompt-agent pipeline without external APIs, credentials, or network calls.

It intentionally uses two deterministic fixture agents:

- **demo-reference** implements all five expected behaviors.
- **demo-partial** implements the first three behaviors and intentionally omits two behaviors.

These fixture scores demonstrate the evaluation and comparison workflow. They are **not** scores for Claude, Codex, Gemini, or any other LLM.

## Run locally

```bash
python -m pip install -e ".[dev]"

agent-eval-validate examples/agent-demo-benchmark.json

agent-eval examples/agent-demo-benchmark.json \
  --agent-config examples/agents/demo-reference.json \
  --label demo-reference \
  --output demo-results/reference.json \
  --html-output demo-results/reference.html

agent-eval examples/agent-demo-benchmark.json \
  --agent-config examples/agents/demo-partial.json \
  --label demo-partial \
  --output demo-results/partial.json \
  --html-output demo-results/partial.html

agent-eval-compare \
  demo-results/reference.json \
  demo-results/partial.json \
  --output demo-results/comparison.json \
  --html-output demo-results/comparison.html
```

The partial adapter is expected to exit with status `1` because two tasks fail.

## Expected deterministic result

| Adapter | Passed | Failed | Pass rate |
| --- | ---: | ---: | ---: |
| demo-reference | 5 | 0 | 100% |
| demo-partial | 3 | 2 | 60% |

Both reports carry the same benchmark SHA-256 fingerprint, proving that the comparison used the same task definitions.

The [end-to-end demo workflow](../.github/workflows/demo.yml) reruns this demonstration in GitHub Actions and uploads the JSON, HTML, and JUnit reports as a workflow artifact.
