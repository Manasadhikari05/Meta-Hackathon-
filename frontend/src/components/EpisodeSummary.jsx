import { Trophy, RotateCcw, Home, CheckCircle2, XCircle, AlertCircle } from 'lucide-react'

function grade(score) {
  if (score >= 0.90) return { letter: 'S', label: 'Outstanding', color: 'text-yellow-400', bg: 'bg-yellow-400/10 border-yellow-400/30' }
  if (score >= 0.75) return { letter: 'A', label: 'Excellent',   color: 'text-emerald-400', bg: 'bg-emerald-400/10 border-emerald-400/30' }
  if (score >= 0.60) return { letter: 'B', label: 'Good',        color: 'text-sky-400',     bg: 'bg-sky-400/10 border-sky-400/30' }
  if (score >= 0.45) return { letter: 'C', label: 'Average',     color: 'text-amber-400',   bg: 'bg-amber-400/10 border-amber-400/30' }
  return                       { letter: 'D', label: 'Needs Work',  color: 'text-rose-400',   bg: 'bg-rose-400/10 border-rose-400/30' }
}

const DEC_ICON = {
  approve:  { icon: CheckCircle2, color: 'text-emerald-400' },
  remove:   { icon: XCircle,      color: 'text-rose-400' },
  escalate: { icon: AlertCircle,  color: 'text-amber-400' },
}

export default function EpisodeSummary({ history, taskId, onReplay, onHome }) {
  const avg = history.length
    ? history.reduce((s, h) => s + h.reward.value, 0) / history.length
    : 0

  const g = grade(avg)
  const pct = Math.round(avg * 100)

  const decisionCounts = history.reduce((acc, h) => {
    acc[h.action.decision] = (acc[h.action.decision] ?? 0) + 1
    return acc
  }, {})

  return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center px-6 py-16">
      <div className="w-full max-w-2xl animate-slide-up">
        {/* grade card */}
        <div className={`border rounded-2xl p-10 text-center mb-6 ${g.bg}`}>
          <Trophy className={`w-10 h-10 mx-auto mb-4 ${g.color}`} />
          <div className={`text-8xl font-black mb-2 ${g.color}`}>{g.letter}</div>
          <p className="text-zinc-300 text-xl font-semibold mb-1">{g.label}</p>
          <p className="text-zinc-500 text-sm">
            {pct}% average · {history.length} steps · {taskId}
          </p>
        </div>

        {/* stats row */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          {Object.entries(decisionCounts).map(([dec, count]) => {
            const di = DEC_ICON[dec] ?? {}
            const Icon = di.icon ?? CheckCircle2
            return (
              <div key={dec} className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-center">
                <Icon className={`w-5 h-5 mx-auto mb-2 ${di.color}`} />
                <p className="text-2xl font-bold text-zinc-100">{count}</p>
                <p className="text-xs text-zinc-500 capitalize">{dec}d</p>
              </div>
            )
          })}
        </div>

        {/* step breakdown */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 mb-6">
          <p className="text-xs font-semibold uppercase tracking-widest text-zinc-500 mb-4">Step Breakdown</p>
          <div className="space-y-2">
            {history.map((h, i) => {
              const di = DEC_ICON[h.action.decision] ?? {}
              const Icon = di.icon ?? CheckCircle2
              const v = h.reward.value
              const bar = Math.round(v * 100)
              return (
                <div key={i} className="flex items-center gap-3">
                  <span className="text-xs text-zinc-600 w-6 text-right">{i + 1}</span>
                  <Icon className={`w-4 h-4 shrink-0 ${di.color}`} />
                  <div className="flex-1 h-2 bg-zinc-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${v >= 0.75 ? 'bg-emerald-500' : v >= 0.45 ? 'bg-amber-500' : 'bg-rose-500'}`}
                      style={{ width: `${bar}%` }}
                    />
                  </div>
                  <span className="text-xs font-mono text-zinc-400 w-10 text-right">{bar}%</span>
                </div>
              )
            })}
          </div>
        </div>

        {/* actions */}
        <div className="flex gap-4">
          <button
            onClick={onHome}
            className="flex-1 flex items-center justify-center gap-2 py-3.5 rounded-xl
              bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-zinc-300 text-sm font-semibold
              transition-all duration-200"
          >
            <Home className="w-4 h-4" /> Home
          </button>
          <button
            onClick={onReplay}
            className="flex-1 flex items-center justify-center gap-2 py-3.5 rounded-xl
              bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold
              transition-all duration-200 shadow-[0_0_20px_rgba(99,102,241,.25)]"
          >
            <RotateCcw className="w-4 h-4" /> Play Again
          </button>
        </div>
      </div>
    </div>
  )
}
