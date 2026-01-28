"use client"

import { useEffect, useMemo, useState } from "react"

type Mode = "paper" | "live"

const FIELDS = [
  { key: "STATUS", label: "Status (on/off)", type: "text" },
  { key: "ENTRY_TIME_UTC", label: "Entry Time UTC (HH:MM)", type: "text" },
  { key: "TRADE_WEEKENDS", label: "Trade Weekends (true/false)", type: "text" },
  { key: "NUM_LEGS", label: "Num Legs", type: "number" },
  { key: "MARGIN_PER_LEG_USDT", label: "Margin per Leg (USDT)", type: "number" },
  { key: "LEVERAGE", label: "Leverage", type: "number" },
  { key: "MAX_PUMP_PCT", label: "Max Pump %", type: "number" },
  { key: "GLOBAL_KILL_DD_PCT", label: "Global Kill DD %", type: "number" },
  { key: "POLL_INTERVAL_SEC", label: "Poll Interval (sec)", type: "number" },
  { key: "STRATEGY_TAG", label: "Strategy Tag (S1/S2/S3)", type: "text" },
  { key: "HOLD_HOURS", label: "Hold Hours", type: "number" },
  { key: "INITIAL_BALANCE", label: "Initial Investment (USDT)", type: "number" },
]

function getAuthHeader(user: string, pass: string) {
  const token = btoa(`${user}:${pass}`)
  return `Basic ${token}`
}

export default function SettingsPage() {
  const [user, setUser] = useState("")
  const [pass, setPass] = useState("")
  const [authReady, setAuthReady] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [settings, setSettings] = useState<Record<Mode, Record<string, string>>>({
    paper: {},
    live: {},
  })

  useEffect(() => {
    const saved = localStorage.getItem("settings_auth")
    if (saved) {
      try {
        const { user: u, pass: p } = JSON.parse(saved)
        setUser(u || "")
        setPass(p || "")
        setAuthReady(true)
      } catch {
        // ignore
      }
    }
  }, [])

  const authHeader = useMemo(() => {
    if (!user || !pass) return null
    return getAuthHeader(user, pass)
  }, [user, pass])

  const fetchSettings = async (mode: Mode) => {
    if (!authHeader) return
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/settings?mode=${mode}`, {
      headers: { Authorization: authHeader },
      cache: "no-store",
    })
    if (!res.ok) {
      throw new Error(`Failed to load ${mode} settings`)
    }
    const data = await res.json()
    return data.settings || {}
  }

  const loadAll = async () => {
    if (!authHeader) return
    setLoading(true)
    setError(null)
    setSuccess(null)
    try {
      const [paper, live] = await Promise.all([fetchSettings("paper"), fetchSettings("live")])
      setSettings({ paper, live })
    } catch (e: any) {
      setError(e?.message || "Failed to load settings")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (authReady) {
      loadAll()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authReady, authHeader])

  const saveAuth = () => {
    if (!user || !pass) return
    localStorage.setItem("settings_auth", JSON.stringify({ user, pass }))
    setAuthReady(true)
  }

  const updateField = (mode: Mode, key: string, value: string) => {
    setSettings((prev) => ({
      ...prev,
      [mode]: { ...prev[mode], [key]: value },
    }))
  }

  const saveMode = async (mode: Mode) => {
    if (!authHeader) return
    setLoading(true)
    setError(null)
    setSuccess(null)
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/settings?mode=${mode}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: authHeader,
        },
        body: JSON.stringify({ settings: settings[mode] }),
      })
      if (!res.ok) {
        throw new Error(`Failed to save ${mode} settings`)
      }
      await loadAll()
      setSuccess(`${mode.toUpperCase()} settings saved`)
    } catch (e: any) {
      setError(e?.message || "Failed to save settings")
    } finally {
      setLoading(false)
    }
  }

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
      <div className="rounded border border-border bg-card p-4">
        <h1 className="text-lg font-semibold">Settings</h1>
        <p className="text-xs text-muted-foreground mt-1">
          Basic auth required to view and edit settings.
        </p>
        <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-center">
          <input
            className="h-10 w-full rounded border border-border bg-background px-3 text-base"
            placeholder="Username"
            value={user}
            onChange={(e) => setUser(e.target.value)}
          />
          <input
            className="h-10 w-full rounded border border-border bg-background px-3 text-base"
            placeholder="Password"
            type="password"
            value={pass}
            onChange={(e) => setPass(e.target.value)}
          />
          <button
            className="h-10 rounded bg-primary px-4 text-base font-medium text-primary-foreground"
            onClick={saveAuth}
          >
            Save
          </button>
        </div>
        {error && <div className="mt-3 text-sm text-loss">{error}</div>}
        {success && <div className="mt-3 text-sm text-profit">{success}</div>}
      </div>

      {authReady && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {(["paper", "live"] as Mode[]).map((mode) => (
            <div key={mode} className="rounded border border-border bg-card p-4">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-base font-medium text-muted-foreground">
                  {mode.toUpperCase()} Settings
                </h2>
                <button
                  className="h-9 rounded bg-primary px-3 text-sm font-medium text-primary-foreground disabled:opacity-60"
                  onClick={() => saveMode(mode)}
                  disabled={loading}
                >
                  {loading ? "Saving..." : "Save"}
                </button>
              </div>
              <div className="grid grid-cols-1 gap-4">
                {FIELDS.map((field) => (
                  <label key={field.key} className="text-sm text-muted-foreground">
                    <span className="block mb-1 text-base text-foreground">{field.label}</span>
                    <input
                      className="h-10 w-full rounded border border-border bg-background px-3 text-base text-foreground"
                      type={field.type}
                      value={settings[mode]?.[field.key] || ""}
                      onChange={(e) => updateField(mode, field.key, e.target.value)}
                    />
                  </label>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
