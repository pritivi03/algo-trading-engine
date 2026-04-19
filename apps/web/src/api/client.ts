import type { Strategy, Run, Metrics, Fill, CreateRunPayload } from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  strategies: {
    list: () => request<Strategy[]>("/strategies"),
    get: (id: string) => request<Strategy>(`/strategies/${id}`),
  },
  runs: {
    list: () => request<Run[]>("/runs"),
    get: (id: string) => request<Run>(`/runs/${id}`),
    create: (payload: CreateRunPayload) =>
      request<Run>("/runs", { method: "POST", body: JSON.stringify(payload) }),
    start: (id: string) =>
      request<Run>(`/runs/${id}/start`, { method: "POST" }),
    stop: (id: string) =>
      request<Run>(`/runs/${id}/stop`, { method: "POST" }),
    delete: (id: string) =>
      request<void>(`/runs/${id}`, { method: "DELETE" }),
    metrics: (id: string) => request<Metrics>(`/runs/${id}/metrics`),
    fills: (id: string) => request<Fill[]>(`/runs/${id}/fills`),
  },
};