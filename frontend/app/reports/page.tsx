"use client"

import { useEffect, useMemo, useState } from "react"
import { Line, LineChart, CartesianGrid, XAxis, YAxis } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"

type Mode = "paper" | "live" | ""

interface ReportRun {
  run_id: string
  mode: string
  strategy_tag: string
  start_ts: string
  end_ts: string
  duration_hours: number | null
  close_reason: string | null
  initial_investment: number | null
  final_pnl: number | null
  max_dd: number | null
  peak_pnl: number | null
}

interface ReportLeg {
  symbol: string
  status: string
  entry_price: number | null
  exit_price: number | null
  qty: number | null
  initial_investment: number | null
  final_pnl: number | null
  max_dd: number | null
  peak_pnl: number | null
}

export default function ReportsPage() {
  const [mode, setMode] = useState<Mode>("")
  const [strategy, setStrategy] = useState("")
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")
  const [applied, setApplied] = useState({ mode: "", strategy: "", dateFrom: "", dateTo: "" })
  const [runs, setRuns] = useState<ReportRun[]>([])
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null)
  const [runDetail, setRunDetail] = useState<ReportRun | null>(null)
  const [legs, setLegs] = useState<ReportLeg[]>([])
  const [series, setSeries] = useState<any[]>([])
  const [seriesSymbols, setSeriesSymbols] = useState<string[]>([])
  const [initialInvestment, setInitialInvestment] = useState<number>(0)
  const [aggregate, setAggregate] = useState<{ avg_final_pnl_pct: number | null; avg_max_dd_pct: number | null; avg_peak_pnl_pct: number | null } | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const toUtcIso = (value: string) => {
    if (!value) return ""
    // Treat datetime-local as UTC and append seconds + Z
    return value.includes(":") ? `${value}:00Z` : `${value}T00:00:00Z`
  }

  const query = useMemo(() => {
    const params = new URLSearchParams()
    if (applied.mode) params.set("mode", applied.mode)
    if (applied.strategy) params.set("strategy", applied.strategy)
    if (applied.dateFrom) params.set("date_from", toUtcIso(applied.dateFrom))
    if (applied.dateTo) params.set("date_to", toUtcIso(applied.dateTo))
    return params.toString()
  }, [applied])

  const loadRuns = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/reports/runs?${query}`, { cache: "no-store" })
      if (!res.ok) {
        const text = await res.text()
        throw new Error(`Failed to load runs (${res.status}): ${text}`)
      }
      const data = await res.json()
      setRuns(data.runs || [])
    } catch (e: any) {
      setError(e?.message || "Failed to load runs")
    } finally {
      setLoading(false)
    }
  }

  const loadAggregate = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/reports/aggregate?${query}`, { cache: "no-store" })
      if (!res.ok) {
        const text = await res.text()
        throw new Error(`Failed to load aggregate (${res.status}): ${text}`)
      }
      const data = await res.json()
      setAggregate(data.aggregate || null)
    } catch {
      setAggregate(null)
    }
  }

  const loadRunDetail = async (runId: string) => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/reports/run?run_id=${runId}`, { cache: "no-store" })
      if (!res.ok) {
        const text = await res.text()
        throw new Error(`Failed to load run detail (${res.status}): ${text}`)
      }
      const data = await res.json()
      setRunDetail(data.run || null)
      setLegs(data.legs || [])
      await loadSeries(runId)
    } catch (e: any) {
      setError(e?.message || "Failed to load run detail")
    } finally {
      setLoading(false)
    }
  }

  const loadSeries = async (runId: string) => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/reports/run_timeseries?run_id=${runId}`, { cache: "no-store" })
      if (!res.ok) {
        const text = await res.text()
        throw new Error(`Failed to load timeseries (${res.status}): ${text}`)
      }
      const data = await res.json()
      const seriesRaw = data.series || []
      const initial = data.initial_investment || 0
      const normalized = seriesRaw.map((row: any) => ({
        ...row,
        aggregate_equity: initial + (row.aggregate_pnl || 0),
      }))
      setSeries(normalized)
      setSeriesSymbols(data.symbols || [])
      setInitialInvestment(initial)
    } catch {
      setSeries([])
      setSeriesSymbols([])
      setInitialInvestment(0)
    }
  }

  useEffect(() => {
    loadRuns()
    loadAggregate()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query])

  useEffect(() => {
    if (selectedRunId) {
      loadRunDetail(selectedRunId)
    } else {
      setRunDetail(null)
      setLegs([])
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedRunId])

  return (
    <div className="min-h-screen bg-background text-foreground p-4 space-y-6">
      <div className="rounded border border-border bg-card p-4">
        <a
          href="/"
          className="inline-flex items-center rounded-lg bg-primary px-4 py-2 text-base font-semibold text-primary-foreground shadow-sm"
        >
          Dashboard
        </a>
      </div>

      <div className="rounded border border-border bg-card p-4 space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-semibold">Reports</h1>
        </div>

        <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
          <label className="text-sm text-muted-foreground">
            <span className="block mb-1 text-foreground">Mode</span>
            <select
              className="h-10 w-full rounded border border-border bg-background px-3 text-base text-foreground"
              value={mode}
              onChange={(e) => setMode(e.target.value as Mode)}
            >
              <option value="">All</option>
              <option value="paper">Paper</option>
              <option value="live">Live</option>
            </select>
          </label>
          <label className="text-sm text-muted-foreground">
            <span className="block mb-1 text-foreground">Strategy</span>
            <select
              className="h-10 w-full rounded border border-border bg-background px-3 text-base text-foreground"
              value={strategy}
              onChange={(e) => setStrategy(e.target.value)}
            >
              <option value="">All</option>
              <option value="S1">S1</option>
              <option value="S2">S2</option>
              <option value="S3">S3</option>
            </select>
          </label>
          <label className="text-sm text-muted-foreground">
            <span className="block mb-1 text-foreground">Date From (UTC)</span>
            <input
              className="h-10 w-full rounded border border-border bg-background px-3 text-base text-foreground"
              type="datetime-local"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
            />
          </label>
          <label className="text-sm text-muted-foreground">
            <span className="block mb-1 text-foreground">Date To (UTC)</span>
            <input
              className="h-10 w-full rounded border border-border bg-background px-3 text-base text-foreground"
              type="datetime-local"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
            />
          </label>
        </div>
        <div className="flex items-center gap-2">
          <button
            className="h-9 rounded bg-primary px-4 text-sm font-medium text-primary-foreground disabled:opacity-60"
            onClick={() => setApplied({ mode, strategy, dateFrom, dateTo })}
            disabled={loading}
          >
            {loading ? "Loading..." : "Apply Filters"}
          </button>
          <button
            className="h-9 rounded border border-border px-4 text-sm text-foreground"
            onClick={() => {
              setMode("")
              setStrategy("")
              setDateFrom("")
              setDateTo("")
              setApplied({ mode: "", strategy: "", dateFrom: "", dateTo: "" })
            }}
          >
            Reset
          </button>
        </div>

        {aggregate && (
          <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
            <div className="rounded border border-border bg-background p-3">
              <div className="text-xs text-muted-foreground">Avg Final PnL %</div>
              <div className="text-lg font-semibold">{aggregate.avg_final_pnl_pct?.toFixed(2) ?? "—"}%</div>
            </div>
            <div className="rounded border border-border bg-background p-3">
              <div className="text-xs text-muted-foreground">Avg Max DD %</div>
              <div className="text-lg font-semibold">{aggregate.avg_max_dd_pct?.toFixed(2) ?? "—"}%</div>
            </div>
            <div className="rounded border border-border bg-background p-3">
              <div className="text-xs text-muted-foreground">Avg Peak PnL %</div>
              <div className="text-lg font-semibold">{aggregate.avg_peak_pnl_pct?.toFixed(2) ?? "—"}%</div>
            </div>
          </div>
        )}

        {error && <div className="text-sm text-loss">{error}</div>}
      </div>

      <div className="rounded border border-border bg-card p-4">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-base font-semibold">Completed Runs</h2>
          <span className="text-xs text-muted-foreground">{runs.length} runs</span>
        </div>
        <div className="overflow-auto">
          <table className="w-full text-sm">
            <thead className="text-xs text-muted-foreground">
              <tr className="border-b border-border">
                <th className="py-2 text-left">Run ID</th>
                <th className="py-2 text-left">Mode</th>
                <th className="py-2 text-left">Strategy</th>
                <th className="py-2 text-left">Start</th>
                <th className="py-2 text-left">End</th>
                <th className="py-2 text-left">Duration (h)</th>
                <th className="py-2 text-left">Close Reason</th>
                <th className="py-2 text-right">Initial</th>
                <th className="py-2 text-right">Final PnL</th>
                <th className="py-2 text-right">Max DD</th>
                <th className="py-2 text-right">Peak PnL</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r) => (
                <tr
                  key={r.run_id}
                  className={`border-b border-border hover:bg-muted/30 cursor-pointer ${
                    selectedRunId === r.run_id ? "bg-muted/40" : ""
                  }`}
                  onClick={() => setSelectedRunId(r.run_id)}
                >
                  <td className="py-2 font-mono text-xs">{r.run_id}</td>
                  <td className="py-2">{r.mode}</td>
                  <td className="py-2">{r.strategy_tag}</td>
                  <td className="py-2 font-mono text-xs">{r.start_ts}</td>
                  <td className="py-2 font-mono text-xs">{r.end_ts}</td>
                  <td className="py-2">{r.duration_hours?.toFixed(2) ?? "—"}</td>
                  <td className="py-2 text-xs">{r.close_reason || "—"}</td>
                  <td className="py-2 text-right">{r.initial_investment?.toFixed(2) ?? "—"}</td>
                  <td className="py-2 text-right">{r.final_pnl?.toFixed(2) ?? "—"}</td>
                  <td className="py-2 text-right">{r.max_dd?.toFixed(2) ?? "—"}</td>
                  <td className="py-2 text-right">{r.peak_pnl?.toFixed(2) ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {runDetail && (
        <div className="rounded border border-border bg-card p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold">Run Detail</h2>
            <span className="text-xs text-muted-foreground">{runDetail.run_id}</span>
          </div>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
            <div className="rounded border border-border bg-background p-3">
              <div className="text-xs text-muted-foreground">Initial Investment</div>
              <div className="text-lg font-semibold">{runDetail.initial_investment?.toFixed(2) ?? "—"}</div>
            </div>
            <div className="rounded border border-border bg-background p-3">
              <div className="text-xs text-muted-foreground">Final PnL</div>
              <div className="text-lg font-semibold">{runDetail.final_pnl?.toFixed(2) ?? "—"}</div>
            </div>
            <div className="rounded border border-border bg-background p-3">
              <div className="text-xs text-muted-foreground">Max DD</div>
              <div className="text-lg font-semibold">{runDetail.max_dd?.toFixed(2) ?? "—"}</div>
            </div>
            <div className="rounded border border-border bg-background p-3">
              <div className="text-xs text-muted-foreground">Peak PnL</div>
              <div className="text-lg font-semibold">{runDetail.peak_pnl?.toFixed(2) ?? "—"}</div>
            </div>
          </div>

          {series.length > 0 && (
            <div className="rounded border border-border bg-background p-3">
              <div className="mb-2 text-xs text-muted-foreground">Equity Curve (Initial + Unrealized) with Leg PnL</div>
              <ChartContainer
                config={{
                  aggregate: { label: "Aggregate Equity", color: "hsl(var(--primary))" },
                }}
              >
                <LineChart data={series}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="ts" tickFormatter={(v) => v.slice(11, 19)} />
                  <YAxis />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <Line type="monotone" dataKey="aggregate_equity" stroke="var(--color-aggregate)" dot={false} strokeWidth={2} />
                  {seriesSymbols.map((sym, i) => (
                    <Line
                      key={sym}
                      type="monotone"
                      dataKey={sym}
                      stroke={`hsl(${(i * 37) % 360} 70% 60%)`}
                      dot={false}
                      strokeWidth={1}
                    />
                  ))}
                </LineChart>
              </ChartContainer>
              <div className="mt-2 text-xs text-muted-foreground">
                Initial Investment: {initialInvestment.toFixed(2)}
              </div>
            </div>
          )}

          <div className="overflow-auto">
            <table className="w-full text-sm">
              <thead className="text-xs text-muted-foreground">
                <tr className="border-b border-border">
                  <th className="py-2 text-left">Symbol</th>
                  <th className="py-2 text-left">Status</th>
                  <th className="py-2 text-right">Entry</th>
                  <th className="py-2 text-right">Exit</th>
                  <th className="py-2 text-right">Qty</th>
                  <th className="py-2 text-right">Final PnL</th>
                  <th className="py-2 text-right">Max DD</th>
                  <th className="py-2 text-right">Peak PnL</th>
                </tr>
              </thead>
              <tbody>
                {legs.map((l) => (
                  <tr key={l.symbol} className="border-b border-border">
                    <td className="py-2">{l.symbol}</td>
                    <td className="py-2">{l.status}</td>
                    <td className="py-2 text-right">{l.entry_price?.toFixed(6) ?? "—"}</td>
                    <td className="py-2 text-right">{l.exit_price?.toFixed(6) ?? "—"}</td>
                    <td className="py-2 text-right">{l.qty?.toFixed(4) ?? "—"}</td>
                    <td className="py-2 text-right">{l.final_pnl?.toFixed(2) ?? "—"}</td>
                    <td className="py-2 text-right">{l.max_dd?.toFixed(2) ?? "—"}</td>
                    <td className="py-2 text-right">{l.peak_pnl?.toFixed(2) ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
