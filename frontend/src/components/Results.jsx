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

export default function Results({ results, evalData, onReset }) {
  const recs = results?.recommendations?.recommended_courses ?? []
  const reasoning = results?.recommendations?.reasoning ?? ''
  const balance = results?.recommendations?.difficulty_balance ?? ''
  const semestersLeft = results?.recommendations?.semesters_remaining
  const available = results?.available_courses ?? []

  const difficultyStyle = {
    Easy: { color: '#30d158', background: 'rgba(48,209,88,0.1)' },
    Medium: { color: '#ffd60a', background: 'rgba(255,214,10,0.1)' },
    Hard: { color: '#ff453a', background: 'rgba(255,69,58,0.1)' },
  }

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
            Plan generated
          </div>
          <h1 className="text-5xl font-bold text-white tracking-tight mb-4">Your course plan.</h1>
          {reasoning && (
            <p className="text-gray max-w-xl mx-auto text-sm leading-relaxed">{reasoning}</p>
          )}
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          {[
            { label: 'Courses', value: recs.length },
            { label: 'Difficulty', value: balance || '—' },
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
          <h2 className="text-lg font-bold text-white mb-4">Recommended courses</h2>
          {recs.length === 0 ? (
            <div className="bg-zinc border border-white/10 rounded-2xl p-10 text-center text-gray">
              No recommendations generated. Try adjusting your preferences.
            </div>
          ) : (
            recs.map((course, i) => (
              <div key={i} className="bg-zinc border border-white/10 rounded-2xl p-6 hover:border-white/20 transition-all">
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
                  <span className="text-3xl font-bold select-none pt-1" style={{ color: 'rgba(255,255,255,0.05)' }}>
                    {String(i + 1).padStart(2, '0')}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Eligible courses */}
        {available.length > 0 && (
          <details className="bg-zinc border border-white/10 rounded-2xl overflow-hidden mb-6 group">
            <summary className="px-6 py-4 cursor-pointer text-sm font-semibold text-white flex items-center justify-between">
              <span>All eligible courses ({available.length})</span>
              <svg className="w-4 h-4 text-gray group-open:rotate-180 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
              </svg>
            </summary>
            <div className="border-t border-white/10 divide-y divide-white/5">
              {available.slice(0, 30).map((c, i) => (
                <div key={i} className="px-6 py-3 flex items-center justify-between">
                  <div>
                    <span className="text-xs font-mono font-bold mr-2" style={{ color: '#2997FF' }}>{c.course_code}</span>
                    <span className="text-sm text-gray">{c.course_name ?? c.course_code}</span>
                  </div>
                  <span className="text-xs" style={{ color: 'rgba(134,134,139,0.5)' }}>{c.credits ?? 3} cr</span>
                </div>
              ))}
            </div>
          </details>
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
