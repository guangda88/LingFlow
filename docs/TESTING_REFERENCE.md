# Testing Reference

> Extracted from AGENTS.md on 2026-05-06. Source: `docs/AGENTS_ARCHIVE_20260506.md`

## Framework

Pytest-based with `.pytest.ini` configuration:

```ini
[pytest]
python_files = test_*.py
asyncio_mode = auto
markers = unit, snapshot, scenario, e2e, ci, slow
```

## Test Markers

| Marker | Purpose |
|--------|---------|
| `unit` | Unit tests |
| `snapshot` | Snapshot/regression tests |
| `scenario` | Scenario-based tests |
| `e2e` | End-to-end tests |
| `ci` | CI/CD integration tests |
| `slow` | Slow running tests |

## Test Structure

```
lingflow/testing/
├── unit/          # Unit test utilities
├── e2e/           # E2E test utilities
├── snapshot/      # Snapshot testing
├── scenarios/     # Scenario definitions
├── fixtures/      # Shared fixtures
├── ci/            # CI configuration
tests/             # Root test directory
```

## CI Pipelines (`.github/workflows/`)

1. **ci.yml** — Main CI pipeline
2. **code-quality.yml** — Code quality + security scanning
3. **testing-framework.yml** — Comprehensive test execution

## Common Test Commands

```bash
pytest                           # Run full test suite
pytest -m unit                   # Unit tests only
pytest -m e2e                    # End-to-end tests
pytest -m "not slow"             # Skip slow tests
pytest --cov=lingflow            # With coverage
pytest -n auto                   # Parallel execution (pytest-xdist)
python verify_system_simple.py   # Quick system verification
python test_comprehensive.py     # Comprehensive test
```
