"use client"

import { useEffect, useRef } from "react"
import { Circle } from "lucide-react"

interface LogEntry {
  id: string
  timestamp: string
  type: "info" | "trade" | "tp" | "sl" | "error" | "warning"
  message: string
}

interface EventLogProps {
  events: any[]
}

export function EventLog({ events }: EventLogProps) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const logs: LogEntry[] = (events || []).map((e, idx) => ({
    id: `${idx}`,
    timestamp: e.ts?.slice(11, 19) || "--:--:--",
    type: e.level === "error" ? "error" : e.level === "warn" ? "warning" : "info",
    message: `${e.type}: ${e.message}`,
  }))

  useEffect(() => {
    // Auto-scroll to bottom when new logs arrive
    if (scrollRef.current) {
      scrollRef.current.scrollTop = 0
    }
  }, [])

  const getTypeColor = (type: LogEntry["type"]) => {
    switch (type) {
      case "trade":
        return "text-primary"
      case "tp":
        return "text-profit"
      case "sl":
        return "text-loss"
      case "error":
        return "text-loss"
      case "warning":
        return "text-warning"
      default:
        return "text-muted-foreground"
    }
  }

  const getTypeDot = (type: LogEntry["type"]) => {
    switch (type) {
      case "trade":
        return "fill-primary text-primary"
      case "tp":
        return "fill-profit text-profit"
      case "sl":
        return "fill-loss text-loss"
      case "error":
        return "fill-loss text-loss"
      case "warning":
        return "fill-warning text-warning"
      default:
        return "fill-muted-foreground text-muted-foreground"
    }
  }

  return (
    <div className="rounded border border-border bg-card">
      <div className="border-b border-border px-4 py-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-medium text-muted-foreground">Event Log</h2>
          <div className="flex items-center gap-2">
            <Circle className="h-2 w-2 fill-profit text-profit animate-pulse" />
            <span className="text-xs text-muted-foreground">Live</span>
          </div>
        </div>
      </div>

      <div
        ref={scrollRef}
        className="h-[200px] overflow-y-auto p-2 font-mono text-xs"
      >
        {logs.map((log) => (
          <div
            key={log.id}
            className="flex items-start gap-2 rounded px-2 py-1.5 hover:bg-secondary/30"
          >
            <Circle className={`mt-1 h-2 w-2 flex-shrink-0 ${getTypeDot(log.type)}`} />
            <span className="text-muted-foreground flex-shrink-0">
              {log.timestamp}
            </span>
            <span className={`${getTypeColor(log.type)} break-all`}>
              {log.message}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
