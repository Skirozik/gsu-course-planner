import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  // The backend is on Render's free tier and sleeps after ~15 min idle; a cold
  // start takes 30-60s. The ceiling has to clear that comfortably, but it has to
  // exist — with no timeout at all, an unreachable backend hangs the tab forever.
  timeout: 120000,
})

// A sleeping instance answers the first request with a gateway error, or drops
// it while booting. Those are worth retrying. A 4xx is the server telling us the
// request itself is wrong, so retrying it just repeats the same failure.
const RETRY_STATUSES = new Set([502, 503, 504])

// The retry budget has to span an entire cold start, or it just fails faster
// than doing nothing. A free-tier Render instance takes 30-60s to wake, and
// during the boot it refuses connections rather than holding them open — so the
// client burns through attempts in seconds unless the waits are this long.
const RETRY_WINDOW_MS = 90000
const MAX_ATTEMPTS = 8
const BACKOFF_MS = [2000, 5000, 10000, 15000, 20000, 20000, 20000]

function isRetryable(err) {
  if (err.code === 'ECONNABORTED' || err.code === 'ERR_NETWORK') return true
  return RETRY_STATUSES.has(err.response?.status)
}

api.interceptors.response.use(undefined, async (err) => {
  const config = err.config
  if (!config || !isRetryable(err)) return Promise.reject(err)

  // Deadline is set on the first failure so the window covers the whole wake,
  // not each attempt individually.
  if (!config._deadline) config._deadline = Date.now() + RETRY_WINDOW_MS
  config._attempt = (config._attempt || 1) + 1

  const wait = BACKOFF_MS[Math.min(config._attempt - 2, BACKOFF_MS.length - 1)]
  const outOfAttempts = config._attempt > MAX_ATTEMPTS
  const outOfTime = Date.now() + wait >= config._deadline
  if (outOfAttempts || outOfTime) return Promise.reject(err)

  // Let the caller show "waking up" instead of a spinner that looks stuck.
  if (typeof config.onRetry === 'function') config.onRetry(config._attempt)

  await new Promise((resolve) => setTimeout(resolve, wait))
  return api(config)
})

/**
 * Start waking the backend as early as possible, so the cold start overlaps with
 * the user reading the landing page instead of with their upload. Fire and
 * forget: a failure here just means the upload pays the wake cost as before.
 */
export function warmUp() {
  api.get('/api/health').catch(() => {})
}

/**
 * Turn an axios failure into something true. Without this every transport
 * problem gets reported as a bad PDF, which is wrong and unfixable by the user.
 */
export function describeError(err, fallback) {
  const detail = err.response?.data?.detail

  // FastAPI HTTPException detail — the server explaining itself.
  if (typeof detail === 'string') return detail

  // FastAPI request-validation errors arrive as an array of objects.
  if (Array.isArray(detail)) return 'The server rejected that request. Please try again.'

  if (err.code === 'ECONNABORTED') {
    return 'The server took too long to respond. It may be waking up — please try again in a moment.'
  }

  if (!err.response) {
    // Distinguish "your wifi is off" from "we waited out a full cold start and
    // it never came up" — the second is not something the user can fix.
    return err.config?._attempt > 1
      ? 'The server did not come back up after 90 seconds. It may be down — please try again in a few minutes.'
      : 'Could not reach the server. Check your connection and try again.'
  }

  const status = err.response.status
  if (RETRY_STATUSES.has(status)) {
    return 'The server is starting up and did not answer in time. Please try again in a moment.'
  }
  if (status === 429) {
    return 'Too many requests. Please wait a minute and try again.'
  }
  if (status === 413) {
    return 'That file is too large. Please upload a PDF under 10 MB.'
  }

  return fallback
}

export default api
