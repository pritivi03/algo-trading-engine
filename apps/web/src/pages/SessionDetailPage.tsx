import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid,
} from "recharts";
import { api } from "../api/client";
import StatusBadge from "../components/StatusBadge";
import type { RunStatus } from "../api/types";

function fmt(dt: string | null, opts?: Intl.DateTimeFormatOptions) {
  if (!dt) return "—";
  return new Date(dt).toLocaleString(undefined, opts ?? { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function MetricCard({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className={`text-lg font-semibold ${accent ?? ""}`}>{value}</p>
    </div>
  );
}

export default function SessionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [tab, setTab] = useState<"overview" | "fills">("overview");

  const isActive = (s: RunStatus) => s === "pending" || s === "running";

  const { data: run } = useQuery({
    queryKey: ["run", id],
    queryFn: () => api.runs.get(id!),
    refetchInterval: (q) =>
      q.state.data && isActive(q.state.data.status as RunStatus) ? 2000 : false,
  });

  const { data: strategy } = useQuery({
    queryKey: ["strategy", run?.strategy_id],
    queryFn: () => api.strategies.get(run!.strategy_id),
    enabled: !!run?.strategy_id,
  });

  const { data: metrics } = useQuery({
    queryKey: ["metrics", id],
    queryFn: () => api.runs.metrics(id!),
    enabled: run?.status === "completed",
    retry: false,
  });

  const { data: fills } = useQuery({
    queryKey: ["fills", id],
    queryFn: () => api.runs.fills(id!),
    enabled: tab === "fills",
  });

  const { data: equitySnapshots } = useQuery({
    queryKey: ["equity", id],
    queryFn: () => api.runs.equitySnapshots(id!),
    enabled: run?.status === "completed",
  });

  if (!run) return <p className="text-gray-500 text-sm">Loading…</p>;

  const cfg = run.config;
  const pnlColor = (v: number) => v >= 0 ? "text-emerald-400" : "text-red-400";

  return (
    <div className="max-w-5xl">
      {/* Header */}
      <div className="mb-1">
        <button onClick={() => navigate("/sessions")} className="text-gray-500 hover:text-gray-300 text-xs mb-3 inline-block">
          ← Sessions
        </button>
        <div className="flex items-center gap-3 mb-1">
          <span className="font-mono text-2xl font-semibold tracking-tight">{run.id}</span>
          <StatusBadge status={run.status as RunStatus} />
        </div>
        <div className="flex items-center gap-4 text-sm text-gray-400 flex-wrap">
          {strategy && (
            <Link
              to={`/strategies/${run.strategy_id}`}
              onClick={(e) => e.stopPropagation()}
              className="text-indigo-400 hover:text-indigo-300 font-medium"
            >
              {strategy.name}
            </Link>
          )}
          <span className="font-mono font-semibold text-gray-200">{cfg.symbol}</span>
          <span className="capitalize">{cfg.mode}</span>
          <span>${cfg.initial_capital.toLocaleString()}</span>
          <span>{cfg.market_data_config.start_date.slice(0, 10)} → {cfg.market_data_config.end_date.slice(0, 10)}</span>
          <span className="font-mono text-xs bg-gray-800 px-2 py-0.5 rounded">{JSON.stringify(cfg.strategy_params)}</span>
        </div>
        <div className="flex items-center gap-4 text-xs text-gray-600 mt-1.5">
          <span>Created {fmt(run.created_at)}</span>
          {run.started_at && <><span>·</span><span>Started {fmt(run.started_at)}</span></>}
          {run.completed_at && <><span>·</span><span>Completed {fmt(run.completed_at)}</span></>}
        </div>
        {run.error_message && (
          <div className="mt-3 p-3 bg-red-900/20 border border-red-800 rounded-md text-red-400 text-xs font-mono">
            {run.error_message}
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mt-6 mb-5 border-b border-gray-800">
        {(["overview", "fills"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium capitalize transition-colors ${
              tab === t ? "border-b-2 border-indigo-500 text-white" : "text-gray-500 hover:text-gray-300"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "overview" && (
        <>
          {run.status === "completed" && metrics ? (
            <div className="space-y-5">
              {equitySnapshots && equitySnapshots.length > 0 && (
                <EquityChart
                  data={equitySnapshots.map((s) => ({
                    t: new Date(s.timestamp).getTime(),
                    equity: s.equity,
                    cash: s.cash,
                  }))}
                  initialCapital={run.config.initial_capital}
                />
              )}
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wider mb-3">Final Portfolio</p>
                <div className="grid grid-cols-4 gap-3">
                  <MetricCard label="Final Cash" value={`$${metrics.final_cash.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`} />
                  <MetricCard label="Final Equity" value={`$${metrics.final_equity.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`} />
                  <MetricCard label="Realized PnL" value={`$${metrics.realized_pnl.toFixed(2)}`} accent={pnlColor(metrics.realized_pnl)} />
                  <MetricCard label="Unrealized PnL" value={`$${metrics.unrealized_pnl.toFixed(2)}`} accent={pnlColor(metrics.unrealized_pnl)} />
                </div>
              </div>
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wider mb-3">Performance</p>
                <div className="grid grid-cols-4 gap-3">
                  <MetricCard label="Total Return" value={`${metrics.total_return_pct.toFixed(2)}%`} accent={pnlColor(metrics.total_return_pct)} />
                  <MetricCard label="Sharpe Ratio" value={metrics.sharpe_ratio.toFixed(3)} />
                  <MetricCard label="Max Drawdown" value={`${metrics.max_drawdown_pct.toFixed(2)}%`} />
                  <MetricCard label="Win Rate" value={`${(metrics.win_rate * 100).toFixed(1)}%`} />
                  <MetricCard label="Total Trades" value={metrics.total_trades.toLocaleString()} />
                  <MetricCard label="Avg Win" value={`$${metrics.avg_win.toFixed(2)}`} accent="text-emerald-400" />
                  <MetricCard label="Avg Loss" value={`$${metrics.avg_loss.toFixed(2)}`} accent="text-red-400" />
                </div>
              </div>
            </div>
          ) : isActive(run.status as RunStatus) ? (
            <p className="text-gray-500 text-sm">Metrics will appear when the session completes.</p>
          ) : (
            <p className="text-gray-500 text-sm">No metrics available.</p>
          )}
        </>
      )}

      {tab === "equity" && (
        <div>
          {!equitySnapshots ? (
            <p className="text-gray-500 text-sm">Loading chart…</p>
          ) : equitySnapshots.length === 0 ? (
            <p className="text-gray-500 text-sm">No equity data recorded.</p>
          ) : (
            <div className="space-y-6">
              <EquityChart
                data={equitySnapshots.map((s) => ({
                  t: new Date(s.timestamp).getTime(),
                  equity: s.equity,
                  cash: s.cash,
                }))}
                initialCapital={run.config.initial_capital}
              />
            </div>
          )}
        </div>
      )}

      {tab === "fills" && (
        <div className="rounded-lg border border-gray-800 overflow-hidden">
          {!fills ? (
            <p className="text-gray-500 text-sm p-4">Loading fills…</p>
          ) : fills.length === 0 ? (
            <p className="text-gray-500 text-sm p-4">No fills recorded.</p>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-gray-900 text-gray-400 text-xs uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-3 text-left">Time</th>
                  <th className="px-4 py-3 text-left">Symbol</th>
                  <th className="px-4 py-3 text-left">Side</th>
                  <th className="px-4 py-3 text-right">Qty</th>
                  <th className="px-4 py-3 text-right">Price</th>
                  <th className="px-4 py-3 text-right">Fees</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {fills.map((f) => (
                  <tr key={f.id} className="bg-gray-900/40">
                    <td className="px-4 py-2 text-gray-400 text-xs">{fmt(f.timestamp)}</td>
                    <td className="px-4 py-2 font-mono">{f.symbol}</td>
                    <td className={`px-4 py-2 font-medium ${f.side === "buy" ? "text-emerald-400" : "text-red-400"}`}>
                      {f.side.toUpperCase()}
                    </td>
                    <td className="px-4 py-2 text-right">{f.qty}</td>
                    <td className="px-4 py-2 text-right">${f.fill_price.toFixed(2)}</td>
                    <td className="px-4 py-2 text-right text-gray-400">${f.fees.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}

function EquityChart({
  data,
  initialCapital,
}: {
  data: { t: number; equity: number; cash: number }[];
  initialCapital: number;
}) {
  const finalEquity = data[data.length - 1]?.equity ?? initialCapital;
  const isPositive = finalEquity >= initialCapital;
  const color = isPositive ? "#34d399" : "#f87171";

  const fmtDate = (ts: number) =>
    new Date(ts).toLocaleDateString(undefined, { month: "short", day: "numeric" });

  const fmtDollar = (v: number) =>
    `$${v.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
      <p className="text-xs text-gray-500 uppercase tracking-wider mb-4">Equity Curve</p>
      <ResponsiveContainer width="100%" height={320}>
        <AreaChart data={data} margin={{ top: 4, right: 8, left: 8, bottom: 0 }}>
          <defs>
            <linearGradient id="equityGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.25} />
              <stop offset="95%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis
            dataKey="t"
            type="number"
            domain={["dataMin", "dataMax"]}
            scale="time"
            tickFormatter={fmtDate}
            tick={{ fill: "#6b7280", fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            minTickGap={60}
          />
          <YAxis
            tickFormatter={fmtDollar}
            tick={{ fill: "#6b7280", fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            width={80}
          />
          <Tooltip
            contentStyle={{ backgroundColor: "#111827", border: "1px solid #374151", borderRadius: 6 }}
            labelFormatter={(ts) => new Date(ts as number).toLocaleString()}
            formatter={(val: number, name: string) => [fmtDollar(val), name === "equity" ? "Equity" : "Cash"]}
          />
          <Area
            type="monotone"
            dataKey="equity"
            stroke={color}
            strokeWidth={1.5}
            fill="url(#equityGrad)"
            dot={false}
            activeDot={{ r: 3, fill: color }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}