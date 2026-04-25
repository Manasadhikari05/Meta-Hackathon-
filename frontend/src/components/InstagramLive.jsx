import { useEffect, useMemo, useState } from 'react'
import { ChevronLeft, Instagram, Play, Pause, ShieldAlert } from 'lucide-react'
import { api } from '../api/client'

const badgeMap = {
  approve: 'bg-emerald-100 text-emerald-700',
  remove: 'bg-rose-100 text-rose-700',
  escalate: 'bg-amber-100 text-amber-700',
}

export default function InstagramLive({ onBack }) {
  const [sessionId, setSessionId] = useState(null)
  const [comments, setComments] = useState([])
  const [running, setRunning] = useState(true)
  const [rules, setRules] = useState(0)
  const [error, setError] = useState(null)

  useEffect(() => {
    let mounted = true
    ;(async () => {
      try {
        const start = await api.liveStart({ post_caption: 'Realtime moderation demo' })
        if (mounted) setSessionId(start.session_id)
      } catch (e) {
        if (mounted) setError(e.message)
      }
    })()
    return () => { mounted = false }
  }, [])

  useEffect(() => {
    if (!sessionId || !running) return
    const t = setInterval(async () => {
      try {
        const res = await api.livePoll(sessionId)
        setComments(res.comments || [])
        setRules(res.learning_rules || 0)
      } catch (e) {
        setError(e.message)
      }
    }, 1700)
    return () => clearInterval(t)
  }, [sessionId, running])

  const counts = useMemo(() => {
    const out = { approve: 0, remove: 0, escalate: 0 }
    comments.forEach((c) => { out[c.decision] = (out[c.decision] || 0) + 1 })
    return out
  }, [comments])

  const teach = async (comment, desired) => {
    if (!sessionId) return
    try {
      await api.liveTeach({
        session_id: sessionId,
        comment_id: comment.comment_id,
        desired_decision: desired,
        rating: desired === comment.decision ? 8 : 3,
        note: 'manual correction',
      })
      const res = await api.livePoll(sessionId)
      setComments(res.comments || [])
      setRules(res.learning_rules || 0)
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <header className="sticky top-0 z-20 bg-zinc-950/90 border-b border-zinc-800">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center gap-3">
          <Instagram className="w-5 h-5 text-pink-400" />
          <span className="text-sm font-semibold">Instagram Live Moderation</span>
          <span className="text-xs text-zinc-500">session: {sessionId || 'starting...'}</span>
          <button
            onClick={() => setRunning((v) => !v)}
            className="ml-auto text-xs px-3 py-1.5 rounded-lg border border-zinc-700 hover:bg-zinc-800 flex items-center gap-1.5"
          >
            {running ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
            {running ? 'Pause stream' : 'Resume stream'}
          </button>
          <button
            onClick={onBack}
            className="text-xs text-zinc-400 hover:text-zinc-200 flex items-center gap-1"
          >
            <ChevronLeft className="w-3.5 h-3.5" /> Home
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {error && (
          <div className="mb-4 bg-rose-500/10 border border-rose-500/30 text-rose-300 px-4 py-3 rounded-xl text-sm">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-6">
          <Metric label="Approved" value={counts.approve} tone="emerald" />
          <Metric label="Removed" value={counts.remove} tone="rose" />
          <Metric label="Escalated" value={counts.escalate} tone="amber" />
          <Metric label="Learning Rules" value={rules} tone="indigo" />
        </div>

        <div className="space-y-3">
          {comments.slice().reverse().map((c) => (
            <div key={c.comment_id} className="bg-zinc-900 border border-zinc-800 rounded-2xl p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm text-zinc-100">{c.content}</p>
                  <p className="text-xs text-zinc-500 mt-1">{c.reason_code} · {c.severity} · conf {c.confidence}</p>
                </div>
                <span className={`text-xs px-2 py-1 rounded-lg capitalize ${badgeMap[c.decision] || 'bg-zinc-700'}`}>
                  {c.decision}
                </span>
              </div>
              <p className="text-xs text-zinc-400 mt-2">{c.explanation}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                <TeachBtn onClick={() => teach(c, 'approve')} label="Teach Approve" />
                <TeachBtn onClick={() => teach(c, 'remove')} label="Teach Remove" />
                <TeachBtn onClick={() => teach(c, 'escalate')} label="Teach Escalate" />
              </div>
            </div>
          ))}
          {!comments.length && (
            <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8 text-center text-zinc-500 text-sm">
              Waiting for live comments...
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

function Metric({ label, value, tone }) {
  const toneMap = {
    emerald: 'text-emerald-300 border-emerald-500/30 bg-emerald-500/10',
    rose: 'text-rose-300 border-rose-500/30 bg-rose-500/10',
    amber: 'text-amber-300 border-amber-500/30 bg-amber-500/10',
    indigo: 'text-indigo-300 border-indigo-500/30 bg-indigo-500/10',
  }
  return (
    <div className={`rounded-xl border p-3 ${toneMap[tone]}`}>
      <div className="text-xs">{label}</div>
      <div className="text-2xl font-bold mt-1">{value}</div>
    </div>
  )
}

function TeachBtn({ onClick, label }) {
  return (
    <button
      onClick={onClick}
      className="text-xs px-2.5 py-1.5 rounded-lg border border-zinc-700 text-zinc-300 hover:bg-zinc-800 transition inline-flex items-center gap-1.5"
    >
      <ShieldAlert className="w-3.5 h-3.5" />
      {label}
    </button>
  )
}
