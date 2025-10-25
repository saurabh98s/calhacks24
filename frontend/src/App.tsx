import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Landing from './pages/Landing'
import AvatarCreation from './pages/AvatarCreation'
import TutorialHallway from './pages/TutorialHallway'
import GameRoom from './pages/GameRoom'
import { useAuthStore } from './store/authStore'

function App() {
  const { isAuthenticated } = useAuthStore()

  return (
    <Router>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/avatar" element={<AvatarCreation />} />
        <Route 
          path="/tutorial" 
          element={isAuthenticated ? <TutorialHallway /> : <Navigate to="/avatar" />} 
        />
        <Route 
          path="/room/:roomId" 
          element={isAuthenticated ? <GameRoom /> : <Navigate to="/avatar" />} 
        />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  )
}

export default App

