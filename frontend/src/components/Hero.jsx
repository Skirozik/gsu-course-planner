export default function Hero({ onStart }) {
  return (
    <div className="pt-12 bg-black">
      {/* Hero — full viewport, black bg */}
      <section className="relative overflow-hidden min-h-screen flex flex-col items-center justify-center text-center px-6">
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[400px] rounded-full blur-3xl pointer-events-none"
          style={{ background: 'radial-gradient(ellipse, rgba(41,151,255,0.12) 0%, transparent 70%)' }} />

        <p className="text-blue font-semibold text-sm tracking-widest uppercase mb-5 relative z-10">
          Academic Planner
        </p>
        <h1 className="text-6xl md:text-7xl font-bold text-white tracking-tight leading-none mb-4 relative z-10">
          Plan smarter.
        </h1>
        <h1 className="text-6xl md:text-7xl font-bold text-blue tracking-tight leading-none mb-8 relative z-10">
          Graduate on time.
        </h1>
        <p className="text-lg text-gray max-w-xl mx-auto mb-10 leading-relaxed relative z-10">
          Upload your DegreeWorks transcript and get AI-powered course recommendations
          with real professor ratings | For GSU and Georgia Tech.
        </p>

        <div className="flex flex-col sm:flex-row items-center gap-4 relative z-10">
          <button
            onClick={onStart}
            className="bg-blue text-white px-8 py-3 rounded-full text-sm font-semibold active:scale-95"
            style={{ transition: 'box-shadow 0.3s ease, transform 0.15s ease' }}
            onMouseEnter={e => e.currentTarget.style.boxShadow = '0 0 30px rgba(41,151,255,0.45)'}
            onMouseLeave={e => e.currentTarget.style.boxShadow = 'none'}
          >
            Start planning
          </button>
          <a
            href="https://github.com/Skirozik/multischool-course-planner"
            target="_blank"
            rel="noopener noreferrer"
            className="text-white text-sm font-semibold px-8 py-3 rounded-full border border-white/30 hover:border-white/60 transition-all active:scale-95"
          >
            View on GitHub ↗
          </a>
        </div>

        <div className="absolute bottom-10 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 text-gray text-xs z-10">
          <span>Scroll to learn more</span>
          <svg className="w-4 h-4 animate-bounce" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </section>

      {/* Feature grid — zinc (#101010) section */}
      <section className="bg-zinc py-24 border-t border-white/10">
        <div className="max-w-5xl mx-auto px-6">
          <h2 className="text-4xl font-bold text-white tracking-tight text-center mb-4">
            Everything you need to register with confidence.
          </h2>
          <p className="text-gray text-center mb-16 max-w-xl mx-auto">
            No more cross-checking the catalog, the prerequisites, and Rate My Professor in five tabs.
          </p>
          <div className="grid md:grid-cols-3 gap-4">
            {[
              { icon: (<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M7 3h7l4 4v14H7z" strokeLinejoin="round"/><path d="M14 3v4h4M9.5 12h5M9.5 15.5h5" strokeLinecap="round"/></svg>), title: 'Reads your evaluation', desc: 'Upload your DegreeWorks PDF and it pulls your completed courses and remaining requirements automatically.' },
              { icon: (<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="5" y="5" width="14" height="14" rx="2"/><path d="M9 9h6v6H9z M12 2v3M12 19v3M2 12h3M19 12h3" strokeLinecap="round"/></svg>), title: 'Recommends what to take', desc: 'An AI advisor suggests your next semester and explains the reasoning in plain language.' },
              { icon: (<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M12 4l2.3 4.7 5.2.8-3.75 3.65.9 5.15L12 15.9 7.15 18.3l.9-5.15L4.3 9.5l5.2-.8z" strokeLinejoin="round"/></svg>), title: 'Ranks the professors', desc: 'Every recommendation includes live Rate My Professor data, so you choose the right section.' },
              { icon: (<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="6" cy="7" r="2.4"/><circle cx="18" cy="7" r="2.4"/><circle cx="12" cy="17" r="2.4"/><path d="M8 8.5l3 6.5M16 8.5l-3 6.5" strokeLinecap="round"/></svg>), title: 'Maps prerequisites', desc: 'See which courses unlock the ones you want, and plan several semesters ahead.' },
              { icon: (<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M12 3v11m0 0l-4-4m4 4l4-4M5 20h14" strokeLinecap="round" strokeLinejoin="round"/></svg>), title: 'Exports anywhere', desc: 'Download your plan as a PDF, or add it straight to Google or Apple Calendar.' },
              { icon: (<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M4 20V9l8-5 8 5v11" strokeLinejoin="round"/><path d="M4 20h16M10 20v-5h4v5" strokeLinecap="round"/></svg>), title: 'Two schools', desc: 'Full support for both Georgia State and Georgia Tech DegreeWorks formats.' },
            ].map((f) => (
              <div
                key={f.title}
                className="rounded-2xl p-7 border border-white/10 hover:border-white/20 transition-all"
                style={{ background: '#242424' }}
              >
                <div className="mb-4" style={{ color: '#2997FF' }}>{f.icon}</div>
                <h3 className="text-white font-semibold mb-2 text-base">{f.title}</h3>
                <p className="text-gray text-sm leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA — back to black */}
      <section className="bg-black py-24 border-t border-white/10 text-center">
        <div className="max-w-2xl mx-auto px-6">
          <h2 className="text-4xl font-bold text-white tracking-tight mb-4">
            Start with your DegreeWorks PDF.
          </h2>
          <p className="text-gray mb-10">It takes about two minutes, and you don't need an account.</p>
          <button
            onClick={onStart}
            className="bg-blue text-white px-10 py-3.5 rounded-full text-sm font-semibold hover:shadow-glow transition-all active:scale-95"
          >
            Start planning
          </button>
        </div>
      </section>

      <footer className="bg-zinc border-t border-white/10 py-8 text-center text-xs text-gray">
        Not affiliated with Georgia State University or Georgia Tech. Always verify plans with your academic advisor.
      </footer>
    </div>
  )
}
