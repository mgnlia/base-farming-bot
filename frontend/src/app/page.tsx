'use client'
import { useEffect, useState, useRef } from 'react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Status {
  status: string
  simulation_mode: boolean
  portfolio_value: number
  realized_pnl: number
  defi_earned: number
  protocol_coverage: number
  nft_count: number
  nft_score: number
  bridge_score: number
  trade_count_today: number
  risk_metrics: {
    current_drawdown: number
    max_drawdown_pct: number
    daily_loss_usd: number
    daily_loss_cap_usd: number
    is_halted: boolean
  }
  scheduler: { total_tx: number; days_active: number; consistency_score: number }
}

interface Event {
  type: string
  timestamp: number
  [key: string]: unknown
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    running: 'bg-green-500',
    stopped: 'bg-gray-500',
    halted: 'bg-red-500',
  }
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-bold ${colors[status] ?? 'bg-gray-600'}`}>
      <span className={`w-2 h-2 rounded-full ${status === 'running' ? 'animate-pulse bg-white' : 'bg-white/60'}`} />
      {status.toUpperCase()}
    </span>
  )
}

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      <p className="text-2xl font-bold text-white">{value}</p>
      {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
    </div>
  )
}

export default function Home() {
  const [status, setStatus] = useState<Status | null>(null)
  const [events, setEvents] = useState<Event[]>([])
  const [connected, setConnected] = useState(false)
  const [loading, setLoading] = useState(false)
  const eventsRef = useRef<Event[]>([])

  const fetchStatus = async () => {
    try {
      const r = await fetch(`${API}/api/status`)
      if (r.ok) setStatus(await r.json())
    } catch {}
  }

  useEffect(() => {
    fetchStatus()
    const iv = setInterval(fetchStatus, 5000)

    const es = new EventSource(`${API}/api/stream`)
    es.onopen = () => setConnected(true)
    es.onerror = () => setConnected(false)
    es.onmessage = (e) => {
      try {
        const ev: Event = JSON.parse(e.data)
        eventsRef.current = [ev, ...eventsRef.current].slice(0, 100)
        setEvents([...eventsRef.current])
        if (ev.type === 'status_update') fetchStatus()
      } catch {}
    }

    return () => { clearInterval(iv); es.close() }
  }, [])

  const callApi = async (endpoint: string) => {
    setLoading(true)
    try {
      await fetch(`${API}${endpoint}`, { method: 'POST' })
      await fetchStatus()
    } finally { setLoading(false) }
  }

  const pnlColor = (v: number) => v >= 0 ? 'text-green-400' : 'text-red-400'
  const drawdownPct = status ? (status.risk_metrics.current_drawdown * 100).toFixed(1) : '0.0'

  return (
    <main className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
            ⛓ Base Farming Bot
          </h1>
          <p className="text-gray-400 text-sm mt-1">Automated Base L2 airdrop farming — DeFi · NFT · Bridge</p>
        </div>
        <div className="flex items-center gap-3">
          {status && <StatusBadge status={status.status} />}
          {status?.simulation_mode && (
            <span className="px-2 py-0.5 rounded bg-yellow-600/30 text-yellow-400 text-xs font-bold border border-yellow-600/50">SIM MODE</span>
          )}
          <span className={`w-2 h-2 rounded-full ${connected ? 'bg-green-400 animate-pulse' : 'bg-gray-600'}`} title={connected ? 'SSE connected' : 'SSE disconnected'} />
        </div>
      </div>

      {/* Controls */}
      <div className="flex gap-3">
        <button onClick={() => callApi('/api/agent/start')} disabled={loading || status?.status === 'running'}
          className="px-4 py-2 bg-green-600 hover:bg-green-500 disabled:opacity-40 rounded-lg font-semibold text-sm transition">
          ▶ Start
        </button>
        <button onClick={() => callApi('/api/agent/stop')} disabled={loading || status?.status !== 'running'}
          className="px-4 py-2 bg-red-700 hover:bg-red-600 disabled:opacity-40 rounded-lg font-semibold text-sm transition">
          ■ Stop
        </button>
        <button onClick={() => callApi('/api/agent/resume')} disabled={loading || status?.status !== 'halted'}
          className="px-4 py-2 bg-yellow-600 hover:bg-yellow-500 disabled:opacity-40 rounded-lg font-semibold text-sm transition">
          ↺ Resume
        </button>
      </div>

      {/* Stats grid */}
      {status && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Portfolio Value" value={`$${status.portfolio_value.toLocaleString()}`} />
            <StatCard label="DeFi Earned" value={`$${status.defi_earned.toFixed(2)}`} sub={`${status.protocol_coverage} protocols`} />
            <StatCard label="NFT Score" value={status.nft_score.toFixed(1)} sub={`${status.nft_count} mints`} />
            <StatCard label="Bridge Score" value={status.bridge_score.toFixed(1)} sub="cross-chain" />
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Trades Today" value={status.trade_count_today} />
            <StatCard label="Days Active" value={status.scheduler.days_active} sub={`Consistency: ${status.scheduler.consistency_score.toFixed(0)}/100`} />
            <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
              <p className="text-xs text-gray-400 mb-1">Drawdown</p>
              <p className={`text-2xl font-bold ${parseFloat(drawdownPct) > 10 ? 'text-red-400' : 'text-white'}`}>{drawdownPct}%</p>
              <div className="mt-2 h-1.5 bg-gray-700 rounded-full">
                <div className="h-full bg-red-500 rounded-full transition-all" style={{ width: `${Math.min(100, parseFloat(drawdownPct) / status.risk_metrics.max_drawdown_pct)}%` }} />
              </div>
              <p className="text-xs text-gray-500 mt-1">max {(status.risk_metrics.max_drawdown_pct * 100).toFixed(0)}%</p>
            </div>
            <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
              <p className="text-xs text-gray-400 mb-1">Daily Loss</p>
              <p className={`text-2xl font-bold ${status.risk_metrics.daily_loss_usd < -100 ? 'text-red-400' : 'text-white'}`}>
                ${Math.abs(status.risk_metrics.daily_loss_usd).toFixed(0)}
              </p>
              <p className="text-xs text-gray-500 mt-1">cap ${status.risk_metrics.daily_loss_cap_usd}</p>
            </div>
          </div>

          {status.risk_metrics.is_halted && (
            <div className="bg-red-900/30 border border-red-600 rounded-xl p-4 text-red-300 font-semibold">
              🚨 Risk circuit breaker triggered — bot halted. Click Resume to restart with reset drawdown tracking.
            </div>
          )}
        </>
      )}

      {/* Event log */}
      <div className="bg-gray-900 rounded-xl border border-gray-800">
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
          <h2 className="font-semibold text-sm">Live Event Log</h2>
          <span className="text-xs text-gray-500">{events.length} events</span>
        </div>
        <div className="divide-y divide-gray-800/50 max-h-96 overflow-y-auto">
          {events.length === 0 && (
            <p className="text-gray-500 text-sm p-4">No events yet — start the bot to see activity.</p>
          )}
          {events.map((ev, i) => (
            <div key={i} className="px-4 py-2 text-xs font-mono flex items-start gap-3">
              <span className="text-gray-500 shrink-0">{new Date(ev.timestamp * 1000).toLocaleTimeString()}</span>
              <span className={`shrink-0 px-1.5 py-0.5 rounded text-xs font-bold ${
                ev.type.includes('error') || ev.type.includes('halt') ? 'bg-red-900/60 text-red-300' :
                ev.type.includes('nft') ? 'bg-purple-900/60 text-purple-300' :
                ev.type.includes('bridge') ? 'bg-blue-900/60 text-blue-300' :
                ev.type.includes('defi') || ev.type.includes('swap') ? 'bg-green-900/60 text-green-300' :
                'bg-gray-800 text-gray-400'
              }`}>{ev.type}</span>
              <span className="text-gray-300 break-all">{JSON.stringify(Object.fromEntries(Object.entries(ev).filter(([k]) => !['type','timestamp'].includes(k))))}</span>
            </div>
          ))}
        </div>
      </div>

      <footer className="text-center text-xs text-gray-600 pb-4">
        Base Farming Bot — SIMULATION MODE ONLY — Not financial advice
      </footer>
    </main>
  )
}
