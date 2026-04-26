import { useEffect, useRef, useState, useCallback } from 'react'
import { ChevronLeft, Radio, Trash2, ThumbsUp, Flag, ShieldAlert } from 'lucide-react'

/** Public FastAPI base (e.g. https://your-api.railway.app). Set at build time via VITE_BACKEND_URL. */
function deployedBackendBase() {
  const raw = (import.meta.env.VITE_BACKEND_URL || '').trim().replace(/\/$/, '')
  return raw || null
}

/** REST path for discord reviews: same host as WS, no /api prefix when talking to FastAPI directly. */
function discordReviewsUrl() {
  const base = deployedBackendBase()
  if (base) return `${base}/discord/reviews?pending_only=false`
  return '/api/discord/reviews?pending_only=false'
}

/**
 * Local dev: prefer direct FastAPI :7860 — Vite WS proxy is flaky.
 * Production / friends: set VITE_BACKEND_URL so every browser hits YOUR API, not 127.0.0.1 on their machine.
 */
function buildWsUrlCandidates() {
  const pub = deployedBackendBase()
  if (pub) {
    try {
      const u = new URL(pub.startsWith('http') ? pub : `https://${pub}`)
      const wsProto = u.protocol === 'https:' ? 'wss:' : 'ws:'
      return [`${wsProto}//${u.host}/ws/discord/live`]
    } catch {
      /* fall through to local */
    }
  }

  const secure = window.location.protocol === 'https:'
  const host = window.location.hostname
  const proto = secure ? 'wss' : 'ws'

  if (!secure) {
    const v4Local = host === 'localhost' ? '127.0.0.1' : host
    const urls = [`ws://${v4Local}:7860/ws/discord/live`]
    if (v4Local !== host) {
      urls.push(`ws://${host}:7860/ws/discord/live`)
    }
    urls.push(`${proto}://${window.location.host}/ws/discord/live`)
    return urls
  }
  return [`${proto}://${window.location.host}/ws/discord/live`]
}

