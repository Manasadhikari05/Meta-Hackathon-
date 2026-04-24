import { Zap, Layers, FlaskConical } from 'lucide-react'

const TASKS = [
  {
    id: 'task1',
    label: 'Quick Scan',
    icon: Zap,
    posts: 1,
    difficulty: 1,
    difficultyLabel: 'Easy',
    color: 'emerald',
    description: 'A single clear-cut post. Perfect for testing the loop.',
    traits: ['1 post', 'No edge cases', 'Instant result'],
  },
  {
    id: 'task2',
    label: 'Batch Review',
    icon: Layers,
    posts: 8,
    difficulty: 2,
    difficultyLabel: 'Medium',
    color: 'amber',
    description: 'Eight posts including borderline toxicity. Confidence calibration matters.',
    traits: ['8 posts', 'Borderline content', 'Confidence scored'],
  },
  {
    id: 'task3',
    label: 'Edge Cases',
    icon: FlaskConical,
    posts: 12,
    difficulty: 3,
    difficultyLabel: 'Hard',
    color: 'rose',
    description: 'Sarcasm, obfuscation, implicit harm. Explanation required on every call.',
    traits: ['12 posts', 'Obfuscation & sarcasm', 'Explanation required'],
  },
]

const colorMap = {
  emerald: {
    border:   'border-emerald-500/40 hover:border-emerald-500/80',
    badge:    'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
    dot:      'bg-emerald-400',
    glow:     'hover:shadow-[0_0_28px_rgba(16,185,129,.18)]',
    btn:      'bg-emerald-600 hover:bg-emerald-500',
    icon:     'text-emerald-400',
    iconBg:   'bg-emerald-500/10',
  },
  amber: {
    border:   'border-amber-500/40 hover:border-amber-500/80',
    badge:    'bg-amber-500/10 text-amber-400 border border-amber-500/20',
    dot:      'bg-amber-400',
    glow:     'hover:shadow-[0_0_28px_rgba(245,158,11,.18)]',
    btn:      'bg-amber-600 hover:bg-amber-500',
    icon:     'text-amber-400',
    iconBg:   'bg-amber-500/10',
  },
  rose: {
    border:   'border-rose-500/40 hover:border-rose-500/80',
    badge:    'bg-rose-500/10 text-rose-400 border border-rose-500/20',
    dot:      'bg-rose-400',
    glow:     'hover:shadow-[0_0_28px_rgba(244,63,94,.18)]',
    btn:      'bg-rose-600 hover:bg-rose-500',
    icon:     'text-rose-400',
    iconBg:   'bg-rose-500/10',
  },
}

export default function TaskSelector({ onSelect, loading }) {
  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col items-center justify-center px-6 py-16">
      <div className="mb-12 text-center animate-fade-in">
        <p className="text-xs font-semibold tracking-[.2em] text-zinc-500 uppercase mb-3">Select Task</p>
        <h1 className="text-4xl font-bold text-zinc-100 mb-3">Choose your challenge</h1>
        <p className="text-zinc-400 text-base">
          Each task runs the live backend. Your decisions are scored in real-time.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-4xl">
        {TASKS.map((task, i) => {
          const c = colorMap[task.color]
          const Icon = task.icon
          return (
            <div
              key={task.id}
              className={`
                group relative flex flex-col bg-zinc-900 border rounded-2xl p-7
                transition-all duration-300 cursor-pointer
                ${c.border} ${c.glow}
                animate-slide-up
              `}
              style={{ animationDelay: `${i * 80}ms` }}
              onClick={() => !loading && onSelect(task.id)}
            >
              {/* difficulty dots */}
              <div className="absolute top-5 right-5 flex gap-1">
                {[1, 2, 3].map(d => (
                  <span
                    key={d}
                    className={`w-2 h-2 rounded-full ${d <= task.difficulty ? c.dot : 'bg-zinc-700'}`}
                  />
                ))}
              </div>

              <div className={`w-11 h-11 rounded-xl flex items-center justify-center mb-5 ${c.iconBg}`}>
                <Icon className={`w-5 h-5 ${c.icon}`} />
              </div>

              <span className={`text-xs font-semibold px-2 py-0.5 rounded-md w-fit mb-3 ${c.badge}`}>
                {task.difficultyLabel}
              </span>

              <h2 className="text-xl font-bold text-zinc-100 mb-2">{task.label}</h2>
              <p className="text-zinc-400 text-sm leading-relaxed mb-6">{task.description}</p>

              <ul className="space-y-1.5 mb-8">
                {task.traits.map(t => (
                  <li key={t} className="flex items-center gap-2 text-xs text-zinc-500">
                    <span className={`w-1 h-1 rounded-full ${c.dot}`} />
                    {t}
                  </li>
                ))}
              </ul>

              <button
                disabled={loading}
                className={`
                  mt-auto w-full py-2.5 rounded-xl text-sm font-semibold text-white
                  transition-all duration-200 disabled:opacity-40
                  ${c.btn}
                `}
              >
                {loading ? 'Starting…' : `Start ${task.label} →`}
              </button>
            </div>
          )
        })}
      </div>
    </div>
  )
}
