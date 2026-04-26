import { useState } from 'react'
import LandingPage from './components/LandingPage'
import Moderator from './components/Moderator'
import Dashboard from './components/Dashboard'
import LiveDiscord from './components/LiveDiscord'
import MemeMod from './components/MemeMod'
import TrainingMetrics from './components/TrainingMetrics'

export default function App() {
  const [view, setView] = useState('landing')

  if (view === 'moderator') {
    return <Moderator onBack={() => setView('landing')} />
  }
  if (view === 'dashboard') {
    return (
      <Dashboard
        onBack={() => setView('landing')}
        onTrainingMetrics={() => setView('trainingMetrics')}
      />
    )
  }
  if (view === 'liveDiscord') {
    return <LiveDiscord onBack={() => setView('landing')} />
  }
  if (view === 'memeMod') {
    return <MemeMod onBack={() => setView('landing')} />
  }
  if (view === 'trainingMetrics') {
    return <TrainingMetrics onBack={() => setView('landing')} />
  }
  return (
    <LandingPage
      onEnterApp={() => setView('moderator')}
      onEnterDashboard={() => setView('dashboard')}
      onEnterLiveDiscord={() => setView('liveDiscord')}
      onEnterMemeMod={() => setView('memeMod')}
      onEnterTrainingMetrics={() => setView('trainingMetrics')}
    />
  )
}
