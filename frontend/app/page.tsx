"use client"

import { useMemo, useState } from "react"
import { Header } from "@/components/header"
import { RunStatus } from "@/components/run-status"
import { PortfolioOverview } from "@/components/portfolio-overview"
import { PositionsTable } from "@/components/positions-table"
import { Controls } from "@/components/controls"
import { EventLog } from "@/components/event-log"
import { useApiData } from "@/hooks/use-api-data"

export default function Dashboard() {
  const [mode, setMode] = useState<"paper" | "live">("paper")
  const { run, positions, snapshots, legs, heartbeats, events } = useApiData(mode, 5000)
  const isPaused = useMemo(() => run?.status === "paused", [run])

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header mode={mode} setMode={setMode} />
      <main className="p-4 space-y-4">
        {/* Top row: Status + Portfolio */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <RunStatus key={mode} isPaused={isPaused} run={run} heartbeats={heartbeats} />
          <div className="lg:col-span-2">
            <PortfolioOverview key={mode} run={run} positions={positions} snapshots={snapshots} legs={legs} />
          </div>
        </div>

        {/* Middle: Positions Table */}
        <PositionsTable key={mode} run={run} positions={positions} snapshots={snapshots} />

        {/* Bottom row: Controls + Event Log */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <Controls isPaused={isPaused} />
          <div className="lg:col-span-2">
            <EventLog key={mode} events={events} />
          </div>
        </div>
      </main>
    </div>
  )
}
