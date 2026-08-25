import { useState, useCallback, useEffect } from 'react'
import { useDropzone } from 'react-dropzone'
import api, { describeError } from '../api'

const SCHOOL_COLOR = {
  'Georgia State University': '#2997FF',
  'Georgia Tech': '#B3A369',
}

const MAX_UPLOAD_BYTES = 10 * 1024 * 1024

export default function TranscriptUpload({ school, onUpload, onBack }) {
  const [status, setStatus] = useState('idle')
  const [error, setError] = useState(null)
  const [attempt, setAttempt] = useState(0)

  const accentColor = SCHOOL_COLOR[school] ?? '#2997FF'

  // Inject keyframe animation once
  useEffect(() => {
    const id = 'upload-pulse-style'
    if (document.getElementById(id)) return
    const style = document.createElement('style')
    style.id = id
    style.textContent = `
      @keyframes border-pulse {
        0%, 100% { box-shadow: 0 0 0 0 var(--pulse-color, rgba(41,151,255,0)); }
        50%       { box-shadow: 0 0 24px 4px var(--pulse-color, rgba(41,151,255,0.25)); }
      }
      .upload-pulse {
        animation: border-pulse 2.4s ease-in-out infinite;
      }
    `
    document.head.appendChild(style)
  }, [])

  const onDrop = useCallback(async (files, rejections) => {
    // Without this, a rejected file silently does nothing and the page looks frozen.
    if (rejections?.length) {
      const code = rejections[0].errors?.[0]?.code
      setStatus('error')
      setError(
        code === 'file-too-large'
          ? 'That PDF is larger than 10 MB. Re-export just the DegreeWorks audit page.'
          : 'That file is not a PDF. Export your DegreeWorks audit as a PDF and try again.'
      )
      return
    }

    const file = files[0]
    if (!file) return
    setStatus('parsing')
    setError(null)
    setAttempt(0)
    const form = new FormData()
    form.append('file', file)
    try {
      const { data } = await api.post(
        `/api/parse-transcript?school=${encodeURIComponent(school)}`,
        form,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
          // Fired by the retry interceptor when the backend is still waking.
          onRetry: (n) => {
            setStatus('waking')
            setAttempt(n)
          },
        }
      )
      onUpload(data.data)
    } catch (err) {
      setStatus('error')
      setError(
        describeError(
          err,
          'Failed to parse transcript. Make sure you uploaded the correct DegreeWorks PDF.'
        )
      )
    }
  }, [school, onUpload])

  const busy = status === 'parsing' || status === 'waking'

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
    maxSize: MAX_UPLOAD_BYTES,
    disabled: busy,
  })

  // pulse color as CSS variable
  const pulseRgb = school === 'Georgia Tech'
    ? 'rgba(179,163,105,0.3)'
    : 'rgba(41,151,255,0.25)'

  return (
    <div className="min-h-screen bg-black flex flex-col items-center justify-center px-6 pt-12">
      <div className="max-w-xl w-full mx-auto">
        <button
          onClick={onBack}
          className="flex items-center gap-1.5 text-sm mb-8 hover:opacity-70 transition-opacity"
          style={{ color: accentColor }}
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          Back
        </button>

        <p className="font-semibold text-sm tracking-widest uppercase mb-3" style={{ color: accentColor }}>
          Step 2 of 3
        </p>
        <h1 className="text-5xl font-bold text-white tracking-tight mb-2">
          Upload your transcript.
        </h1>
        <p className="text-gray mb-10">
          Your <strong className="text-white">{school}</strong> DegreeWorks PDF
        </p>

        {/* Drop zone with pulsing border */}
        <div
          {...getRootProps()}
          className={`upload-pulse border-2 border-dashed rounded-3xl p-16 text-center cursor-pointer transition-all duration-300
            ${busy ? 'pointer-events-none opacity-50' : ''}
          `}
          style={{
            '--pulse-color': pulseRgb,
            borderColor: isDragActive ? accentColor : `${accentColor}40`,
            background: isDragActive ? `${accentColor}08` : '#101010',
          }}
        >
          <input {...getInputProps()} />
          {busy ? (
            <div className="flex flex-col items-center gap-4">
              <div
                className="w-10 h-10 border-2 border-t-transparent rounded-full animate-spin"
                style={{ borderColor: `${accentColor} transparent transparent transparent` }}
              />
              <p className="text-gray font-medium">
                {status === 'waking'
                  ? `Waking the server — this can take up to a minute… (attempt ${attempt})`
                  : 'Parsing your transcript…'}
              </p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3">
              {/* PDF icon with school accent */}
              <svg className="w-14 h-14 mb-1" viewBox="0 0 56 56" fill="none">
                <rect x="8" y="4" width="32" height="40" rx="4" fill="#1c1c1e" stroke={`${accentColor}60`} strokeWidth="1.5"/>
                <rect x="24" y="4" width="16" height="14" rx="2" fill={`${accentColor}20`} stroke={`${accentColor}60`} strokeWidth="1.5"/>
                <line x1="14" y1="24" x2="34" y2="24" stroke={`${accentColor}80`} strokeWidth="1.5" strokeLinecap="round"/>
                <line x1="14" y1="30" x2="34" y2="30" stroke={`${accentColor}50`} strokeWidth="1.5" strokeLinecap="round"/>
                <line x1="14" y1="36" x2="26" y2="36" stroke={`${accentColor}50`} strokeWidth="1.5" strokeLinecap="round"/>
              </svg>

              <p className="text-white font-semibold text-lg">
                {isDragActive ? 'Drop it here' : 'Drag & drop your PDF'}
              </p>
              <p className="text-sm text-gray">or click to browse</p>
              <span
                className="mt-2 inline-block px-4 py-1.5 rounded-full text-xs font-medium border"
                style={{ color: accentColor, borderColor: `${accentColor}30`, background: `${accentColor}08` }}
              >
                PDF only · Max 10 MB
              </span>
            </div>
          )}
        </div>

        {error && (
          <div className="mt-6 rounded-2xl p-5"
            style={{ background: 'rgba(255,59,48,0.08)', border: '1px solid rgba(255,59,48,0.2)' }}>
            <p className="text-sm" style={{ color: '#ff6b6b' }}>{error}</p>
          </div>
        )}

        <div className="mt-6 bg-zinc border border-white/10 rounded-2xl p-5">
          <p className="text-xs text-gray leading-relaxed">
            <strong className="text-white">How to export from {school}:</strong>{' '}
            {school === 'Georgia Tech'
              ? 'OSCAR → Student Services → Degree Works → Print → Save as PDF'
              : 'PAWS → Student tab → DegreeWorks → Print/Export → Save as PDF'}
          </p>
        </div>
      </div>
    </div>
  )
}
