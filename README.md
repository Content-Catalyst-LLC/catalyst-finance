# Catalyst Finance

An open-source portfolio analytics backend (Flask) for builders—transactions ledger (±shares), positions & cash, optional FIFO cost basis, provider-agnostic market-data adapters, and a pluggable **Narrative Risk** module.

> **Disclaimer:** Educational software; not investment advice.

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
export FLASK_APP=app.py
flask run
```

## API
- `GET /healthz` → `{"ok": true}`

## Tests
```bash
pytest -q
```

## License
MIT — see `LICENSE`.
