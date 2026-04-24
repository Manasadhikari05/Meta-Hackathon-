import { useState, useEffect, useCallback } from 'react'
import { CheckCircle2, XCircle, AlertCircle, Send } from 'lucide-react'

const DECISIONS = [
  { id: 'approve',  label: 'Approve',  icon: CheckCircle2, key: 'A', color: 'emerald' },
  { id: 'remove',   label: 'Remove',   icon: XCircle,      key: 'R', color: 'rose' },
  { id: 'escalate', label: 'Escalate', icon: AlertCircle,  key: 'E', color: 'amber' },
]

const REASONS = [
  { id: 'clean',         label: 'Clean' },
  { id: 'spam',          label: 'Spam' },
  { id: 'harassment',    label: 'Harassment' },
  { id: 'hate_speech',   label: 'Hate Speech' },
  { id: 'misinformation',label: 'Misinfo' },
  { id: 'violence',      label: 'Violence' },
  { id: 'self_harm',     label: 'Self Harm' },
  { id: 'sexual_content',label: 'Sexual' },
]

const SEVERITIES = ['low', 'medium', 'high']

const DECISION_COLORS = {
  emerald: {
    active:   'bg-emerald-500 border-emerald-500 text-white shadow-[0_0_20px_rgba(16,185,129,.35)]',
    inactive: 'bg-zinc-800/60 border-zinc-700 text-zinc-400 hover:border-emerald-500/60 hover:text-emerald-400',
  },
  rose: {
    active:   'bg-rose-500 border-rose-500 text-white shadow-[0_0_20px_rgba(244,63,94,.35)]',
    inactive: 'bg-zinc-800/60 border-zinc-700 text-zinc-400 hover:border-rose-500/60 hover:text-rose-400',
  },
  amber: {
    active:   'bg-amber-500 border-amber-500 text-white shadow-[0_0_20px_rgba(245,158,11,.35)]',
    inactive: 'bg-zinc-800/60 border-zinc-700 text-zinc-400 hover:border-amber-500/60 hover:text-amber-400',
  },
}

const SEV_COLORS = {
  low:    { active: 'bg-sky-500 border-sky-500 text-white', inactive: 'bg-zinc-800/60 border-zinc-700 text-zinc-400 hover:border-sky-500/50' },
  medium: { active: 'bg-amber-500 border-amber-500 text-white', inactive: 'bg-zinc-800/60 border-zinc-700 text-zinc-400 hover:border-amber-500/50' },
  high:   { active: 'bg-rose-500 border-rose-500 text-white', inactive: 'bg-zinc-800/60 border-zinc-700 text-zinc-400 hover:border-rose-500/50' },
}

const DEFAULT_FORM = {
  decision: null,
  reason_code: null,
  severity: null,
  confidence: 0.8,
  explanation: '',
}

