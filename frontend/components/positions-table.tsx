"use client"

import { useMemo, useState } from "react"
import { ChevronDown, ChevronUp, ArrowUpDown, TrendingDown, Target, ShieldAlert } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { LegTpSlDialog } from "@/components/leg-tp-sl-dialog" // Import LegTpSlDialog

interface Position {
  id: string
  symbol: string
  side: "SHORT"
  entryPrice: number
  markPrice: number
  size: number
  margin: number
  leverage: number
  unrealizedPnl: number
  unrealizedPnlPercent: number
  entryTime: string
  timeRemaining: string
  tpPrice: number | null
  slPrice: number | null
  status: "active" | "tp_pending" | "sl_pending"
  trailingStopActive: boolean
  trailingStopTriggerPnl: number | null
  peakPnl: number | null
}

type SortField = "symbol" | "unrealizedPnl" | "unrealizedPnlPercent" | "timeRemaining"
type SortDirection = "asc" | "desc"

interface PositionsTableProps {
  run: any | null
  positions: any[]
  snapshots: any[]
}

export function PositionsTable({ run, positions, snapshots }: PositionsTableProps) {
  const [sortField, setSortField] = useState<SortField>("symbol")
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc")
  const [expandedRow, setExpandedRow] = useState<string | null>(null)

  const derivedPositions: Position[] = useMemo(() => {
    const defaultMargin = run?.margin_per_leg_usdt || 100
    const start = run?.start_ts ? new Date(run.start_ts).getTime() : null
    const now = Date.now()
    const remainingMs = start ? Math.max(0, 24 * 3600 * 1000 - (now - start)) : null
    const timeRemaining = remainingMs
      ? `${Math.floor(remainingMs / 3600000)}h ${Math.floor((remainingMs % 3600000) / 60000)}m`
      : "—"

    const latestBySymbol: Record<string, any> = {}
    for (const s of snapshots || []) {
      if (!latestBySymbol[s.symbol]) latestBySymbol[s.symbol] = s
    }

    return (positions || []).map((p, idx) => {
      const snap = latestBySymbol[p.symbol]
      const margin = snap?.margin_usdt ?? defaultMargin
      const pnl = snap?.unrealized_pnl_usdt ?? 0
      const pnlPct = margin ? (pnl / margin) * 100 : 0
      return {
        id: p.symbol || `${idx}`,
        symbol: p.symbol,
        side: "SHORT",
        entryPrice: snap?.entry_price ?? p.entry_price ?? 0,
        markPrice: snap?.price || p.entry_price || 0,
        size: snap?.position_size ?? p.qty ?? 0,
        margin,
        leverage: (snap?.leverage ?? run?.leverage) || 3,
        unrealizedPnl: pnl,
        unrealizedPnlPercent: pnlPct,
        entryTime: run?.start_ts || "—",
        timeRemaining,
        tpPrice: null,
        slPrice: null,
        status: "active",
        trailingStopActive: false,
        trailingStopTriggerPnl: null,
        peakPnl: null,
      }
    })
  }, [positions, snapshots, run])

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc")
    } else {
      setSortField(field)
      setSortDirection("asc")
    }
  }

  const sortedPositions = [...derivedPositions].sort((a, b) => {
    const multiplier = sortDirection === "asc" ? 1 : -1
    if (sortField === "symbol") {
      return a.symbol.localeCompare(b.symbol) * multiplier
    }
    return (a[sortField] as number) - (b[sortField] as number) * multiplier
  })

  const formatPrice = (price: number) => {
    if (price < 0.0001) return price.toFixed(8)
    if (price < 1) return price.toFixed(6)
    return price.toFixed(4)
  }

  const formatPnl = (value: number) => {
    const prefix = value >= 0 ? "+" : ""
    return `${prefix}${value.toFixed(2)}`
  }

  const getPnlColor = (value: number) => {
    if (value > 0) return "text-profit"
    if (value < 0) return "text-loss"
    return "text-foreground"
  }

  const getStatusBadge = (position: Position) => {
    const badges = []
    
    if (position.trailingStopActive) {
      badges.push(
        <span key="trailing" className="rounded bg-primary/20 px-1.5 py-0.5 text-[10px] font-medium text-primary flex items-center gap-1">
          <TrendingDown className="h-2.5 w-2.5" />
          TRAILING
        </span>
      )
    }
    
    if (position.status === "tp_pending") {
      badges.push(
        <span key="tp" className="rounded bg-profit/20 px-1.5 py-0.5 text-[10px] font-medium text-profit">
          TP SET
        </span>
      )
    }
    
    if (position.status === "sl_pending") {
      badges.push(
        <span key="sl" className="rounded bg-loss/20 px-1.5 py-0.5 text-[10px] font-medium text-loss">
          SL SET
        </span>
      )
    }
    
    if (badges.length === 0) return null
    
    return <div className="flex items-center gap-1 justify-center">{badges}</div>
  }

  return (
    <div className="rounded border border-border bg-card">
      <div className="border-b border-border px-4 py-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-medium text-muted-foreground">
            Open Positions
          </h2>
          <span className="text-xs text-muted-foreground">
            {derivedPositions.length} active legs
          </span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border text-xs text-muted-foreground">
              <th className="px-4 py-3 text-left font-medium">
                <button
                  onClick={() => handleSort("symbol")}
                  className="flex items-center gap-1 hover:text-foreground"
                >
                  Symbol
                  <ArrowUpDown className="h-3 w-3" />
                </button>
              </th>
              <th className="px-4 py-3 text-left font-medium">Side</th>
              <th className="px-4 py-3 text-right font-medium">Entry Price</th>
              <th className="px-4 py-3 text-right font-medium">Mark Price</th>
              <th className="px-4 py-3 text-right font-medium">Size</th>
              <th className="px-4 py-3 text-right font-medium">Margin</th>
              <th className="px-4 py-3 text-right font-medium">
                <button
                  onClick={() => handleSort("unrealizedPnl")}
                  className="flex items-center gap-1 hover:text-foreground ml-auto"
                >
                  PnL (USDT)
                  <ArrowUpDown className="h-3 w-3" />
                </button>
              </th>
              <th className="px-4 py-3 text-right font-medium">
                <button
                  onClick={() => handleSort("unrealizedPnlPercent")}
                  className="flex items-center gap-1 hover:text-foreground ml-auto"
                >
                  PnL %
                  <ArrowUpDown className="h-3 w-3" />
                </button>
              </th>
              <th className="px-4 py-3 text-right font-medium">Time Left</th>
              <th className="px-4 py-3 text-center font-medium">Status</th>
              <th className="px-4 py-3 text-center font-medium"></th>
            </tr>
          </thead>
          <tbody>
            {sortedPositions.map((position) => (
              <>
                <tr
                  key={position.id}
                  className="border-b border-border/50 text-sm hover:bg-secondary/30 transition-colors"
                >
                  <td className="px-4 py-3">
                    <span className="font-medium text-foreground">
                      {position.symbol}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="rounded bg-loss/20 px-2 py-0.5 text-xs font-medium text-loss">
                      {position.side}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-foreground">
                    {formatPrice(position.entryPrice)}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-foreground">
                    {formatPrice(position.markPrice)}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-foreground">
                    {position.size.toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-foreground">
                    ${position.margin}
                  </td>
                  <td
                    className={`px-4 py-3 text-right font-mono font-medium ${getPnlColor(
                      position.unrealizedPnl
                    )}`}
                  >
                    {formatPnl(position.unrealizedPnl)}
                  </td>
                  <td
                    className={`px-4 py-3 text-right font-mono font-medium ${getPnlColor(
                      position.unrealizedPnlPercent
                    )}`}
                  >
                    {formatPnl(position.unrealizedPnlPercent)}%
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-muted-foreground">
                    {position.timeRemaining}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {getStatusBadge(position)}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <button
                      onClick={() =>
                        setExpandedRow(
                          expandedRow === position.id ? null : position.id
                        )
                      }
                      className="p-1 hover:bg-secondary rounded transition-colors"
                    >
                      {expandedRow === position.id ? (
                        <ChevronUp className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <ChevronDown className="h-4 w-4 text-muted-foreground" />
                      )}
                    </button>
                  </td>
                </tr>
                {expandedRow === position.id && (
                  <tr key={`${position.id}-expanded`} className="bg-secondary/20">
                    <td colSpan={11} className="px-4 py-3">
                      <div className="grid grid-cols-2 gap-4 sm:grid-cols-6 text-xs">
                        <div>
                          <span className="text-muted-foreground">Entry Time</span>
                          <p className="font-mono text-foreground mt-1">
                            {position.entryTime}
                          </p>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Leverage</span>
                          <p className="font-mono text-warning mt-1">
                            {position.leverage}x
                          </p>
                        </div>
                        <div>
                          <span className="text-muted-foreground">TP Price</span>
                          <p className="font-mono text-profit mt-1">
                            {position.tpPrice
                              ? formatPrice(position.tpPrice)
                              : "Not set"}
                          </p>
                        </div>
                        <div>
                          <span className="text-muted-foreground">SL Price</span>
                          <p className="font-mono text-loss mt-1">
                            {position.slPrice
                              ? formatPrice(position.slPrice)
                              : "Not set"}
                          </p>
                        </div>
                        {/* Trailing Stop Info (S3 only) */}
                        {position.trailingStopActive && (
                          <>
                            <div>
                              <span className="text-muted-foreground">Peak PnL</span>
                              <p className="font-mono text-primary mt-1">
                                +{position.peakPnl?.toFixed(2)} USDT
                              </p>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Trail Trigger</span>
                              <p className="font-mono text-primary mt-1">
                                +{position.trailingStopTriggerPnl}% (5% retrace)
                              </p>
                            </div>
                          </>
                        )}
                      </div>
                      {/* Manual TP/SL Controls Per Leg */}
                      <div className="mt-3 pt-3 border-t border-border/50 flex items-center gap-2">
                        <span className="text-xs text-muted-foreground mr-2">Manual Controls:</span>
                        <LegTpSlDialog 
                          positionId={position.id} 
                          symbol={position.symbol} 
                          type="tp" 
                          currentPrice={position.tpPrice}
                          formatPrice={formatPrice}
                        />
                        <LegTpSlDialog 
                          positionId={position.id} 
                          symbol={position.symbol} 
                          type="sl" 
                          currentPrice={position.slPrice}
                          formatPrice={formatPrice}
                        />
                      </div>
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
