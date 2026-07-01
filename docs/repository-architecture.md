# Repository Architecture

Catalyst Finance is organized as a small reproducible project:

- `python/` contains the scenario engine.
- `schemas/` defines export shape and validation expectations.
- `data/` stores sample input data.
- `examples/` stores example generated outputs.
- `docs/` explains methodology and review logic.
- `tests/` protects core calculations.
- `wordpress/` contains the public online demo plugin.

The WordPress demo and Python engine intentionally share a similar calculation model so public-facing exploration and reproducible repository artifacts remain aligned.
