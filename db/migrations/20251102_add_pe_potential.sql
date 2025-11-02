CREATE INDEX IF NOT EXISTS ix_metrics_ticker_metric_asof ON metrics(ticker, metric_type, asof);

CREATE TABLE IF NOT EXISTS scenarios (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ticker VARCHAR(16) NOT NULL,
  scenario_type VARCHAR(64) NOT NULL,
  asof DATE NOT NULL,
  payload TEXT NOT NULL,
  method VARCHAR(64) NOT NULL,
  version VARCHAR(16) NOT NULL DEFAULT 'v1',
  source VARCHAR(64) NOT NULL DEFAULT 'catalyst-finance'
);

CREATE INDEX IF NOT EXISTS ix_scenarios_ticker_type_asof
  ON scenarios(ticker, scenario_type, asof);
