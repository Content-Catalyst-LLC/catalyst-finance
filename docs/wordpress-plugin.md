# WordPress Plugin

Build with:

```bash
python scripts/build_plugin.py --versioned-copy
```

## Shortcodes

Persistent multi-scenario workspace:

```text
[catalyst_finance_workspace]
```

The original shortcode now opens the same workspace experience:

```text
[catalyst_finance_demo]
```

Read-only public example:

```text
[catalyst_finance_demo mode="public"]
```

## Browser persistence

The workspace uses `localStorage`, keeps a separate recovery copy for interrupted work, warns before leaving with unsaved changes, and supports complete JSON import/export. Data is local to the current browser and is not synchronized to WordPress or the Catalyst Finance API.
