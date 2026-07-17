# Repository Architecture

Catalyst Finance v1.0.1 establishes one package and application boundary.

## Canonical source

- `catalyst_finance/domain.py` contains the screening calculation model.
- `catalyst_finance/io.py` contains scenario loading and Markdown rendering.
- `catalyst_finance/cli.py` provides the primary scenario command.
- `catalyst_finance/api.py` provides the FastAPI application factory.
- `catalyst_finance/elasticity.py` contains the isolated legacy demand and elasticity utility.
- `catalyst_finance/version.py` is the Python version surface.

The `python/` directory is a backward-compatible wrapper only. New code should import from `catalyst_finance`.

## Contracts

- `VERSION`, `pyproject.toml`, package metadata, plugin metadata, manifest, schema, and examples must report the same release.
- `schemas/finance_scenario.schema.json` validates the checked-in scenario export.
- `.github/workflows/ci.yml` is the only CI workflow.
- `scripts/check_release.py` is the release gate.
- `scripts/build_plugin.py` builds a deterministic WordPress ZIP.
- `scripts/reproduce_examples.py` verifies checked-in outputs from a fixed timestamp.

## Generated artifacts

Generated elasticity CSV files and plots are examples under `examples/elasticity/`. New local output belongs under ignored `outputs/` or `dist/`; it must not be committed as runtime state.
