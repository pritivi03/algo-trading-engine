import { lazy, Suspense, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";

const MonacoEditor = lazy(() => import("@monaco-editor/react"));

export default function StrategyDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [editing, setEditing] = useState(false);
  const [draftName, setDraftName] = useState("");
  const [draftCode, setDraftCode] = useState("");

  const { data: strategy } = useQuery({
    queryKey: ["strategy", id],
    queryFn: () => api.strategies.get(id!),
  });

  const mutation = useMutation({
    mutationFn: () => api.strategies.update(id!, draftName, draftCode),
    onSuccess: (updated) => {
      queryClient.setQueryData(["strategy", id], updated);
      queryClient.invalidateQueries({ queryKey: ["strategies"] });
      setEditing(false);
    },
  });

  function startEditing() {
    setDraftName(strategy!.name);
    setDraftCode(strategy!.code);
    setEditing(true);
  }

  function cancelEditing() {
    setEditing(false);
  }

  if (!strategy) return <p className="text-gray-500 text-sm">Loading…</p>;

  return (
    <div className="flex flex-col h-full">
      <div className="mb-4">
        <button onClick={() => navigate("/strategies")} className="text-gray-500 hover:text-gray-300 text-xs mb-3 inline-block">
          ← Strategies
        </button>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {editing ? (
              <input
                className="bg-gray-900 border border-gray-700 rounded-md px-3 py-1.5 text-lg font-semibold focus:outline-none focus:border-indigo-500"
                value={draftName}
                onChange={(e) => setDraftName(e.target.value)}
              />
            ) : (
              <h1 className="text-2xl font-semibold">{strategy.name}</h1>
            )}
            <span className="font-mono text-xs text-gray-500">{strategy.id}</span>
          </div>
          <div className="flex gap-2">
            {editing ? (
              <>
                <button
                  onClick={cancelEditing}
                  className="px-3 py-1.5 text-sm text-gray-400 hover:text-gray-200 border border-gray-700 rounded-md transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => mutation.mutate()}
                  disabled={mutation.isPending}
                  className="px-3 py-1.5 text-sm bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 rounded-md transition-colors"
                >
                  {mutation.isPending ? "Saving…" : "Save"}
                </button>
              </>
            ) : (
              <button
                onClick={startEditing}
                className="px-3 py-1.5 text-sm border border-gray-700 hover:border-gray-500 text-gray-300 hover:text-white rounded-md transition-colors"
              >
                Edit
              </button>
            )}
          </div>
        </div>
        {!editing && (
          <p className="text-xs text-gray-600 mt-1">
            Created {new Date(strategy.created_at).toLocaleString()}
          </p>
        )}
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
            value={editing ? draftCode : strategy.code}
            onChange={(v) => editing && setDraftCode(v ?? "")}
            theme="vs-dark"
            options={{
              readOnly: !editing,
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
