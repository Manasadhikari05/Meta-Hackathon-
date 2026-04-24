import { useState, useCallback } from 'react'
import { Shield, ChevronLeft, Wifi, WifiOff, RefreshCw } from 'lucide-react'
import { api } from '../api/client'
import TaskSelector from './TaskSelector'
import PostCard from './PostCard'
import ActionForm from './ActionForm'
import ScorePanel from './ScorePanel'
import EpisodeSummary from './EpisodeSummary'

const TASK_MAX  = { task1: 1, task2: 8, task3: 12 }
const TASK_LABEL = { task1: 'Quick Scan', task2: 'Batch Review', task3: 'Edge Cases' }

// phase: 'selecting' | 'playing' | 'done'
export default function Dashboard({ onBack }) {
  const [phase, setPhase]           = useState('selecting')
  const [taskId, setTaskId]         = useState(null)
  const [observation, setObs]       = useState(null)
  const [history, setHistory]       = useState([])
  const [lastReward, setLastReward] = useState(null)
  const [loading, setLoading]       = useState(false)
  const [error, setError]           = useState(null)
  const [stepKey, setStepKey]       = useState(0) // forces PostCard re-mount for animation

  const startTask = useCallback(async (id) => {
    setLoading(true)
    setError(null)
    try {
      const obs = await api.reset(id)
      setTaskId(id)
      setObs(obs)
      setHistory([])
      setLastReward(null)
      setPhase('playing')
      setStepKey(k => k + 1)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  const submitAction = useCallback(async (action) => {
    setLoading(true)
    setError(null)
    try {
      const result = await api.step(action)
      const { observation: nextObs, reward, done } = result

      setLastReward(reward)
      setHistory(h => [...h, { obs: observation, action, reward }])

      if (done) {
        setPhase('done')
      } else {
        setObs(nextObs)
        setStepKey(k => k + 1)
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [observation])

  const replay = () => startTask(taskId)
  const backToSelect = () => {
    setPhase('selecting')
    setObs(null)
    setHistory([])
    setLastReward(null)
    setError(null)
  }

  /* ── Done screen ──────────────────────────────────────── */
  if (phase === 'done') {
    return (
      <EpisodeSummary
        history={history}
        taskId={taskId}
        onReplay={replay}
        onHome={onBack}
      />
    )
  }

  /* ── Task selector ────────────────────────────────────── */
  if (phase === 'selecting') {
    return (
      <div className="relative">
        {/* back button */}
        <button
          onClick={onBack}
          className="absolute top-6 left-6 z-10 flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-300 transition"
        >
          <ChevronLeft className="w-4 h-4" /> Home
        </button>
        <TaskSelector onSelect={startTask} loading={loading} />
        {error && <ErrorBanner msg={error} onDismiss={() => setError(null)} />}
      </div>
    )
  }

  /* ── Playing ──────────────────────────────────────────── */
  const maxSteps = TASK_MAX[taskId] ?? 1
  const stepsDone = history.length
  const progress = maxSteps > 0 ? (stepsDone / maxSteps) * 100 : 0

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col">
      {/* Top bar */}
      <header className="sticky top-0 z-30 bg-zinc-950/80 backdrop-blur border-b border-zinc-800/60">
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center gap-4">
          {/* logo */}
          <div className="flex items-center gap-2 shrink-0">
            <Shield className="w-5 h-5 text-indigo-400" strokeWidth={1.5} />
            <span className="font-bold text-zinc-100 text-sm">ModGuard</span>
            <span className="text-zinc-700 text-sm">/</span>
            <span className="text-zinc-400 text-sm font-medium">Dashboard</span>
          </div>

          {/* task badge */}
          <span className="bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold px-2.5 py-1 rounded-md">
            {TASK_LABEL[taskId]}
          </span>

          {/* progress */}
          <div className="flex-1 flex items-center gap-3 min-w-0">
            <div className="flex-1 max-w-xs h-1.5 bg-zinc-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-indigo-500 rounded-full score-fill"
                style={{ width: `${progress}%` }}
              />
            </div>
            <span className="text-xs text-zinc-500 shrink-0 tabular-nums">
              {stepsDone} / {maxSteps}
            </span>
          </div>

          {/* status dot */}
          <div className="flex items-center gap-1.5 shrink-0">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs text-zinc-600">Live</span>
          </div>

          {/* actions */}
          <button
            onClick={backToSelect}
            className="text-xs text-zinc-500 hover:text-zinc-300 flex items-center gap-1 transition ml-2"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Reset
          </button>
          <button
            onClick={onBack}
            className="text-xs text-zinc-500 hover:text-zinc-300 flex items-center gap-1 transition"
          >
            <ChevronLeft className="w-3.5 h-3.5" /> Home
          </button>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-8">
        {error && <ErrorBanner msg={error} onDismiss={() => setError(null)} />}

        <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-6">
          {/* Left: Post + Form */}
          <div className="space-y-5">
            <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
              <PostCard observation={observation} stepKey={stepKey} />
            </div>
            <ActionForm
              onSubmit={submitAction}
              loading={loading}
              taskId={taskId}
              disabled={!observation}
            />
          </div>

          {/* Right: Score panel */}
          <div className="lg:sticky lg:top-20 lg:self-start">
            <ScorePanel history={history} taskId={taskId} lastReward={lastReward} />
          </div>
        </div>
      </main>
    </div>
  )
}

function ErrorBanner({ msg, onDismiss }) {
  return (
    <div className="flex items-center gap-3 bg-rose-500/10 border border-rose-500/30 text-rose-400 rounded-xl px-4 py-3 mb-5 text-sm animate-fade-in">
      <WifiOff className="w-4 h-4 shrink-0" />
      <span className="flex-1">{msg}</span>
      <button onClick={onDismiss} className="text-rose-500 hover:text-rose-300 text-lg leading-none">×</button>
    </div>
  )
}
