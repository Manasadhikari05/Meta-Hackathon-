import { useCallback, useMemo, useRef, useState } from 'react'
import {
  ChevronLeft,
  Image as ImageIcon,
  UploadCloud,
  ScanText,
  Trash2,
  ThumbsUp,
  Flag,
  ShieldAlert,
  Loader2,
  X,
} from 'lucide-react'

/** Public FastAPI base set at build time. Otherwise we use Vite's /api proxy. */
function deployedBackendBase() {
  const raw = (import.meta.env.VITE_BACKEND_URL || '').trim().replace(/\/$/, '')
  return raw || null
}

function moderateUrl() {
  const base = deployedBackendBase()
  return base ? `${base}/ocr/moderate` : '/api/ocr/moderate'
}

const TAG_STYLES = {
  'Hate speech': 'bg-rose-100 text-rose-800 border-rose-200',
  Threatening: 'bg-rose-100 text-rose-800 border-rose-200',
  Bullying: 'bg-rose-100 text-rose-800 border-rose-200',
  Harassment: 'bg-rose-100 text-rose-800 border-rose-200',
  Abusive: 'bg-rose-100 text-rose-800 border-rose-200',
  Toxic: 'bg-amber-100 text-amber-900 border-amber-200',
  Offensive: 'bg-amber-100 text-amber-900 border-amber-200',
  Aggressive: 'bg-amber-100 text-amber-900 border-amber-200',
  Angry: 'bg-amber-100 text-amber-900 border-amber-200',
  Harsh: 'bg-amber-100 text-amber-900 border-amber-200',
  Sarcastic: 'bg-violet-100 text-violet-800 border-violet-200',
  'Passive-aggressive': 'bg-violet-100 text-violet-800 border-violet-200',
  Frustrated: 'bg-blue-100 text-blue-800 border-blue-200',
  Critical: 'bg-blue-100 text-blue-800 border-blue-200',
  Negative: 'bg-slate-100 text-slate-800 border-slate-200',
  Neutral: 'bg-slate-100 text-slate-700 border-slate-200',
  Polite: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  Friendly: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  Positive: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  Supportive: 'bg-emerald-100 text-emerald-800 border-emerald-200',
}

const DECISION_STYLES = {
  approve: { label: 'APPROVE', className: 'bg-emerald-100 text-emerald-800 border-emerald-200', Icon: ThumbsUp },
  remove: { label: 'REMOVE', className: 'bg-rose-100 text-rose-800 border-rose-200', Icon: Trash2 },
  escalate: { label: 'ESCALATE', className: 'bg-amber-100 text-amber-900 border-amber-200', Icon: Flag },
}

const SEVERITY_STYLES = {
  low: 'bg-slate-100 text-slate-700 border-slate-200',
  medium: 'bg-amber-100 text-amber-900 border-amber-200',
  high: 'bg-rose-100 text-rose-800 border-rose-200',
}

function TagPill({ tag }) {
  const s = TAG_STYLES[tag] || 'bg-slate-100 text-slate-700 border-slate-200'
  return (
    <span className={`inline-flex items-center text-xs font-semibold px-2.5 py-1 rounded-md border ${s}`}>
      {tag}
    </span>
  )
}

