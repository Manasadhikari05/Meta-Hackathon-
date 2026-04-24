import { MessageSquare, Clock, AlertTriangle, FileText, Hash } from 'lucide-react'

const PLATFORM_COLOR = {
  community_forum: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
  social_media:    'bg-sky-500/10 text-sky-400 border-sky-500/20',
  marketplace:     'bg-orange-500/10 text-orange-400 border-orange-500/20',
  default:         'bg-zinc-700/50 text-zinc-400 border-zinc-700',
}

function riskLevel(author) {
  if (author.prior_violations >= 3 || author.account_age_days < 7) return 'high'
  if (author.prior_violations >= 1 || author.account_age_days < 30) return 'medium'
  return 'low'
}

const RISK_COLORS = {
  high:   { bg: 'bg-rose-500/10', text: 'text-rose-400', border: 'border-rose-500/20', dot: 'bg-rose-400' },
  medium: { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/20', dot: 'bg-amber-400' },
  low:    { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20', dot: 'bg-emerald-400' },
}

export default function PostCard({ observation, stepKey }) {
  if (!observation) return null
  const { post, author, thread_context, instructions, step } = observation

  const platformStyle = PLATFORM_COLOR[post.platform] ?? PLATFORM_COLOR.default
  const risk = riskLevel(author)
  const rc = RISK_COLORS[risk]

  return (
    <div key={stepKey} className="animate-slide-up">
      {/* header row */}
      <div className="flex items-center gap-3 mb-5">
        <span className={`text-xs font-semibold px-2.5 py-1 rounded-md border ${platformStyle}`}>
          {post.platform.replace(/_/g, ' ')}
        </span>
        <span className="text-xs text-zinc-600 font-mono">#{post.post_id}</span>
        <span className="ml-auto text-xs text-zinc-600">Step {step + 1}</span>
      </div>

      {/* post content */}
      <div className="bg-zinc-800/50 border border-zinc-700/60 rounded-xl p-5 mb-5">
        <div className="flex items-start gap-2 mb-3">
          <MessageSquare className="w-4 h-4 text-zinc-500 mt-0.5 shrink-0" />
          <p className="text-zinc-100 text-base leading-relaxed font-medium">{post.content}</p>
        </div>
      </div>

      {/* author + thread */}
      <div className="grid grid-cols-2 gap-3 mb-5">
        {/* author risk */}
        <div className={`rounded-xl border p-4 ${rc.bg} ${rc.border}`}>
          <div className="flex items-center gap-1.5 mb-2">
            <span className={`w-2 h-2 rounded-full ${rc.dot}`} />
            <span className={`text-xs font-semibold uppercase tracking-wider ${rc.text}`}>
              Author · {risk} risk
            </span>
          </div>
          <div className="space-y-1">
            <Stat icon={Clock} label="Age" value={`${author.account_age_days}d`} />
            <Stat
              icon={AlertTriangle}
              label="Violations"
              value={author.prior_violations}
              warn={author.prior_violations > 0}
            />
            <Stat icon={FileText} label="Posts" value={author.total_posts} />
          </div>
        </div>

        {/* thread context */}
        <div className="rounded-xl border border-zinc-700/60 bg-zinc-800/30 p-4">
          <div className="flex items-center gap-1.5 mb-2">
            <Hash className="w-3 h-3 text-zinc-500" />
            <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Thread</span>
          </div>
          <p className="text-sm text-zinc-300 capitalize mb-2">{thread_context.topic}</p>
          {thread_context.reply_to_post_id && (
            <p className="text-xs text-zinc-500">
              Reply to <span className="font-mono text-zinc-400">{thread_context.reply_to_post_id}</span>
            </p>
          )}
        </div>
      </div>

      {/* instructions */}
      <div className="rounded-xl border border-zinc-700/40 bg-zinc-800/20 px-4 py-3">
        <p className="text-xs text-zinc-500 leading-relaxed">{instructions}</p>
      </div>
    </div>
  )
}

function Stat({ icon: Icon, label, value, warn }) {
  return (
    <div className="flex items-center justify-between text-xs">
      <span className="flex items-center gap-1 text-zinc-500">
        <Icon className="w-3 h-3" />
        {label}
      </span>
      <span className={warn ? 'text-rose-400 font-semibold' : 'text-zinc-300'}>{value}</span>
    </div>
  )
}
