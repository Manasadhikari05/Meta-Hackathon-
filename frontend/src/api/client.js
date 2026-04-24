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
  // Legacy RL task runner
  reset:    (taskId)        => req(`/reset?task_id=${taskId}`, { method: 'POST' }),
  step:     (action)        => req('/step', { method: 'POST', body: JSON.stringify(action) }),
  state:    ()              => req('/state'),
}
