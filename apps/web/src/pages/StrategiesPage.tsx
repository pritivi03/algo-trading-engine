import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";

export default function StrategiesPage() {
  const navigate = useNavigate();
  const { data: strategies, isLoading } = useQuery({
    queryKey: ["strategies"],
    queryFn: api.strategies.list,
  });

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-6">Strategies</h1>

      {isLoading && <p className="text-gray-500 text-sm">Loading…</p>}

      {strategies && strategies.length === 0 && (
        <p className="text-gray-500 text-sm">No strategies seeded yet.</p>
      )}

      {strategies && strategies.length > 0 && (
        <div className="rounded-lg border border-gray-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-900 text-gray-400 text-xs uppercase tracking-wider">
              <tr>
                <th className="px-4 py-3 text-left">Name</th>
                <th className="px-4 py-3 text-left">ID</th>
                <th className="px-4 py-3 text-left">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {strategies.map((s) => (
                <tr key={s.id} onClick={() => navigate(`/strategies/${s.id}`)} className="bg-gray-900/40 hover:bg-gray-800/60 cursor-pointer transition-colors">
                  <td className="px-4 py-3 font-medium">{s.name}</td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-400">{s.id}</td>
                  <td className="px-4 py-3 text-gray-400">
                    {new Date(s.created_at).toLocaleString()}
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