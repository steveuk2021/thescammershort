"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"

export function useApiData(mode: "paper" | "live", pollMs: number = 5000) {
  const [run, setRun] = useState<any | null>(null)
  const [positions, setPositions] = useState<any[]>([])
  const [snapshots, setSnapshots] = useState<any[]>([])
  const [legs, setLegs] = useState<any[]>([])
  const [heartbeats, setHeartbeats] = useState<any[]>([])
  const [events, setEvents] = useState<any[]>([])

  useEffect(() => {
    let mounted = true
    // clear stale data immediately on mode change
    setRun(null)
    setPositions([])
    setSnapshots([])
    setLegs([])
    setEvents([])

    const fetchAll = async () => {
      try {
        const r = await api.getLatestRun(mode)
        const runId = r.run?.run_id
        const [p, s, l, h, e] = await Promise.all([
          api.getOpenPositions(runId),
          api.getLatestSnapshots(200, runId),
          api.getLegs(runId),
          api.getLatestHeartbeats(20),
          api.getLatestEvents(50, runId),
        ])
        if (!mounted) return
        setRun(r.run || null)
        setPositions(p.positions || [])
        setSnapshots(s.snapshots || [])
        setLegs(l.legs || [])
        setHeartbeats(h.heartbeats || [])
        setEvents(e.events || [])
      } catch (err) {
        // swallow errors to keep UI alive
        console.error(err)
      }
    }

    fetchAll()
    const id = setInterval(fetchAll, pollMs)
    return () => {
      mounted = false
      clearInterval(id)
    }
  }, [pollMs, mode])

  return { run, positions, snapshots, legs, heartbeats, events }
}
