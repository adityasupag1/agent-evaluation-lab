# Contributing

Contributions are welcome. Keep changes focused, testable, and easy to review.

## Development setup

```bash
python -m pip install -e ".[dev]"
pytest -q
```

Before opening a pull request, make sure the test suite passes on a supported Python version.

## Pull requests

- Explain the observable behavior being added or changed.
- Add or update tests for behavior changes.
- Prefer deterministic tests over timing-sensitive or implementation-specific assertions.
- Keep unrelated refactors out of focused fixes.
- Do not commit generated reports, virtual environments, credentials, or secrets.

Bug reports should include a minimal task definition, expected behavior, actual behavior, Python version, and operating system when relevant.
