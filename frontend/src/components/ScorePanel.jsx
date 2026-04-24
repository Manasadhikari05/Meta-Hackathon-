import { useEffect, useRef, useState } from 'react'
import { CheckCircle2, XCircle, AlertCircle, TrendingUp } from 'lucide-react'

const DECISION_ICON = {
  approve:  { icon: CheckCircle2, color: 'text-emerald-400' },
  remove:   { icon: XCircle,      color: 'text-rose-400' },
  escalate: { icon: AlertCircle,  color: 'text-amber-400' },
}

function scoreColor(v) {
  if (v >= 0.75) return 'text-emerald-400'
  if (v >= 0.45) return 'text-amber-400'
  return 'text-rose-400'
}

function scoreBg(v) {
  if (v >= 0.75) return 'bg-emerald-500'
  if (v >= 0.45) return 'bg-amber-500'
  return 'bg-rose-500'
}

function useAnimatedValue(target, duration = 600) {
  const [display, setDisplay] = useState(target)
  const frame = useRef(null)
  const prev = useRef(target)

  useEffect(() => {
    const from = prev.current
    const to = target
    const start = performance.now()
    cancelAnimationFrame(frame.current)
    frame.current = requestAnimationFrame(function tick(now) {
      const t = Math.min((now - start) / duration, 1)
      const ease = t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t
      setDisplay(from + (to - from) * ease)
      if (t < 1) frame.current = requestAnimationFrame(tick)
      else prev.current = to
    })
    return () => cancelAnimationFrame(frame.current)
  }, [target, duration])

  return display
}

const TASK_MAX = { task1: 1, task2: 8, task3: 12 }
const WEIGHT_ROWS = [
  { label: 'Decision',   weight: 50 },
  { label: 'Reason',     weight: 30 },
  { label: 'Severity',   weight: 20 },
]

export default function ScorePanel({ history, taskId, lastReward }) {
  const avgScore = history.length
    ? history.reduce((s, h) => s + h.reward.value, 0) / history.length
    : 0

  const animScore = useAnimatedValue(avgScore)
  const maxSteps = TASK_MAX[taskId] ?? 1
  const pct = Math.round(animScore * 100)

  return (
    <div className="space-y-4">
      {/* Episode score */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <p className="text-xs font-semibold uppercase tracking-widest text-zinc-500">Episode Score</p>
          <TrendingUp className="w-4 h-4 text-zinc-600" />
        </div>

        <div className={`text-5xl font-bold tabular-nums mb-1 ${scoreColor(animScore)} ${lastReward ? 'animate-score-pop' : ''}`}>
          {pct.toString().padStart(2, '0')}
          <span className="text-2xl font-normal text-zinc-500">%</span>
        </div>
        <p className="text-xs text-zinc-600 mb-4">
          {history.length} / {maxSteps} steps · avg reward {animScore.toFixed(3)}
        </p>

        {/* score bar */}
        <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full score-fill ${scoreBg(animScore)}`}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      {/* Step history */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
        <p className="text-xs font-semibold uppercase tracking-widest text-zinc-500 mb-4">Step History</p>
        {history.length === 0 ? (
          <p className="text-zinc-600 text-sm text-center py-4">No steps yet</p>
        ) : (
          <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
            {[...history].reverse().map((h, i) => {
              const di = DECISION_ICON[h.action.decision] ?? {}
              const Icon = di.icon ?? CheckCircle2
              const v = h.reward.value
              return (
                <div
                  key={history.length - 1 - i}
                  className="flex items-center gap-3 p-3 rounded-xl bg-zinc-800/40 border border-zinc-700/40 animate-fade-in"
                >
                  <Icon className={`w-4 h-4 shrink-0 ${di.color}`} />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-mono text-zinc-400 truncate">
                      {h.obs?.post?.post_id ?? `step-${history.length - i}`}
                    </p>
                    <p className="text-[11px] text-zinc-600 capitalize">
                      {h.action.reason_code?.replace(/_/g, ' ')} · {h.action.severity}
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <span className={`text-xs font-bold tabular-nums ${scoreColor(v)}`}>
                      {(v * 100).toFixed(0)}%
                    </span>
                    <div className="h-1 w-12 bg-zinc-700 rounded-full mt-1 overflow-hidden">
                      <div
                        className={`h-full rounded-full ${scoreBg(v)}`}
                        style={{ width: `${v * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Grading weights */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
        <p className="text-xs font-semibold uppercase tracking-widest text-zinc-500 mb-4">Score Weights</p>
        <div className="space-y-3">
          {WEIGHT_ROWS.map(({ label, weight }) => (
            <div key={label}>
              <div className="flex justify-between text-xs mb-1.5">
                <span className="text-zinc-400">{label}</span>
                <span className="text-zinc-500 font-mono">{weight}%</span>
              </div>
              <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-indigo-500/60 rounded-full score-fill"
                  style={{ width: `${weight}%` }}
                />
              </div>
            </div>
          ))}
          {taskId === 'task3' && (
            <p className="text-[11px] text-zinc-600 pt-1">
              + 30% explanation quality in task3 (overlaid on base score)
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
