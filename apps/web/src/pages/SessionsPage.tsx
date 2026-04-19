import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import StatusBadge from "../components/StatusBadge";
import type { Run, RunStatus, Strategy } from "../api/types";

function fmt(dt: string | null) {
  if (!dt) return "—";
  return new Date(dt).toLocaleString();
}

function DeleteButton({ run, strategyMap }: { run: Run; strategyMap: Map<string, Strategy> }) {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: () => api.runs.delete(run.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["runs"] }),
  });

  if (run.status !== "completed" && run.status !== "failed") return null;

  return (
    <button
      onClick={(e) => {
        e.stopPropagation();
        if (!window.confirm("Delete this session? This cannot be undone.")) return;
        mutation.mutate();
      }}
      disabled={mutation.isPending}
      className="opacity-0 group-hover:opacity-100 px-2 py-1 text-xs text-red-400 hover:text-red-300 hover:bg-red-900/30 rounded transition-all"
    >
      {mutation.isPending ? "…" : "Delete"}
    </button>
  );
}

export default function SessionsPage() {
  const navigate = useNavigate();

  const { data: runs, isLoading } = useQuery({
    queryKey: ["runs"],
    queryFn: api.runs.list,
    refetchInterval: 3000,
  });

  const { data: strategies } = useQuery({
    queryKey: ["strategies"],
    queryFn: api.strategies.list,
  });

  const strategyMap = new Map((strategies ?? []).map((s) => [s.id, s]));

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Sessions</h1>
        <button
          onClick={() => navigate("/sessions/new")}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-md text-sm font-medium transition-colors"
        >
          + Launch Backtest
        </button>
      </div>

      {isLoading && <p className="text-gray-500 text-sm">Loading…</p>}

      {runs && runs.length === 0 && (
        <p className="text-gray-500 text-sm">No sessions yet. Launch your first backtest.</p>
      )}

      {runs && runs.length > 0 && (
        <div className="rounded-lg border border-gray-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-900 text-gray-400 text-xs uppercase tracking-wider">
              <tr>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-left">Strategy</th>
                <th className="px-4 py-3 text-left">Symbol</th>
                <th className="px-4 py-3 text-left">Mode</th>
                <th className="px-4 py-3 text-left">Capital</th>
                <th className="px-4 py-3 text-left">Created</th>
                <th className="px-4 py-3 text-left">Completed</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {runs.map((run) => (
                <tr
                  key={run.id}
                  onClick={() => navigate(`/sessions/${run.id}`)}
                  className="group bg-gray-900/40 hover:bg-gray-800/60 cursor-pointer transition-colors"
                >
                  <td className="px-4 py-3">
                    <StatusBadge status={run.status as RunStatus} />
                  </td>
                  <td className="px-4 py-3 text-gray-300">
                    {strategyMap.get(run.strategy_id)?.name ?? <span className="text-gray-600">—</span>}
                  </td>
                  <td className="px-4 py-3 font-mono">{run.config.symbol}</td>
                  <td className="px-4 py-3 capitalize text-gray-400">{run.config.mode}</td>
                  <td className="px-4 py-3">${run.config.initial_capital.toLocaleString()}</td>
                  <td className="px-4 py-3 text-gray-400">{fmt(run.created_at)}</td>
                  <td className="px-4 py-3 text-gray-400">{fmt(run.completed_at)}</td>
                  <td className="px-4 py-3 text-right">
                    <DeleteButton run={run} strategyMap={strategyMap} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}