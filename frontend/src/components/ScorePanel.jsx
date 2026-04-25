import { useEffect, useRef, useState } from 'react'
import { CheckCircle2, XCircle, AlertCircle, TrendingUp, ChevronDown, Bot, MessageSquare } from 'lucide-react'

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
  const prev  = useRef(target)

  useEffect(() => {
    const from = prev.current
    const to   = target
    const start = performance.now()
    cancelAnimationFrame(frame.current)
    frame.current = requestAnimationFrame(function tick(now) {
      const t    = Math.min((now - start) / duration, 1)
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

function HistoryRow({ entry, index, total }) {
  const [open, setOpen] = useState(false)
  const di    = DECISION_ICON[entry.action.decision] ?? {}
  const Icon  = di.icon ?? CheckCircle2
  const v     = entry.reward.value
  const hasReasoning = !!entry.reasoning
  const hasNote = !!(entry.action.explanation || '').trim()

  return (
    <div className="rounded-xl border border-zinc-700/40 bg-zinc-800/40 overflow-hidden animate-fade-in">
      {/* collapsed row */}
      <button
        className="w-full flex items-center gap-3 p-3 text-left hover:bg-zinc-700/20 transition-colors"
        onClick={() => (hasReasoning || hasNote) && setOpen(o => !o)}
      >
        <Icon className={`w-4 h-4 shrink-0 ${di.color}`} />
        <div className="flex-1 min-w-0">
          <p className="text-xs font-mono text-zinc-400 truncate">
            {entry.obs?.post?.post_id ?? `step-${total - index}`}
          </p>
          <p className="text-[11px] text-zinc-600 capitalize">
            {entry.action.reason_code?.replace(/_/g, ' ')} · {entry.action.severity}
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <div className="text-right">
            <span className={`text-xs font-bold tabular-nums ${scoreColor(v)}`}>
              {(v * 100).toFixed(0)}%
            </span>
            <div className="h-1 w-12 bg-zinc-700 rounded-full mt-1 overflow-hidden">
              <div className={`h-full rounded-full ${scoreBg(v)}`} style={{ width: `${v * 100}%` }} />
            </div>
          </div>
          {(hasReasoning || hasNote) && (
            <ChevronDown className={`w-3.5 h-3.5 text-zinc-600 transition-transform ${open ? 'rotate-180' : ''}`} />
          )}
        </div>
      </button>

      {/* expanded detail */}
      {open && (
        <div className="border-t border-zinc-700/40 px-4 py-3 space-y-3">
          {hasReasoning && (
            <div>
              <div className="flex items-center gap-1.5 mb-1.5">
                <Bot className="w-3.5 h-3.5 text-indigo-400" />
                <span className="text-[11px] font-semibold text-indigo-400 uppercase tracking-wider">
                  {entry.model ?? 'AI'} Judge
                </span>
              </div>
              <p className="text-xs text-zinc-300 leading-relaxed">{entry.reasoning}</p>
            </div>
          )}
          {hasNote && (
            <div>
              <div className="flex items-center gap-1.5 mb-1.5">
                <MessageSquare className="w-3.5 h-3.5 text-sky-400" />
                <span className="text-[11px] font-semibold text-sky-400 uppercase tracking-wider">Your Note</span>
              </div>
              <p className="text-xs text-zinc-300 leading-relaxed">{entry.action.explanation}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function ScorePanel({ history, taskId, lastReward }) {
  const avgScore  = history.length
    ? history.reduce((s, h) => s + h.reward.value, 0) / history.length
    : 0

  const animScore = useAnimatedValue(avgScore)
  const maxSteps  = TASK_MAX[taskId] ?? 1
  const pct       = Math.round(animScore * 100)

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
          {history.length} / {maxSteps} steps · avg {animScore.toFixed(3)}
        </p>

        <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
          <div className={`h-full rounded-full score-fill ${scoreBg(animScore)}`} style={{ width: `${pct}%` }} />
        </div>
      </div>

      {/* Latest AI verdict — shown as soon as first step completes */}
      {history.length > 0 && history[history.length - 1].reasoning && (
        <div className="bg-indigo-950/40 border border-indigo-500/20 rounded-2xl p-5 animate-fade-in">
          <div className="flex items-center gap-2 mb-2">
            <Bot className="w-4 h-4 text-indigo-400" />
            <span className="text-xs font-semibold uppercase tracking-widest text-indigo-400">
              Latest AI Verdict
            </span>
            {history[history.length - 1].model && (
              <span className="ml-auto text-[10px] text-indigo-600 font-mono">
                {history[history.length - 1].model}
              </span>
            )}
          </div>
          <p className="text-sm text-zinc-300 leading-relaxed">
            {history[history.length - 1].reasoning}
          </p>
        </div>
      )}

      {/* Step history */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <p className="text-xs font-semibold uppercase tracking-widest text-zinc-500">Step History</p>
          {history.length > 0 && (
            <span className="text-[11px] text-zinc-600">click row to expand</span>
          )}
        </div>

        {history.length === 0 ? (
          <p className="text-zinc-600 text-sm text-center py-4">No steps yet</p>
        ) : (
          <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
            {[...history].reverse().map((h, i) => (
              <HistoryRow
                key={history.length - 1 - i}
                entry={h}
                index={i}
                total={history.length}
              />
            ))}
          </div>
        )}
      </div>

      {/* Score weights */}
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
                <div className="h-full bg-indigo-500/60 rounded-full score-fill" style={{ width: `${weight}%` }} />
              </div>
            </div>
          ))}
          {taskId === 'task3' && (
            <p className="text-[11px] text-zinc-600 pt-1">
              + 30% explanation quality (task3 only)
            </p>
          )}
        </div>
        <div className="mt-4 pt-4 border-t border-zinc-800 flex items-center gap-2">
          <Bot className="w-3.5 h-3.5 text-indigo-500" />
          <p className="text-[11px] text-zinc-500">Graded by gpt-4o-mini via OpenAI</p>
        </div>
      </div>
    </div>
  )
}
