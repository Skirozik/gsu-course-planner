export default function Navbar({ onReset, step }) {
  const steps = ['school', 'upload', 'prefs', 'results']
  const labels = ['School', 'Transcript', 'Preferences', 'Results']
  const currentIdx = steps.indexOf(step)

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-black/80 backdrop-blur-xl border-b-2 border-white/10">
      <div className="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
        <button
          onClick={onReset}
          className="text-white text-base font-semibold tracking-tight hover:opacity-70 transition-opacity"
        >
          PrereqPilot
        </button>

        {step !== 'home' && (
          <div className="flex items-center gap-1 text-sm text-gray">
            {steps.map((s, i) => (
              <span key={s} className="flex items-center gap-1">
                <span className={`${i === currentIdx ? 'text-blue font-medium' : i < currentIdx ? 'text-gray' : 'text-white/20'}`}>
                  {labels[i]}
                </span>
                {i < 3 && <span className="text-white/20 mx-1">›</span>}
              </span>
            ))}
          </div>
        )}

        <a
          href="https://github.com/Skirozik/multischool-course-planner"
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-gray hover:text-white transition-colors"
        >
          GitHub ↗
        </a>
      </div>
    </nav>
  )
}