export default function ActionForm({ onSubmit, loading, taskId, disabled }) {
  const [form, setForm] = useState(DEFAULT_FORM)

  const needsExplanation = taskId === 'task3'

  const isValid = form.decision && form.reason_code && form.severity &&
    (!needsExplanation || form.explanation.trim().length > 0)

  const set = (key, val) => setForm(f => ({ ...f, [key]: val }))

  const handleSubmit = () => {
    if (!isValid || loading || disabled) return
    onSubmit({
      decision: form.decision,
      reason_code: form.reason_code,
      severity: form.severity,
      confidence: form.confidence,
      explanation: form.explanation || undefined,
    })
    setForm(DEFAULT_FORM)
  }

  // keyboard shortcuts
  const onKey = useCallback((e) => {
    if (disabled || loading) return
    if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT') return
    if (e.key === 'a' || e.key === 'A') set('decision', 'approve')
    if (e.key === 'r' || e.key === 'R') set('decision', 'remove')
    if (e.key === 'e' || e.key === 'E') set('decision', 'escalate')
    if (e.key === 'Enter' && isValid) handleSubmit()
  }, [disabled, loading, isValid, form]) // eslint-disable-line

  useEffect(() => {
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onKey])

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 space-y-6">
      <p className="text-xs font-semibold uppercase tracking-widest text-zinc-500">Your Decision</p>

      {/* Decision buttons */}
      <div className="grid grid-cols-3 gap-3">
        {DECISIONS.map(({ id, label, icon: Icon, key, color }) => {
          const active = form.decision === id
          const cls = DECISION_COLORS[color]
          return (
            <button
              key={id}
              disabled={disabled}
              onClick={() => set('decision', id)}
              className={`
                relative flex flex-col items-center gap-2 py-4 rounded-xl border
                font-semibold text-sm transition-all duration-200 disabled:opacity-40
                ${active ? cls.active : cls.inactive}
              `}
            >
              <Icon className="w-5 h-5" />
              {label}
              <span className="absolute top-2 right-2 text-[10px] opacity-40 font-mono">{key}</span>
            </button>
          )
        })}
      </div>

      {/* Reason code */}
      <div>
        <p className="text-xs text-zinc-500 mb-2.5">Reason Code</p>
        <div className="grid grid-cols-4 gap-2">
          {REASONS.map(r => (
            <button
              key={r.id}
              disabled={disabled}
              onClick={() => set('reason_code', r.id)}
              className={`
                py-1.5 px-2 rounded-lg border text-xs font-medium transition-all duration-150
                disabled:opacity-40
                ${form.reason_code === r.id
                  ? 'bg-indigo-600 border-indigo-500 text-white'
                  : 'bg-zinc-800/60 border-zinc-700 text-zinc-400 hover:border-indigo-500/50 hover:text-indigo-300'
                }
              `}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      {/* Severity */}
      <div>
        <p className="text-xs text-zinc-500 mb-2.5">Severity</p>
        <div className="flex gap-2">
          {SEVERITIES.map(s => {
            const cls = SEV_COLORS[s]
            return (
              <button
                key={s}
                disabled={disabled}
                onClick={() => set('severity', s)}
                className={`
                  flex-1 py-2 rounded-xl border text-xs font-semibold capitalize
                  transition-all duration-150 disabled:opacity-40
                  ${form.severity === s ? cls.active : cls.inactive}
                `}
              >
                {s}
              </button>
            )
          })}
        </div>
      </div>

      {/* Confidence slider */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <p className="text-xs text-zinc-500">Confidence</p>
          <span className="text-xs font-mono font-semibold text-indigo-400">
            {form.confidence.toFixed(2)}
          </span>
        </div>
        <input
          type="range"
          min="0" max="1" step="0.01"
          value={form.confidence}
          disabled={disabled}
          onChange={e => set('confidence', parseFloat(e.target.value))}
          className="w-full h-1.5 rounded-full accent-indigo-500 bg-zinc-700 cursor-pointer disabled:opacity-40"
        />
        <div className="flex justify-between mt-1 text-[10px] text-zinc-600">
          <span>0.00</span><span>0.50</span><span>1.00</span>
        </div>
      </div>

      {/* Explanation — task3 only */}
      {needsExplanation && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs text-zinc-500">Explanation</p>
            <span className="text-[10px] text-rose-400 font-semibold">Required for task3</span>
          </div>
          <textarea
            rows={2}
            disabled={disabled}
            value={form.explanation}
            onChange={e => set('explanation', e.target.value)}
            placeholder="One sentence explaining your decision…"
            className="
              w-full bg-zinc-800/60 border border-zinc-700 rounded-xl px-4 py-3
              text-sm text-zinc-200 placeholder-zinc-600 resize-none
              focus:outline-none focus:border-indigo-500 transition-colors
              disabled:opacity-40
            "
          />
        </div>
      )}

      {/* Submit */}
      <button
        disabled={!isValid || loading || disabled}
        onClick={handleSubmit}
        className="
          w-full flex items-center justify-center gap-2 py-3.5 rounded-xl
          bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700
          text-white font-semibold text-sm
          transition-all duration-200
          disabled:opacity-35 disabled:cursor-not-allowed
          shadow-[0_0_20px_rgba(99,102,241,.2)] hover:shadow-[0_0_28px_rgba(99,102,241,.4)]
        "
      >
        {loading
          ? <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Submitting…</>
          : <><Send className="w-4 h-4" />Submit Decision</>
        }
      </button>

      {/* keyboard hint */}
      <p className="text-center text-[11px] text-zinc-700">
        Shortcuts: <kbd className="font-mono">A</kbd> Approve · <kbd className="font-mono">R</kbd> Remove · <kbd className="font-mono">E</kbd> Escalate · <kbd className="font-mono">↵</kbd> Submit
      </p>
    </div>
  )
}
