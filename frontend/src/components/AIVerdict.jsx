import { CheckCircle2, XCircle, AlertCircle, Bot } from 'lucide-react'

const CONFIG = {
  approve: {
    label:  'APPROVED',
    Icon:   CheckCircle2,
    ring:   'border-emerald-500/40',
    glow:   'shadow-[0_0_40px_rgba(16,185,129,.18)]',
    badge:  'bg-emerald-500 text-white',
    text:   'text-emerald-400',
    bar:    'bg-emerald-500',
    dim:    'bg-emerald-500/10',
  },
  remove: {
    label:  'REMOVED',
    Icon:   XCircle,
    ring:   'border-rose-500/40',
    glow:   'shadow-[0_0_40px_rgba(244,63,94,.18)]',
    badge:  'bg-rose-500 text-white',
    text:   'text-rose-400',
    bar:    'bg-rose-500',
    dim:    'bg-rose-500/10',
  },
  escalate: {
    label:  'ESCALATED',
    Icon:   AlertCircle,
    ring:   'border-amber-500/40',
    glow:   'shadow-[0_0_40px_rgba(245,158,11,.18)]',
    badge:  'bg-amber-500 text-white',
    text:   'text-amber-400',
    bar:    'bg-amber-500',
    dim:    'bg-amber-500/10',
  },
}

const SEVERITY_COLOR = {
  low:    'bg-sky-500/10 text-sky-400 border-sky-500/20',
  medium: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  high:   'bg-rose-500/10 text-rose-400 border-rose-500/20',
}

const REASON_LABEL = {
  clean:          'Clean',
  spam:           'Spam',
  hate_speech:    'Hate Speech',
  harassment:     'Harassment',
  misinformation: 'Misinformation',
  self_harm:      'Self Harm',
  violence:       'Violence',
  sexual_content: 'Sexual Content',
}

export default function AIVerdict({ verdict }) {
  if (!verdict) return null
  const { decision, reason_code, severity, confidence, explanation, model } = verdict
  const c = CONFIG[decision] ?? CONFIG.escalate

  return (
    <div className={`rounded-2xl border ${c.ring} ${c.glow} ${c.dim} p-6 animate-slide-up`}>
      {/* model tag */}
      <div className="flex items-center gap-1.5 mb-5">
        <Bot className="w-3.5 h-3.5 text-zinc-500" />
        <span className="text-[11px] text-zinc-500 font-mono">{model ?? 'llama3.2'}</span>
      </div>

      {/* big decision badge */}
      <div className="flex items-center gap-3 mb-6">
        <span className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold tracking-wide ${c.badge}`}>
          <c.Icon className="w-4 h-4" />
          {c.label}
        </span>
      </div>

      {/* reason + severity row */}
      <div className="flex flex-wrap gap-2 mb-5">
        <span className="bg-zinc-800 border border-zinc-700 text-zinc-300 text-xs font-medium px-3 py-1 rounded-lg">
          {REASON_LABEL[reason_code] ?? reason_code}
        </span>
        <span className={`text-xs font-semibold px-3 py-1 rounded-lg border capitalize ${SEVERITY_COLOR[severity] ?? SEVERITY_COLOR.medium}`}>
          {severity} severity
        </span>
      </div>

      {/* confidence bar */}
      <div className="mb-5">
        <div className="flex justify-between text-xs mb-1.5">
          <span className="text-zinc-500">Confidence</span>
          <span className={`font-bold tabular-nums ${c.text}`}>{Math.round(confidence * 100)}%</span>
        </div>
        <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full score-fill ${c.bar}`}
            style={{ width: `${confidence * 100}%` }}
          />
        </div>
      </div>

      {/* explanation */}
      {explanation && (
        <div className="border-t border-zinc-700/50 pt-4">
          <p className="text-xs text-zinc-500 mb-1">AI Reasoning</p>
          <p className="text-sm text-zinc-200 leading-relaxed">"{explanation}"</p>
        </div>
      )}
    </div>
  )
}
