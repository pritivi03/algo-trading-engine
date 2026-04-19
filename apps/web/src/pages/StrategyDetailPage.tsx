import { lazy, Suspense } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";

const MonacoEditor = lazy(() => import("@monaco-editor/react"));

export default function StrategyDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: strategy } = useQuery({
    queryKey: ["strategy", id],
    queryFn: () => api.strategies.get(id!),
  });

  if (!strategy) return <p className="text-gray-500 text-sm">Loading…</p>;

  return (
    <div className="flex flex-col h-full">
      <div className="mb-4">
        <button onClick={() => navigate("/strategies")} className="text-gray-500 hover:text-gray-300 text-xs mb-3 inline-block">
          ← Strategies
        </button>
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold">{strategy.name}</h1>
          <span className="font-mono text-xs text-gray-500">{strategy.id}</span>
        </div>
        <p className="text-xs text-gray-600 mt-1">
          Created {new Date(strategy.created_at).toLocaleString()}
        </p>
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
            value={strategy.code}
            theme="vs-dark"
            options={{
              readOnly: true,
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