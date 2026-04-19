import { lazy, Suspense, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "../api/client";

const MonacoEditor = lazy(() => import("@monaco-editor/react"));

const DEFAULTS = {
  symbol: "AAPL",
  initial_capital: "100000",
  start_date: "2021-07-01",
  end_date: "2021-10-01",
  strategy_params: JSON.stringify({ short_window: 5, long_window: 20 }, null, 2),
  max_pos_size: "100",
  max_notional_per_trade: "50000",
};

export default function NewSessionPage() {
  const navigate = useNavigate();
  const [strategyId, setStrategyId] = useState("");
  const [symbol, setSymbol] = useState(DEFAULTS.symbol);
  const [capital, setCapital] = useState(DEFAULTS.initial_capital);
  const [startDate, setStartDate] = useState(DEFAULTS.start_date);
  const [endDate, setEndDate] = useState(DEFAULTS.end_date);
  const [strategyParams, setStrategyParams] = useState(DEFAULTS.strategy_params);
  const [maxPos, setMaxPos] = useState(DEFAULTS.max_pos_size);
  const [maxNotional, setMaxNotional] = useState(DEFAULTS.max_notional_per_trade);
  const [paramsError, setParamsError] = useState("");

  const { data: strategies } = useQuery({
    queryKey: ["strategies"],
    queryFn: api.strategies.list,
  });

  const selectedCode =
    strategies?.find((s) => s.id === strategyId)?.code ??
    "# Select a strategy above to preview its code.";

  const mutation = useMutation({
    mutationFn: async () => {
      let params: Record<string, unknown>;
      try {
        params = JSON.parse(strategyParams);
      } catch {
        throw new Error("Strategy params must be valid JSON");
      }
      const run = await api.runs.create({
        strategy_id: strategyId,
        symbol,
        mode: "backtest",
        initial_capital: Number(capital),
        strategy_params: params,
        risk_config: {
          max_pos_size: Number(maxPos),
          max_notional_per_trade: Number(maxNotional),
        },
        market_data_config: {
          source: "historical",
          start_date: `${startDate}T00:00:00`,
          end_date: `${endDate}T00:00:00`,
        },
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
        <button
          onClick={() => navigate("/sessions")}
          className="text-gray-500 hover:text-gray-300 text-sm"
        >
          ← Sessions
        </button>
        <h1 className="text-2xl font-semibold">Launch Backtest</h1>
      </div>

      <div className="space-y-5">
        <div>
          <label className={labelCls}>Strategy</label>
          <select
            value={strategyId}
            onChange={(e) => setStrategyId(e.target.value)}
            className={inputCls}
          >
            <option value="">Select a strategy…</option>
            {strategies?.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelCls}>Symbol</label>
            <input className={inputCls} value={symbol} onChange={(e) => setSymbol(e.target.value)} />
          </div>
          <div>
            <label className={labelCls}>Initial Capital ($)</label>
            <input className={inputCls} value={capital} onChange={(e) => setCapital(e.target.value)} type="number" />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelCls}>Start Date</label>
            <input className={inputCls} value={startDate} onChange={(e) => setStartDate(e.target.value)} type="date" />
          </div>
          <div>
            <label className={labelCls}>End Date</label>
            <input className={inputCls} value={endDate} onChange={(e) => setEndDate(e.target.value)} type="date" />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelCls}>Max Position Size (shares)</label>
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

        {paramsError && (
          <p className="text-red-400 text-sm">{paramsError}</p>
        )}

        <button
          onClick={() => mutation.mutate()}
          disabled={!strategyId || mutation.isPending}
          className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-md text-sm font-medium transition-colors"
        >
          {mutation.isPending ? "Launching…" : "Launch Backtest"}
        </button>
      </div>
    </div>
  );
}