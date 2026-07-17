# Repository Architecture

The v1.1.0 architecture has one contract and two calculation runtimes.

- `catalyst_finance/models.py`: validated contracts and structured issues
- `catalyst_finance/calculation.py`: pure financial calculations and score trace
- `catalyst_finance/interpretation.py`: review flags and concern level
- `catalyst_finance/narrative.py`: decision note and responsible-use boundary
- `catalyst_finance/migration.py`: v1.0.0 normalization
- `catalyst_finance/engine.py`: orchestration and publication
- `catalyst_finance/registry.py`: stable model metadata
- `catalyst_finance/api.py`: HTTP system, registry, and evaluation boundary
- `wordpress/.../catalyst-finance-engine.js`: contract-equivalent browser engine
- `wordpress/.../catalyst-finance-demo.js`: presentation-only browser UI
- `schemas/`: generated versioned JSON Schemas
- `scripts/browser_parity.js`: Node parity runner

The JavaScript engine is independently implemented but contract-tested against Python fixtures. UI code does not contain financial formulas.
