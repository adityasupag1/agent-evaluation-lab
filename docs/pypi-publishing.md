# PyPI publishing

Agent Evaluation Lab is prepared for PyPI Trusted Publishing through GitHub Actions. No long-lived PyPI API token is stored in the repository.

## One-time PyPI setup

If the project does not exist on PyPI yet, create a **pending GitHub publisher** in your PyPI account with these exact values:

| Field | Value |
| --- | --- |
| PyPI project name | `agent-evaluation-lab` |
| GitHub owner | `adityasupag1` |
| Repository name | `agent-evaluation-lab` |
| Workflow filename | `release.yml` |
| Environment name | `pypi` |

PyPI can create the project automatically on the first successful trusted publish. A pending publisher does not reserve the project name until that first upload succeeds.

## One-time GitHub setup

Create a GitHub Actions environment named `pypi`:

1. Open **Settings → Environments** in the repository.
2. Create an environment named exactly `pypi`.
3. Optionally add a required reviewer so every package publication needs explicit approval.

The workflow requests `id-token: write` only in the publish job. The build job does not receive OIDC publishing permission.

## Release flow

Publishing is triggered only when a GitHub Release is published.

Before creating a release, update the package version in:

- `pyproject.toml`
- `src/agent_eval/__init__.py`
- `CHANGELOG.md`

Then create a GitHub release whose tag exactly matches the package version, for example:

```text
Package version: 0.7.0
Git tag:         v0.7.0
```

The release workflow will:

1. check out the exact release tag;
2. reject a tag/version mismatch;
3. build wheel and source distributions;
4. validate them with Twine;
5. pass only the built distributions to the publishing job;
6. obtain a short-lived PyPI credential through GitHub OIDC;
7. publish the distributions to PyPI.

## Security notes

- Do not add a `PYPI_TOKEN` secret for this workflow.
- Keep `.github/workflows/release.yml` narrowly scoped and review changes to it carefully.
- Keep the `pypi` GitHub environment name synchronized with the PyPI Trusted Publisher configuration.
- Prefer protected release processes and environment approval for production publishing.
