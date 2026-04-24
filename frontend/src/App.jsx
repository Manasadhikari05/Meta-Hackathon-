import { useState } from 'react'
import LandingPage from './components/LandingPage'
import Moderator from './components/Moderator'

export default function App() {
  const [view, setView] = useState('landing')

  if (view === 'moderator') {
    return <Moderator onBack={() => setView('landing')} />
  }
  return <LandingPage onEnterApp={() => setView('moderator')} />
}
