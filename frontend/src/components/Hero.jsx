export default function Hero({ onStart }) {
  return (
    <div className="pt-12 bg-black">
      {/* Hero — full viewport, black bg */}
      <section className="relative overflow-hidden min-h-screen flex flex-col items-center justify-center text-center px-6">
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[400px] rounded-full blur-3xl pointer-events-none"
          style={{ background: 'radial-gradient(ellipse, rgba(41,151,255,0.12) 0%, transparent 70%)' }} />

        <p className="text-blue font-semibold text-sm tracking-widest uppercase mb-5 relative z-10">
          AI-Powered Academic Planning
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
            Get started
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
            Built for serious students.
          </h2>
          <p className="text-gray text-center mb-16 max-w-xl mx-auto">
            Every feature designed to save time and remove the guesswork from registration.
          </p>
          <div className="grid md:grid-cols-3 gap-4">
            {[
              { icon: '📄', title: 'Transcript Analysis', desc: 'Upload your DegreeWorks PDF and we extract completed courses and requirements automatically.' },
              { icon: '🤖', title: 'Claude AI', desc: "Powered by Anthropic's Claude — the same AI behind claude.ai — for intelligent recommendations." },
              { icon: '⭐', title: 'Professor Ratings', desc: 'Every recommendation includes live Rate My Professor data so you pick the right section.' },
              { icon: '🗺️', title: 'Prerequisite Map', desc: 'See which courses unlock future ones and plan multiple semesters ahead.' },
              { icon: '📅', title: 'Export Anywhere', desc: 'Download as PDF or .ics to import straight into Google Calendar or Apple Calendar.' },
              { icon: '🏫', title: 'GSU & Georgia Tech', desc: "Full support for both schools' DegreeWorks PDF formats." },
            ].map((f) => (
              <div
                key={f.title}
                className="rounded-2xl p-7 border border-white/10 hover:border-white/20 transition-all"
                style={{ background: '#242424' }}
              >
                <div className="text-3xl mb-4">{f.icon}</div>
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
            Ready to plan your semester?
          </h2>
          <p className="text-gray mb-10">Takes less than 2 minutes. No account required.</p>
          <button
            onClick={onStart}
            className="bg-blue text-white px-10 py-3.5 rounded-full text-sm font-semibold hover:shadow-glow transition-all active:scale-95"
          >
            Start planning →
          </button>
        </div>
      </section>

      <footer className="bg-zinc border-t border-white/10 py-8 text-center text-xs text-gray">
        Not affiliated with Georgia State University or Georgia Tech. Always verify plans with your academic advisor.
      </footer>
    </div>
  )
}
