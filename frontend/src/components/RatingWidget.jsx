import { useState } from 'react'
import { Send } from 'lucide-react'

const DECISION_COLOR = {
  approve:  { active: 'bg-emerald-500 text-white border-emerald-500', hover: 'hover:border-emerald-500/60 hover:text-emerald-400' },
  remove:   { active: 'bg-rose-500 text-white border-rose-500',    hover: 'hover:border-rose-500/60 hover:text-rose-400' },
  escalate: { active: 'bg-amber-500 text-white border-amber-500',  hover: 'hover:border-amber-500/60 hover:text-amber-400' },
}

const LABELS = {
  1:  'Terrible',
  2:  'Very Bad',
  3:  'Bad',
  4:  'Poor',
  5:  'Okay',
  6:  'Decent',
  7:  'Good',
  8:  'Great',
  9:  'Excellent',
  10: 'Perfect',
}

export default function RatingWidget({ decision, onSubmit, loading }) {
  const [rating,  setRating]  = useState(null)
  const [hovered, setHovered] = useState(null)
  const [comment, setComment] = useState('')

  const colors = DECISION_COLOR[decision] ?? DECISION_COLOR.escalate
  const display = hovered ?? rating

  return (
    <div className="animate-slide-up space-y-4">
      <div>
        <p className="text-xs font-semibold uppercase tracking-widest text-zinc-500 mb-3">
          How well did the AI do? (1–10)
        </p>

        {/* rating buttons */}
        <div className="flex gap-1.5">
          {Array.from({ length: 10 }, (_, i) => i + 1).map(n => {
            const isActive = rating === n
            const isHigh   = hovered ? n <= hovered : n <= (rating ?? 0)
            return (
              <button
                key={n}
                onClick={() => setRating(n)}
                onMouseEnter={() => setHovered(n)}
                onMouseLeave={() => setHovered(null)}
                className={`
                  flex-1 aspect-square rounded-lg border text-xs font-bold
                  transition-all duration-100
                  ${isHigh
                    ? `${colors.active} scale-105`
                    : `bg-zinc-800/60 border-zinc-700 text-zinc-500 ${colors.hover}`
                  }
                `}
              >
                {n}
              </button>
            )
          })}
        </div>

        {/* label */}
        {display && (
          <p className="text-xs text-zinc-500 mt-2 text-center animate-fade-in">
            {display}/10 — {LABELS[display]}
          </p>
        )}
      </div>

      {/* comment */}
      <textarea
        rows={2}
        value={comment}
        onChange={e => setComment(e.target.value)}
        placeholder="Leave a comment on the AI's decision… (optional)"
        className="
          w-full bg-zinc-800/60 border border-zinc-700 rounded-xl px-4 py-3
          text-sm text-zinc-200 placeholder-zinc-600 resize-none
          focus:outline-none focus:border-indigo-500 transition-colors
        "
      />

      {/* submit */}
      <button
        disabled={!rating || loading}
        onClick={() => onSubmit(rating, comment)}
        className="
          w-full flex items-center justify-center gap-2 py-3 rounded-xl
          bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm
          transition-all duration-200 disabled:opacity-35 disabled:cursor-not-allowed
          shadow-[0_0_20px_rgba(99,102,241,.2)]
        "
      >
        {loading
          ? <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Submitting…</>
          : <><Send className="w-4 h-4" /> Submit Rating</>
        }
      </button>
    </div>
  )
}
