import { useState, useCallback, useEffect, useRef } from 'react'
import { Shield, ChevronLeft, Sparkles, RotateCcw, CheckCircle2, XCircle, AlertCircle, ChevronDown, Bot, Star, Brain, Zap, Eye, Shield as ShieldIcon, AlertTriangle, CheckSquare } from 'lucide-react'
import { api } from '../api/client'
import AIVerdict from './AIVerdict'
import RatingWidget from './RatingWidget'

const PLATFORMS = [
  { id: 'social_media',     label: 'Social Media' },
  { id: 'community_forum',  label: 'Community Forum' },
  { id: 'marketplace',      label: 'Marketplace' },
  { id: 'messaging',        label: 'Messaging App' },
  { id: 'news_comments',    label: 'News Comments' },
]

const DEC_ICON  = { approve: CheckCircle2, remove: XCircle, escalate: AlertCircle }
const DEC_COLOR = {
  approve:  'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
  remove:   'text-rose-400 bg-rose-500/10 border-rose-500/30',
  escalate: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
}
const RATING_COLOR = (r) => r >= 8 ? 'text-emerald-400' : r >= 5 ? 'text-amber-400' : 'text-rose-400'

// Thinking steps configuration for the AI analysis animation
const THINKING_STEPS = [
  { icon: Brain, text: 'Analyzing content intent...', delay: 800 },
  { icon: Eye, text: 'Scanning for policy violations...', delay: 1200 },
  { icon: ShieldIcon, text: 'Evaluating tone and context...', delay: 1500 },
  { icon: AlertTriangle, text: 'Assessing severity level...', delay: 1000 },
  { icon: CheckSquare, text: 'Finalizing moderation decision...', delay: 800 },
]

