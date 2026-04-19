import { lazy, Suspense, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";

const MonacoEditor = lazy(() => import("@monaco-editor/react"));

const STARTER_CODE = `from collections import deque

from trading.core.enums import Side
from trading.core.events import MarketEvent, SignalEvent
from trading.core.models import PortfolioState
from trading.strategies.base import BaseStrategy


class MyStrategy(BaseStrategy):
    def __init__(self):
        pass

    def on_market_event(self, event: MarketEvent, portfolio: PortfolioState) -> list[SignalEvent]:
        return []
`;

export default function NewStrategyPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [code, setCode] = useState(STARTER_CODE);

  const mutation = useMutation({
    mutationFn: () => api.strategies.create(name, code),
    onSuccess: (strategy) => {
      queryClient.invalidateQueries({ queryKey: ["strategies"] });
      navigate(`/strategies/${strategy.id}`);
    },
  });

  return (
    <div className="flex flex-col h-full">
      <div className="mb-4">
        <button onClick={() => navigate("/strategies")} className="text-gray-500 hover:text-gray-300 text-xs mb-3 inline-block">
          ← Strategies
        </button>
        <div className="flex items-center justify-between">
          <input
            placeholder="Strategy name…"
            className="bg-transparent border-b border-gray-700 focus:border-indigo-500 outline-none text-2xl font-semibold pb-1 w-80 placeholder-gray-600"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <button
            onClick={() => mutation.mutate()}
            disabled={!name.trim() || mutation.isPending}
            className="px-4 py-1.5 text-sm bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-md transition-colors"
          >
            {mutation.isPending ? "Saving…" : "Save Strategy"}
          </button>
        </div>
      </div>

      <div className="flex-1 rounded-lg overflow-hidden border border-gray-800" style={{ minHeight: "70vh" }}>
        <Suspense fallback={
          <div className="h-full bg-gray-900 flex items-center justify-center text-gray-500 text-sm">
            Loading editor…
          </div>
        }>
          <MonacoEditor
            height="70vh"
            language="python"
            value={code}
            onChange={(v) => setCode(v ?? "")}
            theme="vs-dark"
            options={{
              minimap: { enabled: true },
              fontSize: 13,
              lineNumbers: "on",
              scrollBeyondLastLine: false,
              wordWrap: "on",
            }}
          />
        </Suspense>
      </div>
    </div>
  );
}