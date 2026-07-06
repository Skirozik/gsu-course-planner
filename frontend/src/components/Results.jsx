import { useState, useRef, useEffect } from 'react'
import api from '../api'

function ChatBot({ evalData, results }) {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: `Hey! I'm your academic advisor AI. I can answer questions about your course plan, explain why I recommended specific courses, or help you think through your schedule. What's on your mind?`,
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, open])

  const context = {
    gpa: evalData?.gpa,
    total_credits: evalData?.total_credits,
    credits_required: evalData?.credits_required,
    major: evalData?.major,
    recommended_courses: results?.recommendations?.recommended_courses ?? [],
    reasoning: results?.recommendations?.reasoning ?? '',
  }

  async function send() {
    const text = input.trim()
    if (!text || loading) return
    setInput('')
    const userMsg = { role: 'user', content: text }
    const newMsgs = [...messages, userMsg]
    setMessages(newMsgs)
    setLoading(true)
    try {
      const { data } = await api.post('/api/chat', {
        messages: newMsgs,
        context,
      })
      setMessages([...newMsgs, { role: 'assistant', content: data.reply }])
    } catch {
      setMessages([...newMsgs, { role: 'assistant', content: "Sorry, I couldn't reach the server. Make sure the API is running." }])
    } finally {
      setLoading(false)
    }
  }

  function onKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
  }

  return (
    <>
      {/* Floating button */}
      <button
        onClick={() => setOpen(v => !v)}
        className="fixed bottom-6 right-6 w-14 h-14 rounded-full flex items-center justify-center shadow-lg z-50 transition-all active:scale-95"
        style={{ background: '#2997FF', boxShadow: open ? '0 0 30px rgba(41,151,255,0.5)' : '0 4px 20px rgba(41,151,255,0.35)' }}
        title="Ask your advisor"
      >
        {open ? (
          <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
        )}
      </button>

      {/* Chat window */}
      {open && (
        <div
          className="fixed bottom-24 right-6 w-[370px] rounded-3xl overflow-hidden flex flex-col z-50"
          style={{
            height: 480,
            background: '#0a0a0a',
            border: '1px solid rgba(255,255,255,0.1)',
            boxShadow: '0 24px 60px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,255,255,0.05)',
          }}
        >
          {/* Header */}
          <div className="px-5 py-4 border-b border-white/10 flex items-center gap-3" style={{ background: '#111' }}>
            <div className="w-8 h-8 rounded-full flex items-center justify-center" style={{ background: 'rgba(41,151,255,0.15)' }}>
              <svg className="w-4 h-4" style={{ color: '#2997FF' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15m-6.75-3.25v6.75m0-6.75L12 14.5m0 6.75V14.5m0 6.75a24.301 24.301 0 01-4.5 0" />
              </svg>
            </div>
            <div>
              <p className="text-white text-sm font-semibold">Academic Advisor</p>
              <p className="text-xs" style={{ color: '#86868b' }}>Powered by Claude AI</p>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3" style={{ scrollbarWidth: 'none' }}>
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className="max-w-[80%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed"
                  style={m.role === 'user'
                    ? { background: '#2997FF', color: '#fff', borderBottomRightRadius: 6 }
                    : { background: '#1c1c1e', color: '#f5f5f7', borderBottomLeftRadius: 6 }
                  }
                >
                  {m.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="rounded-2xl px-4 py-3 flex gap-1" style={{ background: '#1c1c1e', borderBottomLeftRadius: 6 }}>
                  {[0, 1, 2].map(i => (
                    <span key={i} className="w-1.5 h-1.5 rounded-full bg-gray-500 animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
                  ))}
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="px-3 py-3 border-t border-white/10" style={{ background: '#111' }}>
            <div className="flex items-end gap-2 rounded-2xl px-4 py-2.5" style={{ background: '#1c1c1e' }}>
              <textarea
                className="flex-1 bg-transparent text-white text-sm resize-none outline-none placeholder-white/25 leading-relaxed"
                style={{ maxHeight: 80 }}
                rows={1}
                placeholder="Ask about your course plan…"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={onKey}
              />
              <button
                onClick={send}
                disabled={!input.trim() || loading}
                className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 transition-all disabled:opacity-30"
                style={{ background: '#2997FF', marginBottom: 1 }}
              >
                <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 10.5L12 3m0 0l7.5 7.5M12 3v18" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

const difficultyStyle = {
  Easy: { color: '#30d158', background: 'rgba(48,209,88,0.1)' },
  Medium: { color: '#ffd60a', background: 'rgba(255,214,10,0.1)' },
  Hard: { color: '#ff453a', background: 'rgba(255,69,58,0.1)' },
}

// Format a Banner time like "1350-1620" into "1:50 PM–4:20 PM".
function fmtTime(t) {
  if (!t || t === 'TBA') return ''
  const m = t.match(/^(\d{1,2})(\d{2})-(\d{1,2})(\d{2})$/)
  if (!m) return t
  const to12 = (h, mm) => {
    const ap = h >= 12 ? 'PM' : 'AM'
    const hh = ((h + 11) % 12) + 1
    return `${hh}:${mm} ${ap}`
  }
  return `${to12(+m[1], m[2])}–${to12(+m[3], m[4])}`
}

function ratingColor(r) {
  if (r == null) return '#86868b'
  if (r >= 4) return '#30d158'
  if (r >= 3) return '#ffd60a'
  return '#ff453a'
}

function CourseCard({ course, index, school, onRemove }) {
  const [open, setOpen] = useState(false)
  const [sections, setSections] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(false)

  async function toggle() {
    const next = !open
    setOpen(next)
    if (next && sections === null && !loading) {
      setLoading(true)
      setError(false)
      try {
        const { data } = await api.get('/api/sections', {
          params: { course: course.course_code, school },
        })
        setSections(data.sections || [])
      } catch {
        setError(true)
        setSections([])
      } finally {
        setLoading(false)
      }
    }
  }

  return (
    <div className="bg-zinc border border-white/10 rounded-2xl p-6 hover:border-white/20 transition-all">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-bold font-mono px-2.5 py-0.5 rounded-full"
              style={{ color: '#2997FF', background: 'rgba(41,151,255,0.1)' }}>
              {course.course_code}
            </span>
            {course.difficulty && difficultyStyle[course.difficulty] && (
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full"
                style={difficultyStyle[course.difficulty]}>
                {course.difficulty}
              </span>
            )}
          </div>
          <h3 className="font-semibold text-white text-base">{course.course_name}</h3>
          {course.reason && (
            <p className="text-sm text-gray mt-2 leading-relaxed">{course.reason}</p>
          )}
        </div>
        <div className="flex flex-col items-end gap-2 pt-1 flex-shrink-0">
          {onRemove && (
            <button
              onClick={() => onRemove(course.course_code)}
              title="Remove from plan"
              className="text-gray hover:text-red-400 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
          <span className="text-3xl font-bold select-none" style={{ color: 'rgba(255,255,255,0.05)' }}>
            {String(index + 1).padStart(2, '0')}
          </span>
        </div>
      </div>

      <button
        onClick={toggle}
        className="mt-4 flex items-center gap-1.5 text-sm font-semibold text-blue hover:opacity-80 transition-opacity"
      >
        {open ? 'Hide sections' : 'View sections & professors'}
        <svg className={`w-4 h-4 transition-transform ${open ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="mt-4 border-t border-white/10 pt-4">
          {loading ? (
            <div className="flex items-center gap-2 text-sm text-gray py-3">
              <span className="w-4 h-4 border-2 border-blue border-t-transparent rounded-full animate-spin" />
              Checking live sections and professor ratings…
            </div>
          ) : error ? (
            <p className="text-sm text-gray py-2">Couldn't load sections right now. Try again in a moment.</p>
          ) : sections.length === 0 ? (
            <p className="text-sm text-gray py-2">No sections offered this term.</p>
          ) : (
            <div className="space-y-2">
              {sections.map((s, si) => (
                <div key={si} className="flex items-center justify-between gap-3 bg-black/40 rounded-xl px-4 py-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono text-gray">§{s.section}</span>
                      {s.rmp_url ? (
                        <a href={s.rmp_url} target="_blank" rel="noopener noreferrer"
                          className="text-sm font-semibold text-white hover:text-blue transition-colors truncate">
                          {s.instructor}
                        </a>
                      ) : (
                        <span className="text-sm font-semibold text-white truncate">{s.instructor}</span>
                      )}
                    </div>
                    <div className="text-xs text-gray mt-0.5">
                      {fmtTime(s.time) || 'Time TBA'}{s.location ? ` in ${s.location}` : ''}
                    </div>
                  </div>
                  <div className="text-right flex-shrink-0">
                    {s.rating != null ? (
                      <>
                        <div className="text-sm font-bold" style={{ color: ratingColor(s.rating) }}>
                          {s.rating.toFixed(1)}<span className="text-gray font-normal text-xs">/5</span>
                        </div>
                        <div className="text-xs text-gray">{s.num_reviews ? `${s.num_reviews} reviews` : 'RMP'}</div>
                      </>
                    ) : (
                      <div className="text-xs text-gray">No rating</div>
                    )}
                  </div>
                </div>
              ))}
              <p className="text-xs text-gray pt-1">Ranked by professor rating. Section data is live from the registrar.</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function Results({ results, evalData, onReset, school }) {
  const recs = results?.recommendations?.recommended_courses ?? []
  const reasoning = results?.recommendations?.reasoning ?? ''
  const balance = results?.recommendations?.difficulty_balance ?? ''
  const semestersLeft = results?.recommendations?.semesters_remaining
  const available = results?.available_courses ?? []

  const [plan, setPlan] = useState(recs)
  const [feedback, setFeedback] = useState(null)
  const [feedbackLoading, setFeedbackLoading] = useState(false)
  const [feedbackError, setFeedbackError] = useState(false)

  const planCodes = new Set(plan.map((c) => c.course_code))
  const edited = plan.map((c) => c.course_code).join(',') !== recs.map((c) => c.course_code).join(',')
  const totalCredits = plan.reduce((sum, c) => sum + (Number(c.credits) || 3), 0)

  function addCourse(c) {
    if (planCodes.has(c.course_code)) return
    setPlan([...plan, { course_code: c.course_code, course_name: c.course_name ?? c.course_code, credits: c.credits ?? 3 }])
    setFeedback(null)
  }

  function removeCourse(code) {
    setPlan(plan.filter((c) => c.course_code !== code))
    setFeedback(null)
  }

  async function getFeedback() {
    if (feedbackLoading || !edited || plan.length === 0) return
    setFeedbackLoading(true)
    setFeedbackError(false)
    try {
      const { data } = await api.post('/api/plan-feedback', {
        courses: plan,
        student: {
          gpa: evalData?.gpa,
          total_credits: evalData?.total_credits,
          credits_required: evalData?.credits_required,
          major: evalData?.major,
        },
        school,
      })
      setFeedback(data.feedback || '')
    } catch {
      setFeedbackError(true)
    } finally {
      setFeedbackLoading(false)
    }
  }

  const [exporting, setExporting] = useState(null)

  async function exportPlan(format) {
    if (exporting) return
    setExporting(format)
    try {
      const student_info = {
        name: evalData?.student_name || 'Student',
        major: evalData?.major || '',
        semester: new Date().toLocaleString('en-US', { month: 'long', year: 'numeric' }),
      }
      const res = await api.post(
        '/api/export',
        { courses: plan, student_info, format },
        { responseType: 'blob' }
      )
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a')
      a.href = url
      a.download = `course-plan.${format}`
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch {
      // download failed silently; user can retry
    } finally {
      setExporting(null)
    }
  }

  const exportOptions = [
    { fmt: 'pdf', label: 'PDF', hint: 'Printable', icon: 'M7 3h7l4 4v14H7z M14 3v4h4 M9.5 12h5 M9.5 15.5h5' },
    { fmt: 'ics', label: 'Calendar', hint: 'Google / Apple', icon: 'M4 6h16v14H4z M4 10h16 M8 3v4 M16 3v4' },
    { fmt: 'txt', label: 'Text', hint: 'Copy anywhere', icon: 'M6 4h12 M6 9h12 M6 14h9 M6 19h6' },
  ]

  return (
    <div className="relative min-h-screen bg-black pb-24 pt-20 overflow-hidden">
      {/* Background glow — same as Hero but 25% brighter */}
      <div
        className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[500px] rounded-full blur-3xl pointer-events-none"
        style={{ background: 'radial-gradient(ellipse, rgba(41,151,255,0.15) 0%, transparent 65%)' }}
      />
      <div className="relative z-10 max-w-3xl mx-auto px-6">
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 text-xs font-semibold px-4 py-1.5 rounded-full mb-5"
            style={{ background: 'rgba(48,209,88,0.1)', color: '#30d158' }}>
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
            {edited ? 'Your plan' : 'Plan generated'}
          </div>
          <h1 className="text-5xl font-bold text-white tracking-tight mb-4">Your course plan.</h1>
          {reasoning && !edited && (
            <p className="text-gray max-w-xl mx-auto text-sm leading-relaxed">{reasoning}</p>
          )}
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          {[
            { label: 'Courses', value: plan.length },
            { label: 'Credits', value: totalCredits },
            { label: 'Semesters left', value: semestersLeft ?? '—' },
          ].map((s) => (
            <div key={s.label} className="bg-zinc border border-white/10 rounded-2xl p-5 text-center">
              <p className="text-2xl font-bold text-white">{s.value}</p>
              <p className="text-xs text-gray mt-1">{s.label}</p>
            </div>
          ))}
        </div>

        {/* Course cards */}
        <div className="space-y-3 mb-8">
          <h2 className="text-lg font-bold text-white mb-4">Your courses</h2>
          {plan.length === 0 ? (
            <div className="bg-zinc border border-white/10 rounded-2xl p-10 text-center text-gray">
              Your plan is empty. Add courses from the list below.
            </div>
          ) : (
            plan.map((course, i) => (
              <CourseCard key={course.course_code || i} course={course} index={i} school={school} onRemove={removeCourse} />
            ))
          )}
        </div>

        {/* Export */}
        {plan.length > 0 && (
          <div className="mb-8">
            <h2 className="text-lg font-bold text-white mb-4">Export your plan</h2>
            <div className="grid grid-cols-3 gap-3">
              {exportOptions.map((opt) => (
                <button
                  key={opt.fmt}
                  onClick={() => exportPlan(opt.fmt)}
                  disabled={exporting !== null}
                  className="bg-zinc border border-white/10 rounded-2xl p-5 flex flex-col items-center gap-2 hover:border-blue/40 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <span style={{ color: '#2997FF' }}>
                    {exporting === opt.fmt ? (
                      <span className="block w-6 h-6 border-2 border-blue border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round">
                        <path d={opt.icon} />
                      </svg>
                    )}
                  </span>
                  <span className="text-sm text-white font-semibold">{opt.label}</span>
                  <span className="text-xs text-gray">{opt.hint}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Eligible courses */}
        {available.length > 0 && (
          <details className="bg-zinc border border-white/10 rounded-2xl overflow-hidden mb-6 group">
            <summary className="px-6 py-4 cursor-pointer text-sm font-semibold text-white flex items-center justify-between">
              <span>Add courses ({available.length} eligible)</span>
              <svg className="w-4 h-4 text-gray group-open:rotate-180 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
              </svg>
            </summary>
            <div className="border-t border-white/10 divide-y divide-white/5">
              {available.slice(0, 30).map((c, i) => {
                const inPlan = planCodes.has(c.course_code)
                return (
                  <div key={i} className="px-6 py-3 flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <span className="text-xs font-mono font-bold mr-2" style={{ color: '#2997FF' }}>{c.course_code}</span>
                      <span className="text-sm text-gray">{c.course_name ?? c.course_code}</span>
                    </div>
                    <div className="flex items-center gap-3 flex-shrink-0">
                      <span className="text-xs" style={{ color: 'rgba(134,134,139,0.5)' }}>{c.credits ?? 3} cr</span>
                      <button
                        onClick={() => addCourse(c)}
                        disabled={inPlan}
                        className={`text-xs font-semibold px-3 py-1 rounded-full border transition-all ${inPlan ? 'border-white/10 text-gray cursor-default' : 'border-blue/40 text-blue hover:bg-blue hover:text-white'}`}
                      >
                        {inPlan ? 'Added' : '+ Add'}
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          </details>
        )}

        {/* AI feedback on the finalized plan */}
        {plan.length > 0 && (
          <div className="mb-8">
            <h2 className="text-lg font-bold text-white mb-1">How's this plan?</h2>
            <p className="text-sm text-gray mb-4">Add and remove courses until it's right, then get the advisor's take on your final selection.</p>
            {feedback ? (
              <div className="bg-zinc border border-white/10 rounded-2xl p-6">
                <p className="text-sm leading-relaxed whitespace-pre-line" style={{ color: 'rgba(245,245,247,0.9)' }}>{feedback}</p>
                <button onClick={getFeedback} disabled={feedbackLoading} className="mt-4 text-xs font-semibold text-blue hover:opacity-80 disabled:opacity-40">
                  Re-check my plan
                </button>
              </div>
            ) : (
              <button
                onClick={getFeedback}
                disabled={feedbackLoading || !edited}
                title={!edited ? 'Add or remove a course to get feedback on your own plan' : undefined}
                className="w-full bg-zinc border border-white/10 rounded-2xl py-4 text-sm font-semibold text-white hover:border-blue/40 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:border-white/10 flex items-center justify-center gap-2"
              >
                {feedbackLoading ? (
                  <>
                    <span className="w-4 h-4 border-2 border-blue border-t-transparent rounded-full animate-spin" />
                    Reviewing your plan…
                  </>
                ) : (
                  'Get AI feedback on my plan'
                )}
              </button>
            )}
            {feedbackError && <p className="text-sm text-gray mt-2">Couldn't get feedback right now. Try again.</p>}
          </div>
        )}

        <div className="rounded-2xl p-5 mb-6" style={{ background: 'rgba(255,214,10,0.05)', border: '1px solid rgba(255,214,10,0.1)' }}>
          <p className="text-xs leading-relaxed" style={{ color: 'rgba(255,214,10,0.7)' }}>
            <strong style={{ color: '#ffd60a' }}>Note:</strong> AI-generated recommendations. Always verify with your academic advisor before registering.
          </p>
        </div>

        <button
          onClick={onReset}
          className="w-full border border-white/10 text-gray py-3.5 rounded-xl font-semibold text-sm hover:border-blue/40 hover:text-blue transition-all"
        >
          ← Start over
        </button>
      </div>

      <ChatBot evalData={evalData} results={results} />
    </div>
  )
}
