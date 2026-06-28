import { useState } from 'react'

const schools = [
  {
    id: 'Georgia State University',
    name: 'Georgia State University',
    hint: 'PAWS → DegreeWorks → Print/Export as PDF',
    label: 'Select GSU',
    glowColor: 'rgba(0, 57, 166, 0.35)',
    borderColor: '#0039A6',
    accentColor: '#2997FF',
    icon: (
      <div style={{ width: 52, height: 52, borderRadius: 12, background: '#0039A6', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <span style={{ color: '#fff', fontSize: 26, fontWeight: 800, fontFamily: 'Georgia, serif', lineHeight: 1 }}>G</span>
      </div>
    ),
  },
  {
    id: 'Georgia Tech',
    name: 'Georgia Tech',
    label: 'Select Georgia Tech',
    hint: 'OSCAR → Student Services → DegreeWorks → Export as PDF',
    glowColor: 'rgba(179, 163, 105, 0.35)',
    borderColor: '#B3A369',
    accentColor: '#B3A369',
    icon: (
      <div style={{ width: 52, height: 52, borderRadius: 12, background: '#003057', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <span style={{ color: '#B3A369', fontSize: 26, fontWeight: 800, fontFamily: 'Georgia, serif', lineHeight: 1 }}>T</span>
      </div>
    ),
  },
]

export default function SchoolPicker({ onSelect }) {
  const [hovered, setHovered] = useState(null)

  return (
    <div className="min-h-screen bg-black flex flex-col items-center justify-center px-6 pt-12">
      <div className="max-w-2xl w-full mx-auto text-center">
        <p className="text-blue font-semibold text-sm tracking-widest uppercase mb-3">
          Step 1 of 3
        </p>
        <h1 className="text-5xl font-bold text-white tracking-tight mb-3">
          Select your school.
        </h1>
        <p className="text-gray mb-14">We support DegreeWorks from both schools.</p>

        <div className="grid md:grid-cols-2 gap-5">
          {schools.map((school) => {
            const isHovered = hovered === school.id
            return (
              <button
                key={school.id}
                onClick={() => onSelect(school.id)}
                onMouseEnter={() => setHovered(school.id)}
                onMouseLeave={() => setHovered(null)}
                style={{
                  borderColor: isHovered ? school.borderColor : 'rgba(255,255,255,0.08)',
                  boxShadow: isHovered ? `0 0 40px ${school.glowColor}, inset 0 0 40px ${school.glowColor}` : 'none',
                  transition: 'border-color 0.3s ease, box-shadow 0.3s ease, transform 0.2s ease',
                  transform: isHovered ? 'translateY(-4px)' : 'translateY(0)',
                }}
                className="bg-zinc rounded-3xl p-10 text-left border-2 active:scale-95"
              >
                <div className="mb-5">{school.icon}</div>

                <h2 className="text-xl font-bold text-white mb-2">{school.name}</h2>
                <p className="text-sm text-gray leading-relaxed mb-7">{school.hint}</p>

                <span
                  style={{ color: isHovered ? school.accentColor : '#2997FF' }}
                  className="inline-flex items-center gap-1.5 text-sm font-semibold transition-colors duration-300"
                >
                  {school.label}
                  <svg
                    className="w-4 h-4 transition-transform duration-200"
                    style={{ transform: isHovered ? 'translateX(4px)' : 'translateX(0)' }}
                    fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                  </svg>
                </span>
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}