function ThinkingAnimation({ currentStep, isComplete }) {
  return (
    <div className="space-y-3">
      {THINKING_STEPS.map((step, index) => {
        const Icon = step.icon
        const isActive = index === currentStep
        const isCompleted = index < currentStep

        return (
          <div
            key={index}
            className={`flex items-center gap-3 p-3 rounded-xl transition-all duration-500 ${
              isActive
                ? 'bg-indigo-500/10 border border-indigo-500/30 text-indigo-300'
                : isCompleted
                ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
                : 'bg-zinc-800/50 border border-zinc-700/50 text-zinc-600'
            }`}
          >
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
              isActive ? 'bg-indigo-500/20' : isCompleted ? 'bg-emerald-500/20' : 'bg-zinc-700/50'
            }`}>
              {isCompleted ? (
                <CheckSquare className="w-4 h-4" />
              ) : (
                <Icon className={`w-4 h-4 ${isActive ? 'animate-pulse' : ''}`} />
              )}
            </div>
            <span className={`text-sm ${isActive ? 'font-medium' : ''}`}>
              {step.text}
            </span>
            {isActive && (
              <div className="ml-auto w-5 h-5 border-2 border-indigo-400/30 border-t-indigo-400 rounded-full animate-spin" />
            )}
          </div>
        )
      })}
    </div>
  )
}

function HistoryItem({ item }) {
  const [open, setOpen] = useState(false)
  const Icon = DEC_ICON[item.decision] ?? AlertCircle

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
      <button
        className="w-full flex items-start gap-3 p-4 text-left hover:bg-zinc-800/40 transition-colors"
        onClick={() => setOpen(o => !o)}
      >
        <Icon className={`w-4 h-4 mt-0.5 shrink-0 ${DEC_COLOR[item.decision]?.split(' ')[0]}`} />
        <div className="flex-1 min-w-0">
          <p className="text-sm text-zinc-200 truncate">"{item.content}"</p>
          <p className="text-xs text-zinc-500 mt-0.5 capitalize">
            {item.platform?.replace(/_/g, ' ')} · {item.reason_code?.replace(/_/g, ' ')} · {item.severity}
          </p>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <span className={`text-sm font-bold tabular-nums ${RATING_COLOR(item.rating)}`}>
            {item.rating}/10
          </span>
          <span className={`text-xs font-semibold px-2 py-0.5 rounded-lg border capitalize ${DEC_COLOR[item.decision]}`}>
            {item.decision}
          </span>
          <ChevronDown className={`w-3.5 h-3.5 text-zinc-600 transition-transform ${open ? 'rotate-180' : ''}`} />
        </div>
      </button>

      {open && (
        <div className="border-t border-zinc-800 px-4 py-3 space-y-2 animate-fade-in">
          <p className="text-xs text-zinc-400 leading-relaxed">
            <span className="text-zinc-600">AI: </span>"{item.explanation}"
          </p>
          {item.comment && (
            <p className="text-xs text-zinc-400">
              <span className="text-zinc-600">Your comment: </span>"{item.comment}"
            </p>
          )}
          <p className="text-[11px] text-zinc-600 font-mono">{item.model} · {item.post_id}</p>
        </div>
      )}
    </div>
  )
}

// phase: 'input' | 'loading' | 'thinking' | 'verdict' | 'submitting' | 'rated'
export default function Moderator({ onBack }) {
  const [phase,    setPhase]    = useState('input')
  const [content,  setContent]  = useState('')
  const [platform, setPlatform] = useState('social_media')
  const [verdict,  setVerdict]  = useState(null)
  const [history,  setHistory]  = useState([])
  const [error,    setError]    = useState(null)
  const [lastRating, setLastRating] = useState(null)
  const [thinkingStep, setThinkingStep] = useState(0)
  const thinkingIntervalRef = useRef(null)

  const handleModerate = useCallback(async () => {
    if (!content.trim()) return
    setPhase('loading')
    setThinkingStep(0)
    setError(null)

    // Start thinking animation after a brief delay
    setTimeout(() => {
      setPhase('thinking')
    }, 500)

    try {
      const result = await api.moderate(content.trim(), platform)
      setVerdict(result)
      setPhase('verdict')
    } catch (e) {
      setError(e.message)
      setPhase('input')
    }
  }, [content, platform])

  const handleFeedback = useCallback(async (rating, comment) => {
    setPhase('submitting')
    try {
      await api.feedback({ ...verdict, rating, comment: comment || null })
      const entry = { ...verdict, rating, comment }
      setHistory(h => [entry, ...h])
      setLastRating(rating)
      setPhase('rated')
    } catch (e) {
      setError(e.message)
      setPhase('verdict')
    }
  }, [verdict])

  const reset = () => {
    setPhase('input')
    setContent('')
    setVerdict(null)
    setLastRating(null)
    setError(null)
    setThinkingStep(0)
    if (thinkingIntervalRef.current) {
      clearInterval(thinkingIntervalRef.current)
      thinkingIntervalRef.current = null
    }
  }

  // Thinking steps progression
  useEffect(() => {
    if (phase === 'thinking') {
      let currentStep = 0
      setThinkingStep(0)

      thinkingIntervalRef.current = setInterval(() => {
        currentStep += 1
        setThinkingStep(currentStep)

        if (currentStep >= THINKING_STEPS.length - 1) {
          clearInterval(thinkingIntervalRef.current)
          thinkingIntervalRef.current = null
        }
      }, 800) // Change step every 800ms
    }

    return () => {
      if (thinkingIntervalRef.current) {
        clearInterval(thinkingIntervalRef.current)
        thinkingIntervalRef.current = null
      }
    }
  }, [phase])

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-30 bg-zinc-950/80 backdrop-blur border-b border-zinc-800/60">
        <div className="max-w-5xl mx-auto px-6 h-14 flex items-center gap-3">
          <Shield className="w-5 h-5 text-indigo-400" strokeWidth={1.5} />
          <span className="font-bold text-zinc-100 text-sm">ModGuard</span>
          <span className="text-zinc-700">/</span>
          <span className="text-zinc-400 text-sm">AI Moderator</span>
          <div className="flex items-center gap-1.5 ml-3">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs text-zinc-600">GPT live</span>
          </div>
          <button
            onClick={onBack}
            className="ml-auto flex items-center gap-1 text-xs text-zinc-500 hover:text-zinc-300 transition"
          >
            <ChevronLeft className="w-3.5 h-3.5" /> Home
          </button>
        </div>
      </header>

      <main className="flex-1 max-w-5xl mx-auto w-full px-6 py-10">
        {error && (
          <div className="mb-6 bg-rose-500/10 border border-rose-500/30 text-rose-400 rounded-xl px-4 py-3 text-sm animate-fade-in flex items-center justify-between">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="text-rose-500 text-lg leading-none ml-4">×</button>
          </div>
        )}

        {/* ── Input phase ───────────────────────────────── */}
        {phase === 'input' && (
          <div className="max-w-2xl mx-auto animate-slide-up">
            <div className="text-center mb-10">
              <p className="text-xs font-semibold tracking-[.2em] text-zinc-500 uppercase mb-3">AI Moderation</p>
              <h1 className="text-3xl font-bold text-zinc-100 mb-3">Write anything.</h1>
              <p className="text-zinc-400">
                The AI will moderate it — approve, remove, or escalate — then you rate how well it did.
              </p>
            </div>

            <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 space-y-4">
              <textarea
                rows={5}
                value={content}
                onChange={e => setContent(e.target.value)}
                placeholder="Type a social media post, comment, or message…"
                disabled={phase === 'loading' || phase === 'thinking'}
                className="
                  w-full bg-zinc-800/50 border border-zinc-700 rounded-xl px-4 py-3
                  text-sm text-zinc-200 placeholder-zinc-600 resize-none
                  focus:outline-none focus:border-indigo-500 transition-colors
                  disabled:opacity-40
                "
              />

              <div className="flex items-center gap-3">
                <select
                  value={platform}
                  onChange={e => setPlatform(e.target.value)}
                  disabled={phase === 'loading' || phase === 'thinking'}
                  className="
                    flex-1 bg-zinc-800/60 border border-zinc-700 rounded-xl px-3 py-2.5
                    text-sm text-zinc-300 focus:outline-none focus:border-indigo-500
                    transition-colors disabled:opacity-40
                  "
                >
                  {PLATFORMS.map(p => (
                    <option key={p.id} value={p.id}>{p.label}</option>
                  ))}
                </select>

                <button
                  onClick={handleModerate}
                  disabled={!content.trim() || phase === 'loading' || phase === 'thinking'}
                  className="
                    flex items-center gap-2 px-6 py-2.5 rounded-xl
                    bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm
                    transition-all duration-200 disabled:opacity-35 disabled:cursor-not-allowed
                    shadow-[0_0_20px_rgba(99,102,241,.25)]
                  "
                >
                  {(phase === 'loading' || phase === 'thinking') ? (
                    <>
                      <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    <><Sparkles className="w-4 h-4" /> Moderate</>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ── Loading phase ─────────────────────────────── */}
        {phase === 'loading' && (
          <div className="max-w-2xl mx-auto animate-slide-up text-center">
            <div className="flex flex-col items-center justify-center py-20">
              <div className="w-16 h-16 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin mb-6" />
              <p className="text-zinc-400 text-sm">Initializing AI analysis...</p>
            </div>
          </div>
        )}

        {/* ── Thinking phase ────────────────────────────── */}
        {phase === 'thinking' && (
          <div className="max-w-2xl mx-auto animate-slide-up">
            <div className="text-center mb-8">
              <p className="text-xs font-semibold tracking-[.2em] text-zinc-500 uppercase mb-3">AI Analysis in Progress</p>
              <h2 className="text-2xl font-bold text-zinc-100 mb-2">Thinking through your content</h2>
              <p className="text-zinc-400 text-sm">Watch the AI analyze step by step</p>
            </div>

            <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
              <ThinkingAnimation currentStep={thinkingStep} isComplete={false} />
            </div>

            <div className="mt-6 text-center">
              <div className="inline-flex items-center gap-2 text-xs text-zinc-500">
                <div className="w-2 h-2 bg-indigo-500 rounded-full animate-pulse" />
                Processing with GPT-4o
              </div>
            </div>
          </div>
        )}

        {/* ── Verdict + rating phase ────────────────────── */}
        {(phase === 'verdict' || phase === 'submitting') && verdict && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-slide-up">
            {/* Left — the post */}
            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-zinc-500 mb-3">Your Content</p>
              <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 mb-4">
                <p className="text-zinc-200 text-sm leading-relaxed whitespace-pre-wrap">"{verdict.content}"</p>
                <div className="mt-3 pt-3 border-t border-zinc-800 flex items-center gap-2">
                  <span className="text-xs text-zinc-600">Platform:</span>
                  <span className="text-xs text-zinc-400 capitalize">{verdict.platform?.replace(/_/g, ' ')}</span>
                </div>
              </div>
              <button
                onClick={reset}
                className="flex items-center gap-1.5 text-xs text-zinc-600 hover:text-zinc-400 transition"
              >
                <RotateCcw className="w-3.5 h-3.5" /> Try different content
              </button>
            </div>

            {/* Right — AI verdict + rating */}
            <div className="space-y-5">
              <div>
                <p className="text-xs font-semibold uppercase tracking-widest text-zinc-500 mb-3">AI Verdict</p>
                <AIVerdict verdict={verdict} />
              </div>
              <div>
                <RatingWidget
                  decision={verdict.decision}
                  onSubmit={handleFeedback}
                  loading={phase === 'submitting'}
                />
              </div>
            </div>
          </div>
        )}

        {/* ── Rated confirmation ────────────────────────── */}
        {phase === 'rated' && (
          <div className="max-w-md mx-auto text-center animate-slide-up">
            <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-10 mb-6">
              <Star className="w-10 h-10 mx-auto mb-4 text-indigo-400" />
              <p className="text-4xl font-black text-zinc-100 mb-1">{lastRating}<span className="text-xl font-normal text-zinc-500">/10</span></p>
              <p className="text-zinc-400 text-sm">You rated the AI's decision</p>
            </div>
            <button
              onClick={reset}
              className="
                w-full flex items-center justify-center gap-2 py-3.5 rounded-xl
                bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm
                transition-all duration-200
              "
            >
              <Sparkles className="w-4 h-4" /> Moderate another post
            </button>
          </div>
        )}

        {/* ── History ───────────────────────────────────── */}
        {history.length > 0 && (
          <div className="mt-12">
            <div className="flex items-center gap-3 mb-4">
              <p className="text-xs font-semibold uppercase tracking-widest text-zinc-500">Session History</p>
              <span className="text-xs text-zinc-700">{history.length} item{history.length > 1 ? 's' : ''}</span>
              <div className="flex-1 h-px bg-zinc-800" />
              <div className="flex items-center gap-1.5">
                <Bot className="w-3.5 h-3.5 text-zinc-600" />
                <span className="text-[11px] text-zinc-600">graded by {history.model ?? 'GPT'}</span>
              </div>
            </div>
            <div className="space-y-2">
              {history.map((item, i) => (
                <HistoryItem key={i} item={item} />
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
