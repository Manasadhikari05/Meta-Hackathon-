import { useEffect, useState, useMemo } from 'react'
import { ChevronLeft, BarChart3, RefreshCw, AlertCircle } from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

function metricsUrl() {
  const raw = (import.meta.env.VITE_BACKEND_URL || '').trim().replace(/\/$/, '')
  return raw ? `${raw}/training/metrics` : '/api/training/metrics'
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

  const chartRows = useMemo(() => {
    if (!data?.before || !data?.after) return []
    const b = data.before
    const a = data.after
    return [
      { name: 'Mean reward', before: b.mean_reward, after: a.mean_reward },
      { name: 'Decision accuracy', before: b.decision_accuracy, after: a.decision_accuracy },
      {
        name: 'Latency (ms)',
        before: Math.round(b.mean_latency_ms || 0),
        after: Math.round(a.mean_latency_ms || 0),
      },
    ]
  }, [data])

  const eff = data?.efficiency

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
            RL training — before vs after
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
                python scripts/rl_trainer.py eval-comparison --best-of 4 --limit 40
              </pre>
              <p className="text-xs text-zinc-500 mt-2">
                Or open <code className="text-indigo-300">RLtrainer.ipynb</code> at the repo root and run all cells.
              </p>
            </div>
          </div>
        )}

        {data?.loaded && data.before && data.after && (
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
                <div className="text-xs uppercase tracking-wide text-zinc-500">Policies</div>
                <div className="text-sm text-zinc-300 mt-1">
                  <span className="text-indigo-400">Before:</span> {data.before.policy}
                  <br />
                  <span className="text-emerald-400">After:</span> {data.after.policy}
                </div>
              </div>
            </div>

            {eff && (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4">
                  <div className="text-xs text-zinc-500">Reward gain</div>
                  <div className="text-2xl font-semibold text-emerald-400 tabular-nums">
                    {eff.mean_reward_delta >= 0 ? '+' : ''}
                    {eff.mean_reward_delta}
                  </div>
                </div>
                <div className="rounded-xl border border-indigo-500/20 bg-indigo-500/5 p-4">
                  <div className="text-xs text-zinc-500">Accuracy Δ (pp)</div>
                  <div className="text-2xl font-semibold text-indigo-300 tabular-nums">
                    {eff.accuracy_delta_pp >= 0 ? '+' : ''}
                    {eff.accuracy_delta_pp}
                  </div>
                </div>
                <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4">
                  <div className="text-xs text-zinc-500">Latency ratio (after / before)</div>
                  <div className="text-2xl font-semibold text-amber-200 tabular-nums">
                    {eff.latency_ratio}x
                  </div>
                  <div className="text-[11px] text-zinc-500 mt-1">
                    Best-of-N trades compute for quality; LoRA + greedy can lower this again.
                  </div>
                </div>
              </div>
            )}

            <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-4 h-[360px]">
              <div className="text-sm font-medium text-zinc-300 mb-3">Before vs after (same eval set)</div>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartRows} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#3f3f46" />
                  <XAxis dataKey="name" tick={{ fill: '#a1a1aa', fontSize: 11 }} />
                  <YAxis tick={{ fill: '#a1a1aa', fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{ background: '#18181b', border: '1px solid #3f3f46', borderRadius: 8 }}
                    labelStyle={{ color: '#e4e4e7' }}
                  />
                  <Legend />
                  <Bar dataKey="before" name="Before" fill="#6366f1" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="after" name="After" fill="#22c55e" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div className="rounded-xl border border-zinc-800 p-4">
                <div className="text-xs uppercase text-zinc-500 mb-2">Before snapshot</div>
                <pre className="text-xs text-zinc-400 overflow-x-auto whitespace-pre-wrap">
                  {JSON.stringify(data.before, null, 2)}
                </pre>
              </div>
              <div className="rounded-xl border border-zinc-800 p-4">
                <div className="text-xs uppercase text-zinc-500 mb-2">After snapshot</div>
                <pre className="text-xs text-zinc-400 overflow-x-auto whitespace-pre-wrap">
                  {JSON.stringify(data.after, null, 2)}
                </pre>
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