function DecisionPill({ decision }) {
  const cfg = DECISION_STYLES[decision] || {
    label: (decision || '—').toUpperCase(),
    className: 'bg-slate-100 text-slate-800 border-slate-200',
    Icon: null,
  }
  const { Icon } = cfg
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-md border ${cfg.className}`}>
      {Icon ? <Icon className="w-3.5 h-3.5" /> : null}
      {cfg.label}
    </span>
  )
}

function SeverityPill({ severity }) {
  const s = SEVERITY_STYLES[severity] || SEVERITY_STYLES.low
  return (
    <span className={`inline-flex items-center text-[11px] uppercase tracking-wide font-semibold px-2 py-0.5 rounded border ${s}`}>
      {severity || 'low'}
    </span>
  )
}

function ResultCard({ entry }) {
  const { previewUrl, file, result, error } = entry
  const moderation = result?.moderation || {}
  const decision = moderation.decision
  const tag = moderation.tag || '—'
  const severity = moderation.severity
  const reason = moderation.reason_code
  const explanation = moderation.explanation
  const text = result?.extracted_text || ''
  const engine = result?.ocr_engine || 'pending'
  const conf = typeof moderation.confidence === 'number' ? moderation.confidence : null

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="grid grid-cols-1 md:grid-cols-[260px_1fr]">
        <div className="bg-slate-100 flex items-center justify-center md:border-r md:border-slate-200 max-h-72 md:max-h-none overflow-hidden">
          {previewUrl ? (
            <img src={previewUrl} alt={file?.name || 'meme'} className="w-full h-full object-contain max-h-72 md:max-h-[18rem]" />
          ) : (
            <div className="text-slate-400 text-sm flex flex-col items-center gap-1 py-12">
              <ImageIcon className="w-6 h-6" />
              no preview
            </div>
          )}
        </div>
        <div className="p-5 flex flex-col gap-3">
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <div className="flex items-center gap-2 flex-wrap">
              <DecisionPill decision={decision} />
              <SeverityPill severity={severity} />
              <TagPill tag={tag} />
            </div>
            <div className="text-[11px] uppercase tracking-wide text-slate-500">
              OCR: <span className="font-semibold text-slate-700">{engine}</span>
              {conf != null && (
                <>
                  {' '}· conf{' '}
                  <span className="font-semibold text-slate-700">{conf.toFixed(2)}</span>
                </>
              )}
            </div>
          </div>

          <div>
            <div className="text-[11px] uppercase tracking-wide text-slate-500 mb-1">Extracted text</div>
            {error ? (
              <div className="text-sm text-rose-700 bg-rose-50 border border-rose-200 rounded-md p-2.5">
                {error}
              </div>
            ) : text ? (
              <pre className="text-sm text-slate-800 bg-slate-50 border border-slate-200 rounded-md p-2.5 whitespace-pre-wrap break-words max-h-40 overflow-auto">
                {text}
              </pre>
            ) : (
              <div className="text-sm text-slate-400 italic">No readable text in image.</div>
            )}
          </div>

          {explanation && (
            <div>
              <div className="text-[11px] uppercase tracking-wide text-slate-500 mb-1">Why</div>
              <div className="text-sm text-slate-700">{explanation}</div>
            </div>
          )}

          <div className="text-[11px] text-slate-500 mt-auto flex flex-wrap gap-x-4 gap-y-1">
            {file?.name && <span>file: <span className="text-slate-700">{file.name}</span></span>}
            {reason && <span>reason: <span className="text-slate-700">{reason}</span></span>}
            {moderation.classifier_source && (
              <span>core: <span className="text-slate-700">{moderation.classifier_source}</span></span>
            )}
            {moderation.model && <span>model: <span className="text-slate-700">{moderation.model}</span></span>}
          </div>
        </div>
      </div>
    </div>
  )
}

export default function MemeMod({ onBack }) {
  const inputRef = useRef(null)
  const [entries, setEntries] = useState([])
  const [busy, setBusy] = useState(false)
  const [dragOver, setDragOver] = useState(false)

  const accepted = useMemo(() => ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'], [])

  const sendOne = useCallback(async (file) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
    const previewUrl = URL.createObjectURL(file)
    const placeholder = { id, file, previewUrl, status: 'uploading', result: null, error: null }
    setEntries((prev) => [placeholder, ...prev])

    const fd = new FormData()
    fd.append('image', file, file.name)
    try {
      const res = await fetch(moderateUrl(), { method: 'POST', body: fd })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        const msg = (data && (data.detail || data.error)) || `HTTP ${res.status}`
        setEntries((prev) =>
          prev.map((e) => (e.id === id ? { ...e, status: 'error', error: msg } : e)),
        )
        return
      }
      setEntries((prev) =>
        prev.map((e) => (e.id === id ? { ...e, status: 'done', result: data, error: null } : e)),
      )
    } catch (exc) {
      setEntries((prev) =>
        prev.map((e) =>
          e.id === id
            ? { ...e, status: 'error', error: `Network error: ${exc.message || exc}` }
            : e,
        ),
      )
    }
  }, [])

  const onFiles = useCallback(
    async (fileList) => {
      const arr = Array.from(fileList || []).filter((f) => accepted.includes(f.type))
      if (arr.length === 0) return
      setBusy(true)
      try {
        for (const f of arr) {
          // Sequential keeps the UI ordered and avoids overwhelming a CPU OCR.
          // eslint-disable-next-line no-await-in-loop
          await sendOne(f)
        }
      } finally {
        setBusy(false)
      }
    },
    [accepted, sendOne],
  )

  const onPick = () => inputRef.current?.click()
  const onChange = (ev) => {
    onFiles(ev.target.files)
    ev.target.value = ''
  }
  const onDrop = (ev) => {
    ev.preventDefault()
    setDragOver(false)
    onFiles(ev.dataTransfer?.files)
  }
  const onDragOver = (ev) => {
    ev.preventDefault()
    setDragOver(true)
  }
  const onDragLeave = () => setDragOver(false)

  const clearOne = (id) =>
    setEntries((prev) => {
      const e = prev.find((x) => x.id === id)
      if (e?.previewUrl) URL.revokeObjectURL(e.previewUrl)
      return prev.filter((x) => x.id !== id)
    })

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <header className="sticky top-0 z-40 bg-white/80 backdrop-blur-md border-b border-slate-100">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between gap-3">
          <button
            onClick={onBack}
            className="flex items-center gap-1.5 text-sm text-slate-600 hover:text-slate-900 transition"
          >
            <ChevronLeft className="w-4 h-4" /> Back
          </button>
          <div className="flex items-center gap-2 text-slate-900 font-semibold">
            <ShieldAlert className="w-5 h-5 text-violet-600" />
            JPEG / PNG Meme Moderation
          </div>
          <div className="hidden md:flex items-center gap-2 text-xs text-slate-500">
            <ScanText className="w-4 h-4" />
            OCR → core (Qwen RL + guardrail) → tag · decision · severity
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-10">
        <div
          onDrop={onDrop}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onClick={onPick}
          className={`cursor-pointer rounded-2xl border-2 border-dashed p-10 text-center transition ${
            dragOver
              ? 'border-violet-500 bg-violet-50'
              : 'border-slate-300 bg-white hover:border-violet-400 hover:bg-violet-50/40'
          }`}
        >
          <div className="flex flex-col items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-violet-100 text-violet-700 flex items-center justify-center">
              {busy ? (
                <Loader2 className="w-6 h-6 animate-spin" />
              ) : (
                <UploadCloud className="w-6 h-6" />
              )}
            </div>
            <div className="text-slate-900 font-semibold">
              {busy ? 'Processing…' : 'Drop a meme here, or click to choose JPEG/PNG/WebP'}
            </div>
            <div className="text-sm text-slate-500 max-w-md">
              Up to 8 MB. EasyOCR extracts the text, then the project core (Qwen RL + heuristic
              guardrail) decides <span className="font-semibold">approve / remove / escalate</span>{' '}
              and tags the message (e.g. Sarcastic, Threatening, Friendly).
            </div>
            <input
              ref={inputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              multiple
              hidden
              onChange={onChange}
            />
          </div>
        </div>

        <div className="mt-8 space-y-5">
          {entries.length === 0 && (
            <div className="text-center text-slate-400 text-sm">
              No memes uploaded yet. Try a screenshot of a comment, a meme caption, or a sticker.
            </div>
          )}
          {entries.map((entry) => (
            <div key={entry.id} className="relative">
              {entry.status === 'uploading' && (
                <div className="absolute inset-0 z-10 bg-white/70 backdrop-blur-[1px] rounded-2xl flex items-center justify-center pointer-events-none">
                  <div className="flex items-center gap-2 text-violet-700 text-sm font-semibold">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Running OCR + core…
                  </div>
                </div>
              )}
              <button
                type="button"
                onClick={() => clearOne(entry.id)}
                className="absolute -top-2 -right-2 z-20 bg-white border border-slate-200 rounded-full p-1 shadow hover:bg-slate-50"
                title="Remove from list"
              >
                <X className="w-4 h-4 text-slate-500" />
              </button>
              <ResultCard entry={entry} />
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}
