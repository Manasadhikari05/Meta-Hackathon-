const BASE = '/api'

async function req(path, opts = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  health:   ()              => req('/health'),

  // AI Moderator
  moderate: (content, platform) =>
    req('/moderate', { method: 'POST', body: JSON.stringify({ content, platform }) }),
  feedback: (payload)       =>
    req('/feedback', { method: 'POST', body: JSON.stringify(payload) }),
  history:  ()              => req('/history'),
  policyStats: ()           => req('/policy/stats'),
  policyRules: (limit = 20) => req(`/policy/rules?limit=${limit}`),

  // OpenEnv RL task runner
  reset:    (taskId)        => req(`/reset?task_id=${taskId}`, { method: 'POST' }),
  step:     (action)        => req('/step', { method: 'POST', body: JSON.stringify(action) }),
  state:    ()              => req('/state'),

  // OpenEnv dataset endpoints
  posts:    (limit, difficulty) => {
    const params = new URLSearchParams()
    if (limit)      params.set('limit', limit)
    if (difficulty) params.set('difficulty', difficulty)
    const qs = params.toString()
    return req(`/posts${qs ? `?${qs}` : ''}`)
  },
  stats:    ()              => req('/stats'),

  // Live Instagram-style moderation demo
  liveStart: (payload)      => req('/live-comments/start', { method: 'POST', body: JSON.stringify(payload || {}) }),
  livePoll:  (sessionId)    => req(`/live-comments/poll?session_id=${sessionId}`),
  liveTeach: (payload)      => req('/live-comments/feedback', { method: 'POST', body: JSON.stringify(payload) }),
}
