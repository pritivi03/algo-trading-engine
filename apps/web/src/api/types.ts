export type RunStatus = "pending" | "running" | "completed" | "failed";

export interface Strategy {
  id: string;
  name: string;
  code: string;
  default_params: Record<string, unknown>;
  created_at: string;
}

export interface Run {
  id: string;
  strategy_id: string;
  status: RunStatus;
  container_id: string | null;
  error_message: string | null;
  config: RunConfig;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  current_equity: number | null;
}

export interface RunConfig {
  run_id: string;
  strategy_id: string;
  symbol: string;
  mode: string;
  initial_capital: number;
  strategy_params: Record<string, unknown>;
  risk_config: { max_pos_size: number; max_notional_per_trade: number };
  market_data_config: {
    source: string;
    start_date: string;
    end_date: string;
    timeframe: string;
  };
}

export interface Metrics {
  run_id: string;
  total_return_pct: number;
  sharpe_ratio: number;
  max_drawdown_pct: number;
  win_rate: number;
  total_trades: number;
  avg_win: number;
  avg_loss: number;
  final_cash: number;
  final_equity: number;
  realized_pnl: number;
  unrealized_pnl: number;
  updated_at: string;
}

export interface Fill {
  id: string;
  order_id: string;
  symbol: string;
  side: string;
  qty: number;
  fill_price: number;
  fees: number;
  timestamp: string;
}

export interface EquitySnapshot {
  timestamp: string;
  equity: number;
  cash: number;
}

export interface AccountBalance {
  portfolio_value: number;
  cash: number;
}

export interface CreateRunPayload {
  strategy_id: string;
  symbol: string;
  mode: string;
  initial_capital: number;
  strategy_params: Record<string, unknown>;
  risk_config: { max_pos_size: number; max_notional_per_trade: number };
  market_data_config: {
    source: string;
    start_date?: string;
    end_date?: string;
    timeframe?: string;
  };
}