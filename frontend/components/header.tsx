"use client"

import { Activity } from "lucide-react"

interface HeaderProps {
  mode: "paper" | "live"
  setMode: (mode: "paper" | "live") => void
}

export function Header({ mode, setMode }: HeaderProps) {
  return (
    <header className="border-b border-border bg-card px-4 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Activity className="h-6 w-6 text-primary" />
            <h1 className="text-lg font-semibold text-foreground">
              THE SCAMMER SHORT
            </h1>
          </div>
          <span className="rounded bg-primary/20 px-2 py-0.5 text-xs font-medium text-primary">
            Phase 0
          </span>
        </div>
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <span>Bitget USDT-M Futures</span>
          <div className="flex items-center gap-2">
            <button
              className={`rounded px-2 py-0.5 text-xs font-medium ${
                mode === "paper" ? "bg-primary/20 text-primary" : "text-muted-foreground"
              }`}
              onClick={() => setMode("paper")}
            >
              Paper
            </button>
            <button
              className={`rounded px-2 py-0.5 text-xs font-medium ${
                mode === "live" ? "bg-primary/20 text-primary" : "text-muted-foreground"
              }`}
              onClick={() => setMode("live")}
            >
              Live
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}
