import { useState } from 'react'
import LandingPage from './components/LandingPage'
import Moderator from './components/Moderator'
import Dashboard from './components/Dashboard'
import TrainingDemo from './components/TrainingDemo'
import InstagramLive from './components/InstagramLive'

export default function App() {
  const [view, setView] = useState('landing')

  if (view === 'moderator') {
    return <Moderator onBack={() => setView('landing')} />
  }
  if (view === 'dashboard') {
    return <Dashboard onBack={() => setView('landing')} />
  }
  if (view === 'training') {
    return <TrainingDemo onBack={() => setView('landing')} />
  }
  if (view === 'instagram-live') {
    return <InstagramLive onBack={() => setView('landing')} />
  }
  return (
    <LandingPage
      onEnterApp={() => setView('moderator')}
      onEnterDashboard={() => setView('dashboard')}
      onEnterTraining={() => setView('training')}
      onEnterInstagramLive={() => setView('instagram-live')}
    />
  )
}
