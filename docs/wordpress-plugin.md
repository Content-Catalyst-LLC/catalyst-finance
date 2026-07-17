# WordPress Plugin

The plugin source is located at `wordpress/catalyst-finance-demo/`.

Build it with:

```bash
python scripts/build_plugin.py --versioned-copy
```

This creates:

- `dist/catalyst-finance.zip`
- `dist/catalyst-finance-demo-v1.0.1.zip`

Both packages contain one top-level `catalyst-finance-demo/` directory. The plugin registers `[catalyst_finance_demo]`, performs calculations locally in the browser, and does not submit visitor inputs to Sustainable Catalyst.

The browser model remains a public demonstration surface. Cross-runtime calculation parity is scheduled for v1.1.0.
