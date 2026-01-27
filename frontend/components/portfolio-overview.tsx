"use client"

import { TrendingDown, TrendingUp } from "lucide-react"

interface PortfolioOverviewProps {
  run: any | null
  positions: any[]
  snapshots: any[]
  legs: any[]
}

export function PortfolioOverview({ run, positions, snapshots, legs }: PortfolioOverviewProps) {
  const runId = run?.run_id
  const marginPerLeg = run?.margin_per_leg_usdt || 100
  const isLive = run?.mode === "live"
  const initialInvestment = run?.initial_balance ?? 0

  const openSymbols = new Set((positions || []).map((p) => p.symbol))
  const runSnapshots = (snapshots || []).filter((s) => s.run_id === runId && openSymbols.has(s.symbol))

  const latestBySymbol: Record<string, any> = {}
  for (const s of runSnapshots) {
    if (!latestBySymbol[s.symbol]) {
      latestBySymbol[s.symbol] = s
    }
  }
  const unrealizedPnl = Object.values(latestBySymbol).reduce(
    (a, b) => a + (b?.unrealized_pnl_usdt || 0),
    0
  )
  const realizedPnl = (legs || []).reduce((a, l) => {
    if (l?.status !== "closed") return a
    const entry = l?.entry_price
    const exit = l?.exit_price
    const qty = l?.qty
    if (entry == null || exit == null || qty == null) return a
    return a + (entry - exit) * qty
  }, 0)
  const usedMargin = isLive
    ? Object.values(latestBySymbol).reduce((a, b) => a + (b?.margin_usdt || 0), 0)
    : (positions?.length || 0) * marginPerLeg
  const currentBalance = run?.current_balance ?? (initialInvestment + realizedPnl + unrealizedPnl)
  const totalPnl = realizedPnl + unrealizedPnl

  // Compute max drawdown from snapshot history (latest N snapshots)
  const pnlByTs: Record<string, number> = {}
  for (const s of runSnapshots) {
    const ts = s.ts
    pnlByTs[ts] = (pnlByTs[ts] || 0) + (s.unrealized_pnl_usdt || 0)
  }
  const realizedByTs: Record<string, number> = {}
  const closedLegs = (legs || [])
    .filter((l) => l?.status === "closed" && l?.exit_ts)
    .map((l) => ({
      exit_ts: l.exit_ts,
      pnl: (l.entry_price - l.exit_price) * l.qty,
    }))
    .sort((a, b) => Date.parse(a.exit_ts) - Date.parse(b.exit_ts))

  const sortedTs = Object.keys(pnlByTs).sort((a, b) => Date.parse(a) - Date.parse(b))
  let realizedRunning = 0
  let closedIndex = 0
  for (const ts of sortedTs) {
    const tsMs = Date.parse(ts)
    while (closedIndex < closedLegs.length && Date.parse(closedLegs[closedIndex].exit_ts) <= tsMs) {
      realizedRunning += closedLegs[closedIndex].pnl
      closedIndex += 1
    }
    realizedByTs[ts] = realizedRunning
  }

  let peakEquity = initialInvestment
  let currentDrawdown = 0
  let maxDrawdown = 0
  for (const ts of sortedTs) {
    const equity = initialInvestment + (realizedByTs[ts] || 0) + pnlByTs[ts]
    if (equity > peakEquity) peakEquity = equity
    const dd = peakEquity > 0 ? ((equity - peakEquity) / peakEquity) * 100 : 0
    if (ts === sortedTs[sortedTs.length - 1]) currentDrawdown = dd
    if (dd < maxDrawdown) maxDrawdown = dd
  }
  if (sortedTs.length === 0) {
    currentDrawdown = 0
    maxDrawdown = 0
  }

  const formatUsd = (value: number) => {
    const prefix = value >= 0 ? "+" : ""
    return `${prefix}${value.toFixed(2)}`
  }

  const getPnlColor = (value: number) => {
    if (value > 0) return "text-profit"
    if (value < 0) return "text-loss"
    return "text-foreground"
  }

  return (
    <div className="rounded border border-border bg-card p-4">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-medium text-muted-foreground">
          Portfolio Overview
        </h2>
        <span className="text-xs text-muted-foreground">
          {positions.length}/{run?.num_legs || 10} Positions
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {/* Current Balance */}
        <div className="space-y-1">
          <span className="text-xs text-muted-foreground">Current Balance</span>
          <p className="font-mono text-lg font-semibold text-foreground">
            ${currentBalance.toFixed(2)}
          </p>
        </div>

        {/* Used Margin */}
        <div className="space-y-1">
          <span className="text-xs text-muted-foreground">Used Margin</span>
          <p className="font-mono text-lg font-semibold text-foreground">
            ${usedMargin.toFixed(2)}
          </p>
          <div className="h-1 w-full rounded-full bg-muted">
            <div
              className="h-1 rounded-full bg-primary"
              style={{
                width: currentBalance ? `${(usedMargin / currentBalance) * 100}%` : "0%",
              }}
            />
          </div>
        </div>

        {/* Unrealized PnL */}
        <div className="space-y-1">
          <span className="text-xs text-muted-foreground">Unrealized PnL</span>
          <div className="flex items-center gap-2">
            {unrealizedPnl >= 0 ? (
              <TrendingUp className="h-4 w-4 text-profit" />
            ) : (
              <TrendingDown className="h-4 w-4 text-loss" />
            )}
            <p
              className={`font-mono text-lg font-semibold ${getPnlColor(
                unrealizedPnl
              )}`}
            >
              {formatUsd(unrealizedPnl)} USDT
            </p>
          </div>
        </div>

        {/* Realized PnL */}
        <div className="space-y-1">
          <span className="text-xs text-muted-foreground">Realized PnL</span>
          <div className="flex items-center gap-2">
            {realizedPnl >= 0 ? (
              <TrendingUp className="h-4 w-4 text-profit" />
            ) : (
              <TrendingDown className="h-4 w-4 text-loss" />
            )}
            <p
              className={`font-mono text-lg font-semibold ${getPnlColor(
                realizedPnl
              )}`}
            >
              {formatUsd(realizedPnl)} USDT
            </p>
          </div>
        </div>
      </div>

      {/* Drawdown Section */}
      <div className="mt-4 border-t border-border pt-4">
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div className="space-y-1">
            <span className="text-xs text-muted-foreground">Total PnL</span>
            <p
              className={`font-mono text-base font-semibold ${getPnlColor(
                totalPnl
              )}`}
            >
              {formatUsd(totalPnl)} USDT
            </p>
          </div>

          <div className="space-y-1">
            <span className="text-xs text-muted-foreground">Current DD</span>
            <p className="font-mono text-base font-semibold text-loss">
              {currentDrawdown.toFixed(2)}%
            </p>
          </div>

          <div className="space-y-1">
            <span className="text-xs text-muted-foreground">Max DD</span>
            <p className="font-mono text-base font-semibold text-loss">
              {maxDrawdown.toFixed(2)}%
            </p>
          </div>

          <div className="space-y-1">
            <span className="text-xs text-muted-foreground">Leverage</span>
            <p className="font-mono text-base font-semibold text-warning">
              {isLive
                ? (Object.values(latestBySymbol).find((s) => s?.leverage)?.leverage || run?.leverage || 3)
                : (run?.leverage || 3)}x
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
