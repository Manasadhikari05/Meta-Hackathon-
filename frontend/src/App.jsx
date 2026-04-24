import { useState } from 'react'
import LandingPage from './components/LandingPage'
import Dashboard from './components/Dashboard'

export default function App() {
  const [view, setView] = useState('landing')

  if (view === 'dashboard') {
    return <Dashboard onBack={() => setView('landing')} />
  }
  return <LandingPage onEnterApp={() => setView('dashboard')} />
}
