import { useEffect, useState, useMemo } from 'react'
import { ChevronLeft, BarChart3, RefreshCw, AlertCircle, Sparkles } from 'lucide-react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
  ReferenceDot,
} from 'recharts'

function metricsUrl() {
  const raw = (import.meta.env.VITE_BACKEND_URL || '').trim().replace(/\/$/, '')
  return raw ? `${raw}/training/metrics` : '/api/training/metrics'
}

function fmt(n, digits = 3) {
  if (n === null || n === undefined || Number.isNaN(n)) return '—'
  return Number(n).toFixed(digits)
}

export default function TrainingMetrics({ onBack }) {
  const [data, setData] = useState(null)
  const [err, setErr] = useState(null)
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    setErr(null)
    try {
      const r = await fetch(metricsUrl())
      const j = await r.json()
      setData(j)
    } catch (e) {
      setErr(e.message || String(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const iters = data?.iterations || []
  const rows = useMemo(
    () =>
      iters.map((it) => ({
        step: it.step,
        label: it.label,
        reward: Number(it.mean_reward),
        accuracy: Number(it.decision_accuracy) * 100,
        latency: Math.round(it.mean_latency_ms || 0),
        real: it.real_measurement ? 1 : 0,
      })),
    [iters]
  )

  const eff = data?.efficiency
  const finalRow = rows[rows.length - 1]
  const firstRow = rows[0]

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <header className="sticky top-0 z-30 bg-zinc-950/90 backdrop-blur border-b border-zinc-800/60">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between gap-4">
          <button
            type="button"
            onClick={onBack}
            className="flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-200 transition"
          >
            <ChevronLeft className="w-4 h-4" /> Home
          </button>
          <div className="flex items-center gap-2 text-sm font-semibold text-zinc-100">
            <BarChart3 className="w-4 h-4 text-indigo-400" />
            RL training trajectory
          </div>
          <button
            type="button"
            onClick={load}
            className="inline-flex items-center gap-1.5 text-xs text-indigo-300 hover:text-indigo-100"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-10 space-y-8">
        {loading && <p className="text-zinc-500 text-sm">Loading metrics…</p>}
        {err && (
          <div className="rounded-lg border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
            {err}
          </div>
        )}

        {!loading && data && !data.loaded && (
          <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-6 flex gap-3">
            <AlertCircle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-amber-100">No metrics file yet</p>
              <p className="text-sm text-amber-200/80 mt-1">{data.message}</p>
              <pre className="mt-3 text-xs bg-zinc-900/80 rounded-md p-3 text-zinc-400 overflow-x-auto">
                python scripts/_run_demo.py
              </pre>
            </div>
          </div>
        )}

        {data?.loaded && rows.length > 0 && (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
                <div className="text-xs uppercase tracking-wide text-zinc-500">Model</div>
                <div className="text-sm font-medium text-zinc-200 mt-1 break-all">
                  {data.model_id || '—'}
                </div>
              </div>
              <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
                <div className="text-xs uppercase tracking-wide text-zinc-500">Updated</div>
                <div className="text-sm font-medium text-zinc-200 mt-1">
                  {data.updated_at || '—'}
                </div>
              </div>
              <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
                <div className="text-xs uppercase tracking-wide text-zinc-500">Iterations</div>
                <div className="text-sm font-medium text-zinc-200 mt-1">
                  {rows.length} steps · {rows.filter((r) => r.real).length} real measurements
                </div>
              </div>
            </div>

            {eff && (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4">
                  <div className="text-xs text-zinc-500">Reward gain (start → end)</div>
                  <div className="text-2xl font-semibold text-emerald-400 tabular-nums">
                    {eff.mean_reward_delta >= 0 ? '+' : ''}
                    {eff.mean_reward_delta}
                  </div>
                  <div className="text-[11px] text-zinc-500 mt-1">
                    {fmt(firstRow?.reward)} → {fmt(finalRow?.reward)}
                  </div>
                </div>
                <div className="rounded-xl border border-indigo-500/20 bg-indigo-500/5 p-4">
                  <div className="text-xs text-zinc-500">Accuracy Δ (pp)</div>
                  <div className="text-2xl font-semibold text-indigo-300 tabular-nums">
                    {eff.accuracy_delta_pp >= 0 ? '+' : ''}
                    {eff.accuracy_delta_pp}
                  </div>
                  <div className="text-[11px] text-zinc-500 mt-1">
                    {fmt(firstRow?.accuracy, 1)}% → {fmt(finalRow?.accuracy, 1)}%
                  </div>
                </div>
                <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4">
                  <div className="text-xs text-zinc-500">Compute cost (latency)</div>
                  <div className="text-2xl font-semibold text-amber-200 tabular-nums">
                    {eff.latency_ratio}x
                  </div>
                  <div className="text-[11px] text-zinc-500 mt-1">
                    LLM trades latency for quality; LoRA SFT brings it back down.
                  </div>
                </div>
              </div>
            )}

            <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-4 h-[380px]">
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="w-4 h-4 text-emerald-400" />
                <div className="text-sm font-medium text-zinc-300">
                  Mean reward & decision accuracy across training rollouts
                </div>
              </div>
              <ResponsiveContainer width="100%" height="92%">
                <AreaChart data={rows} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="rewardFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#22c55e" stopOpacity={0.4} />
                      <stop offset="100%" stopColor="#22c55e" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="accFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#6366f1" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#3f3f46" />
                  <XAxis
                    dataKey="step"
                    tick={{ fill: '#a1a1aa', fontSize: 11 }}
                    label={{
                      value: 'training rollout',
                      position: 'insideBottom',
                      offset: -4,
                      fill: '#71717a',
                      fontSize: 11,
                    }}
                  />
                  <YAxis
                    yAxisId="reward"
                    tick={{ fill: '#a1a1aa', fontSize: 11 }}
                    domain={[0, 1]}
                    tickFormatter={(v) => v.toFixed(2)}
                  />
                  <YAxis
                    yAxisId="acc"
                    orientation="right"
                    tick={{ fill: '#a1a1aa', fontSize: 11 }}
                    domain={[0, 100]}
                    tickFormatter={(v) => `${v.toFixed(0)}%`}
                  />
                  <Tooltip
                    contentStyle={{
                      background: '#18181b',
                      border: '1px solid #3f3f46',
                      borderRadius: 8,
                    }}
                    labelStyle={{ color: '#e4e4e7' }}
                    formatter={(value, key) => {
                      if (key === 'reward') return [Number(value).toFixed(3), 'Mean reward']
                      if (key === 'accuracy')
                        return [`${Number(value).toFixed(1)}%`, 'Decision accuracy']
                      return [value, key]
                    }}
                    labelFormatter={(step) => {
                      const r = rows.find((x) => x.step === step)
                      return r ? `Step ${step} — ${r.label}` : `Step ${step}`
                    }}
                  />
                  <Legend />
                  <Area
                    yAxisId="reward"
                    type="monotone"
                    dataKey="reward"
                    stroke="#22c55e"
                    strokeWidth={2.5}
                    fill="url(#rewardFill)"
                    name="Mean reward"
                    dot={{ r: 3, fill: '#22c55e' }}
                    activeDot={{ r: 5 }}
                  />
                  <Area
                    yAxisId="acc"
                    type="monotone"
                    dataKey="accuracy"
                    stroke="#6366f1"
                    strokeWidth={2.5}
                    fill="url(#accFill)"
                    name="Decision accuracy (%)"
                    dot={{ r: 3, fill: '#6366f1' }}
                    activeDot={{ r: 5 }}
                  />
                  {rows
                    .filter((r) => r.real)
                    .map((r) => (
                      <ReferenceDot
                        key={`anchor-${r.step}`}
                        yAxisId="reward"
                        x={r.step}
                        y={r.reward}
                        r={6}
                        stroke="#fbbf24"
                        strokeWidth={2}
                        fill="#fbbf24"
                        isFront
                      />
                    ))}
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-4 h-[260px]">
              <div className="text-sm font-medium text-zinc-300 mb-3">
                Latency per decision (ms) — compute trade-off
              </div>
              <ResponsiveContainer width="100%" height="86%">
                <LineChart data={rows} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#3f3f46" />
                  <XAxis dataKey="step" tick={{ fill: '#a1a1aa', fontSize: 11 }} />
                  <YAxis tick={{ fill: '#a1a1aa', fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{
                      background: '#18181b',
                      border: '1px solid #3f3f46',
                      borderRadius: 8,
                    }}
                    labelStyle={{ color: '#e4e4e7' }}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="latency"
                    stroke="#f59e0b"
                    strokeWidth={2.5}
                    name="Latency (ms / decision)"
                    dot={{ r: 3, fill: '#f59e0b' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
              <div className="text-sm font-medium text-zinc-300 mb-3">
                Per-step ablation cascade
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead className="text-zinc-500">
                    <tr className="border-b border-zinc-800">
                      <th className="py-2 px-2 text-left">step</th>
                      <th className="py-2 px-2 text-left">policy slice</th>
                      <th className="py-2 px-2 text-right">reward</th>
                      <th className="py-2 px-2 text-right">accuracy</th>
                      <th className="py-2 px-2 text-right">latency (ms)</th>
                      <th className="py-2 px-2 text-center">measured?</th>
                    </tr>
                  </thead>
                  <tbody className="text-zinc-300">
                    {rows.map((r) => (
                      <tr key={r.step} className="border-b border-zinc-800/60">
                        <td className="py-1.5 px-2 tabular-nums text-zinc-500">{r.step}</td>
                        <td className="py-1.5 px-2">{r.label}</td>
                        <td className="py-1.5 px-2 text-right tabular-nums">
                          {fmt(r.reward)}
                        </td>
                        <td className="py-1.5 px-2 text-right tabular-nums">
                          {fmt(r.accuracy, 1)}%
                        </td>
                        <td className="py-1.5 px-2 text-right tabular-nums text-amber-300/80">
                          {r.latency.toLocaleString()}
                        </td>
                        <td className="py-1.5 px-2 text-center">
                          {r.real ? (
                            <span className="text-amber-300">● real</span>
                          ) : (
                            <span className="text-zinc-600">projected</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {data.notes && (
              <p className="text-xs text-zinc-500 border-t border-zinc-800 pt-4">{data.notes}</p>
            )}
          </>
        )}
      </main>
    </div>
  )
}
