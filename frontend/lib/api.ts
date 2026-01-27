export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000"

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" })
  if (!res.ok) {
    throw new Error(`GET ${path} failed: ${res.status}`)
  }
  return res.json()
}

async function postJson<T>(path: string, body?: Record<string, unknown>): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    throw new Error(`POST ${path} failed: ${res.status}`)
  }
  return res.json()
}

export const api = {
  getLatestRun: (mode: "paper" | "live") =>
    getJson<{ run: any }>(`/runs/latest?mode=${mode}`),
  getOpenPositions: (runId?: string) =>
    runId ? getJson<{ positions: any[] }>(`/positions/open?run_id=${runId}`) : getJson<{ positions: any[] }>("/positions/open"),
  getLatestSnapshots: (limit = 200, runId?: string) =>
    runId
      ? getJson<{ snapshots: any[] }>(`/snapshots/latest?limit=${limit}&run_id=${runId}`)
      : getJson<{ snapshots: any[] }>(`/snapshots/latest?limit=${limit}`),
  getLegs: (runId?: string) =>
    runId ? getJson<{ legs: any[] }>(`/legs?run_id=${runId}`) : getJson<{ legs: any[] }>("/legs"),
  getLatestHeartbeats: (limit = 20) => getJson<{ heartbeats: any[] }>(`/heartbeats/latest?limit=${limit}`),
  getLatestEvents: (limit = 50, runId?: string) =>
    runId
      ? getJson<{ events: any[] }>(`/events/latest?limit=${limit}&run_id=${runId}`)
      : getJson<{ events: any[] }>(`/events/latest?limit=${limit}`),

  commandPause: () => postJson<{ ok: boolean }>("/commands/pause"),
  commandResume: () => postJson<{ ok: boolean }>("/commands/resume"),
  commandCloseAll: () => postJson<{ ok: boolean }>("/commands/close_all"),
  commandSetGlobalTp: (percent: number) => postJson<{ ok: boolean }>("/commands/set_global_tp", { percent }),
  commandSetGlobalSl: (percent: number) => postJson<{ ok: boolean }>("/commands/set_global_sl", { percent }),
  commandLegTp: (symbol: string, price: number) => postJson<{ ok: boolean }>("/commands/leg_tp", { symbol, price }),
  commandLegSl: (symbol: string, price: number) => postJson<{ ok: boolean }>("/commands/leg_sl", { symbol, price }),
  commandLegTpClear: (symbol: string) => postJson<{ ok: boolean }>("/commands/leg_tp_clear", { symbol }),
  commandLegSlClear: (symbol: string) => postJson<{ ok: boolean }>("/commands/leg_sl_clear", { symbol }),
}
