# Algo Trading Engine

An event-driven backtesting and paper trading platform. Submit a strategy, configure a run, and the engine executes it inside an isolated Docker container — persisting fills, positions, and performance metrics to Postgres, queryable via a REST control plane.

Built to explore the systems design problems at the core of quantitative trading infrastructure: event sequencing, execution abstraction, risk filtering, and accurate PnL accounting.

---

## Dashboard

<img alt="Screen Recording 2026-04-19 at 6 42 29 PM" src="https://github.com/user-attachments/assets/b05f75b8-5242-458c-aa8e-83aba267654b" />

<p align="center"><i>Event-driven backtesting engine with live equity curve, Sharpe ratio, max drawdown, and win rate — computed bar-by-bar</i></p>

<img width="1726" height="960" alt="Screenshot 2026-04-19 at 6 38 17 PM" src="https://github.com/user-attachments/assets/206c4e3f-6791-425d-85c1-0fe62349fb34" />

<p align="center"><i>Monaco-powered strategy editor — write Python strategies that plug directly into the backtest and live trading engine</i></p>

<img width="1726" height="960" alt="Screenshot 2026-04-19 at 6 48 27 PM" src="https://github.com/user-attachments/assets/cfad136b-f81d-4667-a647-a9e2d7912803" />

<p align="center"><i>Paper and live trading via Alpaca — configurable position sizing, notional limits, and one-click deploy to an isolated Docker container with real-time equity tracking</i></p>

---

## Architecture

The system splits into two processes: a **control plane** that manages run lifecycle and a **runtime container** that executes the strategy. They share no direct network connection — all coordination happens through Postgres.

```
[ React Dashboard ]
        ↓
[ FastAPI Control Plane ]  ──────────────────────────────────┐
        ↓ Docker SDK                                         │
[ Runtime Container (one per run) ]                   [ PostgreSQL ]
        ↓                                                    │
[ TradingEngine (event loop) ]  ────────────────────────────┘
    ├── MarketDataAdapter (Alpaca REST)
    ├── Strategy (user-submitted code)
    ├── RiskManager (pluggable rules)
    ├── ExecutionAdapter (simulated / broker)
    └── PortfolioTracker + MetricsEngine
```

The engine runs a typed event queue — `MarketEvent → SignalEvent → OrderEvent → FillEvent` — processed in strict FIFO order. The same strategy code runs in both backtest and paper trading modes; only the execution and data adapters swap out.

---

## Features

**Engine**
- In-process event queue (`deque`) with typed domain events; deterministic replay for reproducibility
- `BaseStrategy` ABC — strategies implement a single `on_market_event()` hook
- `SimulatedExecutionAdapter` fills at bar close; `LiveExecutionAdapter` stub ready for broker integration
- Dynamic strategy loading via `exec()` inside the container (security boundary = container)

**Risk**
- Pluggable `RiskManager` evaluates `SignalEvent`s before order submission
- Built-in rules: max position size, max notional per trade, sufficient cash check
- Config-driven thresholds per run via `RiskConfig`

**Portfolio & Metrics**
- FIFO lot tracking for exact realized PnL per closed position (no cost-basis averaging)
- Online Sharpe computation (Welford's algorithm) — no full history scan
- Metrics persisted at run end: total return, annualized Sharpe, max drawdown, win rate, avg win/loss

**Persistence**
- `strategies` — user/built-in strategy source code
- `strategy_runs` — run metadata, config (JSONB), container ID, status lifecycle
- `fills` — execution records per order, indexed by timestamp
- `run_metrics` — summary analytics per completed run
- Repository pattern over SQLAlchemy for typed, session-scoped access

**Control Plane**
- `POST /strategies`, `GET /strategies` — strategy management
- `POST /runs`, `GET /runs/{id}` — run lifecycle
- `POST /runs/{id}/start` — launches runtime container via Docker SDK, injects env (run ID, DB URL, API keys)
- `POST /runs/{id}/stop` — terminates container

---

## Stack

| Layer | Technology |
|---|---|
| API | FastAPI 0.115+ |
| ORM / DB | SQLAlchemy 2.0, PostgreSQL 16 |
| Validation | Pydantic v2 |
| Market data | Alpaca Python SDK (historical bars) |
| Container orchestration | docker-py (Docker SDK) |
| Package management | uv |
| Infrastructure | Docker Compose (local dev) |
| Dashboard (planned) | React |

---

## Design Decisions

**Database as coordination layer** — the runtime container writes state directly to Postgres; the control plane reads it. No message broker, no internal RPC. Simpler failure model and easier to inspect.

**Per-run container isolation** — each strategy run gets its own container instance. Prevents shared state bugs across concurrent runs and gives a clean lifecycle (pending → running → completed/failed) with no zombie processes.

**Adapter pattern for execution** — `BaseExecutionAdapter` abstracts `submit_order()`. Backtest mode fills at close price with zero latency; live mode will hit the broker paper endpoint. Strategy code is unaware of which adapter is active.

**In-process event queue** — using a `deque` instead of Redis or Kafka keeps the engine deterministic and dependency-free. The tradeoff (no persistence of in-flight events) is acceptable for minute-bar strategies where the bar stream is the source of truth.

**FIFO lot tracking** — position tracking uses a deque of lots per symbol. Realized PnL is computed lot-by-lot on close, giving accounting-accurate results rather than average cost basis.

**Online metrics** — Welford's algorithm computes rolling mean and variance for Sharpe without storing the full equity history in memory.

---

## Getting Started

```bash
# copy and fill in credentials
cp docker/.env.example docker/.env

# start postgres, api, and adminer
docker compose -f docker/docker-compose.yml up -d

# seed built-in strategies
uv run python scripts/seed_strategies.py

# create and launch a test run
uv run python scripts/create_run.py
```

The API is available at `http://localhost:8080`. Adminer (DB UI) at `http://localhost:8888`.

---

## Project Layout

```
algo-trading-engine/
├── apps/
│   ├── api/                  # FastAPI control plane (routes, schemas, launcher)
│   └── runtime/              # Container entrypoint + engine factory
│
├── trading/
│   ├── core/                 # Domain models, events, enums, run config
│   ├── runtime/              # TradingEngine (event loop)
│   ├── strategies/           # BaseStrategy ABC, loader, built-in seeds
│   ├── execution/            # Simulated + live execution adapters
│   ├── market_data/          # Historical + live market data adapters
│   ├── risk/                 # RiskManager + pluggable rule implementations
│   ├── portfolio/            # PortfolioTracker (FIFO lots)
│   ├── metrics/              # MetricsEngine (online computation)
│   └── persistence/          # ORM models, session factory, repositories
│
├── docker/
│   ├── Dockerfile.api
│   ├── Dockerfile.runtime
│   ├── docker-compose.yml
│   └── .env.example
│
└── scripts/                  # Seed strategies, create test runs
```
