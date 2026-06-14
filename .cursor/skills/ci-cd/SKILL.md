---
name: ci-cd
description: >-
  Manages CI/CD for myAlgo2: GitHub Actions, pytest, ruff, Makefile, and PR
  workflows. Use when the user mentions CI, CD, tests, lint, GitHub Actions,
  make check, pull request checks, or pipeline setup.
---

# CI/CD Skill — myAlgo2

## Quick commands

```bash
make install-dev   # one-time setup
make check         # lint + test + compile (CI gate)
make lint          # ruff only
make test          # pytest only
```

## CI pipeline

File: `.github/workflows/ci.yml`

| Step | Tool | Scope |
|------|------|-------|
| Lint | ruff | `src/`, `tests/`, `scripts/` |
| Compile | compileall | `src/`, `scripts/` |
| Test | pytest | unit tests only |

**Not in CI:** Futu OpenD integration (requires local gateway + credentials).

## Adding tests

1. Create `tests/test_<feature>.py`
2. Test pure logic — mock broker, no network
3. Run `make test`
4. New strategy **must** have a test file

## PR workflow

1. Branch from `main`
2. `make check` passes
3. Update [TASKS.md](../../TASKS.md) for completed task IDs
4. Open PR — template at `.github/pull_request_template.md`

## Config files

| File | Purpose |
|------|---------|
| `pyproject.toml` | pytest + ruff config |
| `requirements-dev.txt` | pytest, ruff |
| `Makefile` | local CI shortcuts |

## When modifying CI

- Keep matrix Python 3.10–3.12
- Do not add Futu secrets to GitHub Actions
- Integration tests with OpenD = separate optional workflow (manual dispatch only)
