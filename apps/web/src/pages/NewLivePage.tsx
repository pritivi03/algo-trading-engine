import { lazy, Suspense, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "../api/client";

const MonacoEditor = lazy(() => import("@monaco-editor/react"));

const DEFAULTS = {
  symbol: "BTC/USD",
  max_pos_size: "1",
  max_notional_per_trade: "10000",
  strategy_params: JSON.stringify({ short_window: 5, long_window: 20 }, null, 2),
};

export default function NewLivePage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const p = (key: string, fallback: string) => searchParams.get(key) ?? fallback;

  const [paper, setPaper] = useState(p("paper", "true") !== "false");
  const [strategyId, setStrategyId] = useState(p("strategy_id", ""));
  const [symbol, setSymbol] = useState(p("symbol", DEFAULTS.symbol));
  const [maxPos, setMaxPos] = useState(p("max_pos_size", DEFAULTS.max_pos_size));
  const [maxNotional, setMaxNotional] = useState(p("max_notional_per_trade", DEFAULTS.max_notional_per_trade));
  const [strategyParams, setStrategyParams] = useState(p("strategy_params", DEFAULTS.strategy_params));
  const [paramsError, setParamsError] = useState("");

  const { data: strategies } = useQuery({
    queryKey: ["strategies"],
    queryFn: api.strategies.list,
  });

  const { data: balance, isLoading: balanceLoading, refetch: refetchBalance } = useQuery({
    queryKey: ["account-balance", paper],
    queryFn: () => api.account.balance(paper),
    retry: false,
  });

  const selectedStrategy = strategies?.find((s) => s.id === strategyId);
  const selectedCode = selectedStrategy?.code ?? "# Select a strategy above to preview its code.";

  const mutation = useMutation({
    mutationFn: async () => {
      if (!balance) throw new Error("Could not fetch account balance");
      let params: Record<string, unknown>;
      try {
        params = JSON.parse(strategyParams);
      } catch {
        throw new Error("Strategy params must be valid JSON");
      }
      const run = await api.runs.create({
        strategy_id: strategyId,
        symbol,
        mode: paper ? "paper" : "live",
        initial_capital: balance.portfolio_value,
        strategy_params: params,
        risk_config: {
          max_pos_size: Number(maxPos),
          max_notional_per_trade: Number(maxNotional),
        },
        market_data_config: { source: "live", timeframe: "minute" },
      });
      await api.runs.start(run.id);
      return run;
    },
    onSuccess: (run) => navigate(`/sessions/${run.id}`),
    onError: (err: Error) => setParamsError(err.message),
  });

  const inputCls =
    "w-full bg-gray-900 border border-gray-700 rounded-md px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-indigo-500";
  const labelCls = "block text-xs text-gray-400 mb-1";

  return (
    <div className="max-w-2xl">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => navigate("/sessions")} className="text-gray-500 hover:text-gray-300 text-sm">
          ← Sessions
        </button>
        <h1 className="text-2xl font-semibold">New Live Session</h1>
      </div>

      {/* Paper / Live toggle */}
      <div className="flex items-center gap-3 mb-6 p-4 bg-gray-900 border border-gray-800 rounded-lg">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-200">Paper Trading</p>
          <p className="text-xs text-gray-500 mt-0.5">
            {paper
              ? "Simulated orders on real prices. Safe to experiment."
              : "Real orders with real money. Be careful."}
          </p>
        </div>
        <button
          onClick={() => setPaper(!paper)}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
            paper ? "bg-yellow-500" : "bg-red-600"
          }`}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
              paper ? "translate-x-1" : "translate-x-6"
            }`}
          />
        </button>
        <span className={`text-xs font-mono font-semibold w-12 ${paper ? "text-yellow-400" : "text-red-400"}`}>
          {paper ? "PAPER" : "LIVE"}
        </span>
      </div>

      <div className="space-y-5">
        <div>
          <label className={labelCls}>Strategy</label>
          <select
            value={strategyId}
            onChange={(e) => {
              const id = e.target.value;
              setStrategyId(id);
              const strat = strategies?.find((s) => s.id === id);
              if (strat && Object.keys(strat.default_params).length > 0) {
                setStrategyParams(JSON.stringify(strat.default_params, null, 2));
              }
            }}
            className={inputCls}
          >
            <option value="">Select a strategy…</option>
            {strategies?.map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
        </div>

        <div>
          <label className={labelCls}>Symbol</label>
          <input
            className={inputCls}
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            placeholder="BTC/USD, ETH/USD, AAPL…"
          />
          <p className="text-xs text-gray-600 mt-1">Use BTC/USD format for crypto (24/7). Equity symbols use market hours.</p>
        </div>

        {/* Account balance — fetched, read-only */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className={labelCls + " mb-0"}>Starting Capital (from Alpaca account)</label>
            <button
              onClick={() => refetchBalance()}
              className="text-xs text-indigo-400 hover:text-indigo-300"
            >
              ↻ Refresh
            </button>
          </div>
          {balanceLoading ? (
            <div className={`${inputCls} text-gray-500`}>Fetching from Alpaca…</div>
          ) : balance ? (
            <div className={`${inputCls} bg-gray-800/50 text-gray-300 flex items-center justify-between`}>
              <span>${balance.portfolio_value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
              <span className="text-xs text-gray-500">Cash: ${balance.cash.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
            </div>
          ) : (
            <div className={`${inputCls} text-red-400 text-xs`}>
              Could not fetch balance. Check ALPACA_{paper ? "PAPER_" : ""}API_KEY env vars.
            </div>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelCls}>Max Position Size (shares/units)</label>
            <input className={inputCls} value={maxPos} onChange={(e) => setMaxPos(e.target.value)} type="number" />
          </div>
          <div>
            <label className={labelCls}>Max Notional Per Trade ($)</label>
            <input className={inputCls} value={maxNotional} onChange={(e) => setMaxNotional(e.target.value)} type="number" />
          </div>
        </div>

        <div>
          <label className={labelCls}>Strategy Params (JSON)</label>
          <textarea
            className={`${inputCls} font-mono h-24 resize-none`}
            value={strategyParams}
            onChange={(e) => setStrategyParams(e.target.value)}
          />
        </div>

        <div>
          <label className={labelCls}>Strategy Code Preview</label>
          <div className="rounded-md overflow-hidden border border-gray-700 h-48">
            <Suspense fallback={<div className="h-full bg-gray-900 flex items-center justify-center text-gray-500 text-sm">Loading editor…</div>}>
              <MonacoEditor
                height="100%"
                language="python"
                value={selectedCode}
                theme="vs-dark"
                options={{ readOnly: true, minimap: { enabled: false }, fontSize: 12, lineNumbers: "off" }}
              />
            </Suspense>
          </div>
        </div>

        {paramsError && <p className="text-red-400 text-sm">{paramsError}</p>}

        {!paper && (
          <div className="p-3 bg-red-900/20 border border-red-800 rounded-md text-red-400 text-xs">
            ⚠ Live mode places real orders with real money. Double-check your strategy and risk params before launching.
          </div>
        )}

        <button
          onClick={() => mutation.mutate()}
          disabled={!strategyId || !balance || mutation.isPending}
          className={`w-full py-2.5 disabled:opacity-50 disabled:cursor-not-allowed rounded-md text-sm font-medium transition-colors ${
            paper
              ? "bg-yellow-600 hover:bg-yellow-500 text-white"
              : "bg-red-700 hover:bg-red-600 text-white"
          }`}
        >
          {mutation.isPending
            ? "Launching…"
            : paper
            ? "Start Paper Session"
            : "Start Live Session"}
        </button>
      </div>
    </div>
  );
}