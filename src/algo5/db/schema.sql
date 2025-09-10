PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS market_data (
  symbol   TEXT NOT NULL,
  ts       TIMESTAMP NOT NULL,
  open     REAL,
  high     REAL,
  low      REAL,
  close    REAL,
  volume   INTEGER,
  PRIMARY KEY (symbol, ts)
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS features (
  symbol   TEXT NOT NULL,
  ts       TIMESTAMP NOT NULL,
  name     TEXT NOT NULL,
  version  INTEGER NOT NULL DEFAULT 1,
  value    REAL,
  PRIMARY KEY (symbol, ts, name, version)
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS runs (
  run_id     TEXT PRIMARY KEY,
  strategy   TEXT NOT NULL,
  symbols    TEXT NOT NULL,          -- JSON array
  start_ts   TIMESTAMP,
  end_ts     TIMESTAMP,
  params     TEXT,                   -- JSON
  metrics    TEXT,                   -- JSON
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS watchlist (
  symbol     TEXT PRIMARY KEY,
  active     INTEGER NOT NULL DEFAULT 1,
  source     TEXT NOT NULL DEFAULT 'manual',
  added_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS orders (
  order_id   TEXT PRIMARY KEY,
  run_id     TEXT NOT NULL,
  symbol     TEXT NOT NULL,
  side       TEXT NOT NULL,          -- buy|sell
  qty        REAL NOT NULL,
  type       TEXT NOT NULL,          -- market|limit|stop|stop_limit
  limit_price REAL,
  stop_price  REAL,
  status     TEXT NOT NULL DEFAULT 'new',
  ts         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (run_id) REFERENCES runs(run_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS fills (
  fill_id    TEXT PRIMARY KEY,
  order_id   TEXT NOT NULL,
  ts         TIMESTAMP NOT NULL,
  qty        REAL NOT NULL,
  price      REAL NOT NULL,
  FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
);
