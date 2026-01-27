"use client"

import { Circle, Clock, Wifi, WifiOff, Target, ShieldAlert } from "lucide-react"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

interface RunStatusProps {
  isPaused: boolean
  run: any | null
  heartbeats: any[]
}

// Strategy definitions
const STRATEGIES = {
  S1: {
    name: "S1",
    label: "Hard TP/SL",
    description: "Hard TP +30%, Hard SL -30%, 24h cutoff",
  },
  S2: {
    name: "S2",
    label: "Raw 24h",
    description: "24h cutoff only (no TP/SL)",
  },
  S3: {
    name: "S3",
    label: "S1 + Trailing",
    description: "S1 + trailing stop on +100% leg PnL with 5% retracement",
  },
}

export function RunStatus({ isPaused, run, heartbeats }: RunStatusProps) {
  const latestHeartbeat = heartbeats?.[0]
  const lastHeartbeatTs = latestHeartbeat?.ts || null
  const lastHeartbeatDate = lastHeartbeatTs ? new Date(lastHeartbeatTs) : null
  const now = new Date()
  const isOnline =
    lastHeartbeatDate !== null &&
    now.getTime() - lastHeartbeatDate.getTime() < 120 * 1000

  const status = {
    runId: run?.run_id || "—",
    strategy: (run?.strategy_tag || "S1") as keyof typeof STRATEGIES,
    startTime: run?.start_ts || "—",
    elapsedHours: run?.start_ts
      ? ((now.getTime() - new Date(run.start_ts).getTime()) / 36e5).toFixed(1)
      : "—",
    nextPollIn: "—",
    lastHeartbeat: lastHeartbeatTs || "—",
    globalTp: 30,
    globalSl: 30,
  }

  const strategyInfo = STRATEGIES[status.strategy]
  return (
    <div className="rounded border border-border bg-card p-4">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-medium text-muted-foreground">Run Status</h2>
        <div className="flex items-center gap-3">
          {/* Heartbeat Indicator */}
          <div className="flex items-center gap-1.5">
            {isOnline ? (
              <Wifi className="h-3.5 w-3.5 text-profit" />
            ) : (
              <WifiOff className="h-3.5 w-3.5 text-loss" />
            )}
            <span
              className={`text-xs font-medium ${
                isOnline ? "text-profit" : "text-loss"
              }`}
            >
              {isOnline ? "ONLINE" : "OFFLINE"}
            </span>
          </div>
          
          {/* Run State */}
          <div className="flex items-center gap-1.5 border-l border-border pl-3">
            <Circle
              className={`h-2 w-2 ${
                isPaused
                  ? "fill-warning text-warning"
                  : "fill-profit text-profit"
              }`}
            />
            <span
              className={`text-xs font-medium ${
                isPaused ? "text-warning" : "text-profit"
              }`}
            >
              {isPaused ? "PAUSED" : "RUNNING"}
            </span>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground">Run ID</span>
          <span className="font-mono text-xs text-foreground">{status.runId}</span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground">Strategy</span>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center gap-2 cursor-help">
                  <span className="rounded bg-primary/20 px-2 py-0.5 text-xs font-medium text-primary">
                    {strategyInfo.name}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {strategyInfo.label}
                  </span>
                </div>
              </TooltipTrigger>
              <TooltipContent className="bg-popover border-border">
                <p className="text-xs">{strategyInfo.description}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground">Started</span>
          <span className="font-mono text-xs text-foreground">{status.startTime}</span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground">Elapsed</span>
          <div className="flex items-center gap-1">
            <Clock className="h-3 w-3 text-muted-foreground" />
            <span className="font-mono text-xs text-foreground">
              {status.elapsedHours}h
            </span>
          </div>
        </div>

        {/* Global TP/SL Values */}
        <div className="border-t border-border pt-3">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-1">
              <Target className="h-3 w-3 text-profit" />
              <span className="text-xs text-muted-foreground">Global TP</span>
            </div>
            <span className="font-mono text-xs text-profit">+{status.globalTp}%</span>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1">
              <ShieldAlert className="h-3 w-3 text-loss" />
              <span className="text-xs text-muted-foreground">Global SL</span>
            </div>
            <span className="font-mono text-xs text-loss">-{status.globalSl}%</span>
          </div>
        </div>

        <div className="border-t border-border pt-3">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">Next Poll</span>
            <span className="font-mono text-xs text-primary">{status.nextPollIn}s</span>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground">Last Heartbeat</span>
          <span className="font-mono text-xs text-muted-foreground">
            {status.lastHeartbeat}
          </span>
        </div>
      </div>
    </div>
  )
}
