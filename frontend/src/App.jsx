import { useState } from 'react'
import Hero from './components/Hero.jsx'
import SchoolPicker from './components/SchoolPicker.jsx'
import TranscriptUpload from './components/TranscriptUpload.jsx'
import PreferencesForm from './components/PreferencesForm.jsx'
import Results from './components/Results.jsx'
import Navbar from './components/Navbar.jsx'

export default function App() {
  const [step, setStep] = useState('home') // home | school | upload | prefs | results
  const [school, setSchool] = useState(null)
  const [evalData, setEvalData] = useState(null)
  const [results, setResults] = useState(null)

  function handleStart() {
    setStep('school')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function handleSchool(s) {
    setSchool(s)
    setStep('upload')
  }

  function handleTranscript(data) {
    setEvalData(data)
    setStep('prefs')
  }

  function handleResults(data) {
    setResults(data)
    setStep('results')
  }

  function handleReset() {
    setStep('home')
    setSchool(null)
    setEvalData(null)
    setResults(null)
  }

  return (
    <div className="min-h-screen bg-apple-light">
      <Navbar onReset={handleReset} step={step} />

      {step === 'home' && <Hero onStart={handleStart} />}
      {step === 'school' && <SchoolPicker onSelect={handleSchool} />}
      {step === 'upload' && (
        <TranscriptUpload school={school} onUpload={handleTranscript} onBack={() => setStep('school')} />
      )}
      {step === 'prefs' && (
        <PreferencesForm
          school={school}
          evalData={evalData}
          onResults={handleResults}
          onBack={() => setStep('upload')}
        />
      )}
      {step === 'results' && (
        <Results results={results} evalData={evalData} onReset={handleReset} school={school} />
      )}
    </div>
  )
}
