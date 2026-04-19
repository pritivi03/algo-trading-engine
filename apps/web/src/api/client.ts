import type { Strategy, Run, Metrics, Fill, EquitySnapshot, CreateRunPayload } from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${text}`);
  }
  if (res.status === 204 || res.headers.get("content-length") === "0") {
    return undefined as T;
  }
  return res.json() as Promise<T>;
}

export const api = {
  strategies: {
    list: () => request<Strategy[]>("/strategies"),
    get: (id: string) => request<Strategy>(`/strategies/${id}`),
    create: (name: string, code: string) =>
      request<Strategy>("/strategies", { method: "POST", body: JSON.stringify({ name, code }) }),
    update: (id: string, name: string, code: string) =>
      request<Strategy>(`/strategies/${id}`, { method: "PUT", body: JSON.stringify({ name, code }) }),
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
    equitySnapshots: (id: string) => request<EquitySnapshot[]>(`/runs/${id}/equity-snapshots`),
  },
};