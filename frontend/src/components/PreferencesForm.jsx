import { useState, useEffect } from 'react'
import api, { describeError } from '../api'

export default function PreferencesForm({ school, evalData, onResults, onBack }) {
  const [form, setForm] = useState({ career_goals: '', max_courses: 4, has_job: false })
  const [status, setStatus] = useState('idle')
  const [error, setError] = useState(null)

  const gpa = evalData?.gpa
  const totalCredits = evalData?.total_credits ?? 0
  const requiredCredits = evalData?.credits_required ?? 120
  const completed = evalData?.completed_courses?.length ?? 0
  const progress = Math.min(100, Math.round((totalCredits / requiredCredits) * 100))
  const [displayProgress, setDisplayProgress] = useState(0)

  useEffect(() => {
    const timer = setTimeout(() => setDisplayProgress(progress), 120)
    return () => clearTimeout(timer)
  }, [progress])

  async function handleSubmit(e) {
    e.preventDefault()
    setStatus('loading')
    setError(null)
    try {
      const { data } = await api.post('/api/recommendations', {
        eval_data: evalData,
        school,
        ...form,
        max_courses: Number(form.max_courses),
      })
      onResults(data)
    } catch (err) {
      setStatus('error')
      setError(describeError(err, 'Something went wrong. Please try again.'))
    }
  }

  return (
    <div className="min-h-screen bg-black pb-24 pt-20">
      <div className="max-w-3xl mx-auto px-6">
        <button onClick={onBack} className="flex items-center gap-1.5 text-blue text-sm mb-8 hover:opacity-70 transition-opacity">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          Back
        </button>

        <p className="text-blue font-semibold text-sm tracking-widest uppercase mb-3">Step 3 of 3</p>
        <h1 className="text-5xl font-bold text-white tracking-tight mb-2">Your preferences.</h1>
        <p className="text-gray mb-10">Help the AI tailor your plan.</p>

        {/* Transcript summary */}
        <div className="bg-zinc border border-white/10 rounded-2xl p-6 mb-6 grid grid-cols-3 gap-4 text-center">
          {[
            { label: 'GPA', value: gpa ?? '—' },
            { label: 'Credits Earned', value: totalCredits },
            { label: 'Courses Done', value: completed },
          ].map((s) => (
            <div key={s.label}>
              <p className="text-2xl font-bold text-white">{s.value}</p>
              <p className="text-xs text-gray mt-1">{s.label}</p>
            </div>
          ))}
          <div className="col-span-3 pt-4 border-t border-white/10">
            <div className="flex justify-between text-xs text-gray mb-2">
              <span>Degree progress</span>
              <span style={{ color: '#2997FF' }}>{displayProgress}%</span>
            </div>
            <div className="h-2 bg-white/10 rounded-full overflow-hidden">
              <div
                style={{
                  height: '100%',
                  width: `${displayProgress}%`,
                  borderRadius: '9999px',
                  background: 'linear-gradient(90deg, #1a6fd4 0%, #2997FF 60%, #6dbfff 100%)',
                  boxShadow: displayProgress > 0
                    ? '0 0 12px 3px rgba(41,151,255,0.55), 0 0 4px 1px rgba(41,151,255,0.9)'
                    : 'none',
                  transition: 'width 1.4s cubic-bezier(0.4, 0, 0.2, 1)',
                }}
              />
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="bg-zinc border border-white/10 rounded-2xl p-8 space-y-7">
          <div>
            <label className="block text-sm font-semibold text-white mb-2">
              Career goals <span className="font-normal text-gray">(optional)</span>
            </label>
            <textarea
              className="w-full bg-black border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-white/20 focus:outline-none focus:ring-2 focus:ring-blue/40 focus:border-blue/60 transition resize-none"
              rows={3}
              placeholder="e.g. I want to work in software engineering at a tech company…"
              value={form.career_goals}
              onChange={(e) => setForm({ ...form, career_goals: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-white mb-3">Courses next semester</label>
            <div className="flex gap-3">
              {[2, 3, 4, 5].map((n) => (
                <button
                  key={n}
                  type="button"
                  onClick={() => setForm({ ...form, max_courses: n })}
                  className={`flex-1 py-3 rounded-xl text-sm font-semibold border-2 transition-all
                    ${form.max_courses === n
                      ? 'border-blue bg-blue text-white'
                      : 'border-white/10 text-gray hover:border-blue/40 hover:text-white'
                    }`}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-white">Working while in school?</p>
              <p className="text-xs text-gray mt-0.5">We'll suggest a lighter load</p>
            </div>
            <button
              type="button"
              onClick={() => setForm({ ...form, has_job: !form.has_job })}
              className="relative w-12 h-7 rounded-full transition-colors"
              style={{ background: form.has_job ? '#2997FF' : 'rgba(255,255,255,0.1)' }}
            >
              <span
                className="absolute top-0.5 w-6 h-6 bg-white rounded-full shadow-lg transition-transform"
                style={{ transform: form.has_job ? 'translateX(20px)' : 'translateX(2px)' }}
              />
            </button>
          </div>

          {error && (
            <div className="rounded-xl p-4" style={{ background: 'rgba(255,59,48,0.08)', border: '1px solid rgba(255,59,48,0.2)' }}>
              <p className="text-sm" style={{ color: '#ff6b6b' }}>{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={status === 'loading'}
            className="w-full bg-blue text-white py-3.5 rounded-xl font-semibold text-sm transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2 hover:shadow-glow"
          >
            {status === 'loading' ? (
              <>
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Claude is thinking…
              </>
            ) : (
              'Generate my course plan →'
            )}
          </button>
        </form>
      </div>
    </div>
  )
}
