import { useState } from 'react'
import LandingPage from './components/LandingPage'
import Moderator from './components/Moderator'
import Dashboard from './components/Dashboard'
import LiveDiscord from './components/LiveDiscord'

export default function App() {
  const [view, setView] = useState('landing')

  if (view === 'moderator') {
    return <Moderator onBack={() => setView('landing')} />
  }
  if (view === 'dashboard') {
    return <Dashboard onBack={() => setView('landing')} />
  }
  if (view === 'liveDiscord') {
    return <LiveDiscord onBack={() => setView('landing')} />
  }
  return (
    <LandingPage
      onEnterApp={() => setView('moderator')}
      onEnterDashboard={() => setView('dashboard')}
      onEnterLiveDiscord={() => setView('liveDiscord')}
    />
  )
}