function DecisionBadge({ decision }) {
  const styles = {
    approve: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    remove: 'bg-rose-100 text-rose-800 border-rose-200',
    escalate: 'bg-amber-100 text-amber-900 border-amber-200',
  }
  const s = styles[decision] || 'bg-gray-100 text-gray-800 border-gray-200'
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-md border ${s}`}>
      {decision?.toUpperCase() || '—'}
    </span>
  )
}

function BotActions({ actions }) {
  if (!actions?.length) return null
  return (
    <div className="flex flex-wrap gap-2 mt-2">
      {actions.map((a) => (
        <span
          key={a}
          className="inline-flex items-center gap-1 text-[10px] uppercase tracking-wide bg-gray-100 text-gray-600 px-2 py-0.5 rounded"
        >
          {a.includes('thumbs') && <ThumbsUp className="w-3 h-3" />}
          {a.includes('delete') && <Trash2 className="w-3 h-3" />}
          {(a.includes('report') || a.includes('reaction_report')) && <Flag className="w-3 h-3" />}
          {a.replace('reaction_', '').replace(/_/g, ' ')}
        </span>
      ))}
    </div>
  )
}

export default function LiveDiscord({ onBack }) {
  const [events, setEvents] = useState([])
  const [connected, setConnected] = useState(false)
  const [hello, setHello] = useState(null)
  const [lastError, setLastError] = useState(null)
  const bottomRef = useRef(null)
  const wsRef = useRef(null)

  const sortByTime = (list) =>
    list
      .sort((a, b) => {
        const ta = a.record?.created_at || (a.t ? String(a.t) : '')
        const tb = b.record?.created_at || (b.t ? String(b.t) : '')
        return ta.localeCompare(tb)
      })
      .slice(-200)

  const appendEvent = useCallback((evt) => {
    setEvents((prev) => {
      if (evt.type === 'discord_moderation' && evt.record?.message_id != null) {
        const mid = Number(evt.record.message_id)
        if (prev.some((e) => e.record?.message_id != null && Number(e.record.message_id) === mid)) {
          return prev
        }
      }
      return sortByTime([...prev, evt])
    })
  }, [])

  /** REST fallback: shows messages even when WebSocket cannot connect. */
  useEffect(() => {
    async function pollReviews() {
      try {
        const res = await fetch(discordReviewsUrl())
        if (!res.ok) return
        const j = await res.json()
        const items = j.items || []
        setEvents((prev) => {
          const seen = new Set(
            prev.filter((e) => e.record?.message_id != null).map((e) => Number(e.record.message_id))
          )
          const toAdd = []
          for (const rec of items) {
            const mid = rec.message_id
            if (mid == null) continue
            const n = Number(mid)
            if (seen.has(n)) continue
            seen.add(n)
            toAdd.push({ t: Date.now(), type: 'discord_moderation', record: rec, via: 'poll' })
          }
          if (toAdd.length === 0) return prev
          return [...prev, ...toAdd]
            .sort((a, b) => {
              const ta = a.record?.created_at || ''
              const tb = b.record?.created_at || ''
              return ta.localeCompare(tb)
            })
            .slice(-200)
        })
      } catch {
        /* backend down or CORS — ignore */
      }
    }
    pollReviews()
    const id = window.setInterval(pollReviews, 3000)
    return () => window.clearInterval(id)
  }, [])

  useEffect(() => {
    const urls = buildWsUrlCandidates()
    let cancelled = false
    let active = null
    let failTimer = null
    let reconnectTimer = null

    const failAll = () => {
      if (cancelled) return
      setConnected(false)
      setLastError(
        deployedBackendBase()
          ? 'Could not open the live WebSocket to your deployed API. Check that the backend is running, ' +
              'HTTPS uses wss://, and CORS allows this site.'
          : 'Could not open the live WebSocket. Run uvicorn on port 7860, or build the frontend with ' +
              'VITE_BACKEND_URL=https://your-public-api… so friends connect to your server, not their own 127.0.0.1.',
      )
    }

    function connectFrom(urlIndex) {
      if (cancelled) return
      if (urlIndex >= urls.length) {
        failAll()
        reconnectTimer = window.setTimeout(() => connectFrom(0), 4000)
        return
      }

      const url = urls[urlIndex]
      const socket = new WebSocket(url)
      active = socket
      wsRef.current = socket
      let opened = false

      socket.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data)
          if (data.type === 'hello') {
            setHello(data.discord || null)
            return
          }
          appendEvent({ t: Date.now(), ...data })
        } catch {
          appendEvent({ t: Date.now(), type: 'raw', raw: ev.data })
        }
      }

      failTimer = window.setTimeout(() => {
        if (cancelled || opened) return
        try {
          socket.close()
        } catch {
          /* ignore */
        }
      }, 2800)

      socket.onopen = () => {
        if (cancelled) return
        opened = true
        window.clearTimeout(failTimer)
        failTimer = null
        setConnected(true)
        setLastError(null)
      }

      socket.onclose = () => {
        if (cancelled) return
        window.clearTimeout(failTimer)
        failTimer = null
        setConnected(false)
        if (!opened) {
          connectFrom(urlIndex + 1)
          return
        }
        reconnectTimer = window.setTimeout(() => connectFrom(0), 3000)
      }
    }

    connectFrom(0)

    return () => {
      cancelled = true
      window.clearTimeout(failTimer)
      window.clearTimeout(reconnectTimer)
      try {
        active?.close()
      } catch {
        /* ignore */
      }
      wsRef.current = null
    }
  }, [appendEvent])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [events])

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-slate-100">
      <header className="sticky top-0 z-20 border-b border-slate-800/80 bg-slate-950/90 backdrop-blur-md">
        <div className="max-w-3xl mx-auto px-4 h-14 flex items-center justify-between">
          <button
            type="button"
            onClick={onBack}
            className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition"
          >
            <ChevronLeft className="w-4 h-4" />
            Back
          </button>
          <div className="flex items-center gap-2">
            <span className="relative flex h-2.5 w-2.5">
              <span
                className={`absolute inline-flex h-full w-full rounded-full opacity-75 ${
                  connected ? 'animate-ping bg-emerald-400' : 'bg-transparent'
                }`}
              />
              <span
                className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
                  connected ? 'bg-emerald-500' : 'bg-rose-500'
                }`}
              />
            </span>
            <span className="font-semibold text-sm tracking-tight">LIVE DISCORD</span>
            <Radio className={`w-4 h-4 ${connected ? 'text-emerald-400' : 'text-slate-500'}`} />
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-6 space-y-4">
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4 text-sm text-slate-400">
          <p className="text-slate-300 font-medium mb-1">Stream</p>
          <p>
            Messages from your Discord server appear here in real time. Decisions come from your configured
            classifier (RL / local model or OpenAI moderator). Bot actions:{' '}
            <strong className="text-slate-200">approve</strong> → 👍, <strong className="text-slate-200">remove</strong>{' '}
            → delete, <strong className="text-slate-200">escalate</strong> → 🚨 + mod log.
          </p>
          <p className="mt-2 text-xs text-slate-500">
            The page also polls the reviews API every few seconds (
            <code className="text-slate-400">
              {deployedBackendBase() ? `${deployedBackendBase()}/discord/reviews` : '/api/discord/reviews'}
            </code>
            ), so
            moderated messages should appear even if the WebSocket fails. WebSocket prefers{' '}
            <code className="text-slate-400">ws://127.0.0.1:7860/...</code> when you open the app on{' '}
            <code className="text-slate-400">localhost</code>.
          </p>
          {hello && (
            <p className="mt-2 text-xs text-slate-500">
              Bot: {hello.user || '…'} · watched: {hello.watched_messages ?? 0}
            </p>
          )}
          {lastError && <p className="mt-2 text-rose-400 text-xs">{lastError}</p>}
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/30 min-h-[320px] max-h-[calc(100vh-220px)] overflow-y-auto p-3 space-y-3">
          {events.length === 0 && (
            <p className="text-center text-slate-500 text-sm py-12">Waiting for Discord messages…</p>
          )}
          {events.map((e) => {
            if (e.type === 'discord_error') {
              return (
                <div
                  key={e.t}
                  className="rounded-lg border border-rose-900/50 bg-rose-950/30 px-3 py-2 text-sm text-rose-200"
                >
                  <ShieldAlert className="w-4 h-4 inline mr-1" />
                  Error #{e.message_id}: {e.error}
                </div>
              )
            }
            if (e.type === 'discord_moderation' || e.type === 'discord_review') {
              const r = e.record
              if (!r) return null
              return (
                <div
                  key={`${e.type}-${r.message_id}-${e.t}`}
                  className="rounded-lg border border-slate-800 bg-slate-950/80 p-3 shadow-sm"
                >
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <span className="text-xs font-mono text-slate-500">#{r.message_id}</span>
                    <DecisionBadge decision={r.decision} />
                  </div>
                  <div className="text-xs text-slate-500 mb-1">{r.author_name}</div>
                  <p className="text-sm text-slate-200 whitespace-pre-wrap break-words">{r.content}</p>
                  <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-slate-500">
                    <span>reason: {r.reason_code}</span>
                    <span>·</span>
                    <span>sev: {r.severity}</span>
                    <span>·</span>
                    <span>conf: {r.confidence}</span>
                    {r.classifier_source && (
                      <>
                        <span>·</span>
                        <span className="text-emerald-600/90">{r.classifier_source}</span>
                      </>
                    )}
                  </div>
                  {r.explanation && (
                    <p className="mt-1 text-xs text-slate-400 italic">{r.explanation}</p>
                  )}
                  <BotActions actions={r.bot_actions} />
                  <div className="mt-1 text-[10px] text-slate-600">
                    {r.action_taken} · {r.status}
                    {e.type === 'discord_review' && ' · manual review'}
                  </div>
                </div>
              )
            }
            return (
              <div key={e.t} className="text-xs font-mono text-slate-600">
                {JSON.stringify(e)}
              </div>
            )
          })}
          <div ref={bottomRef} />
        </div>
      </main>
    </div>
  )
}
