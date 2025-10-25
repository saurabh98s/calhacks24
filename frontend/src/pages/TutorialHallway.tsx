import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { GameCanvas } from '../components/GameCanvas'
import { useAuthStore } from '../store/authStore'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { GameScene } from '../game/GameScene'
import { apiService } from '../services/apiService'
import { Room } from '../types'

export default function TutorialHallway() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [scene, setScene] = useState<GameScene | null>(null)
  const [rooms, setRooms] = useState<Room[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadRooms()
  }, [])

  const loadRooms = async () => {
    try {
      const data = await apiService.getRooms()
      setRooms(data)
    } catch (error) {
      console.error('Failed to load rooms:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSceneReady = (gameScene: GameScene) => {
    console.log('Scene ready, setting up tutorial')
    setScene(gameScene)

    // Create doors for different room types
    const doors = [
      { x: 150, y: 300, type: 'study', label: 'STUDY\nGROUP' },
      { x: 300, y: 300, type: 'support', label: 'SUPPORT\nCIRCLE' },
      { x: 450, y: 300, type: 'casual', label: 'CASUAL\nLOUNGE' },
      { x: 600, y: 300, type: 'private', label: 'PRIVATE\nROOM' },
    ]

    gameScene.createDoors(doors)
    console.log('Doors created')

    // Listen for door clicks
    gameScene.events.on('door-clicked', (doorType: string) => {
      console.log('Door clicked event received:', doorType, 'Available rooms:', rooms)
      
      // Map door types to room types
      const roomTypeMap: { [key: string]: string[] } = {
        'study': ['study_group', 'study'],
        'support': ['support_circle', 'support'],
        'casual': ['casual_lounge', 'casual'],
        'private': ['private', 'private_room']
      }
      
      const possibleTypes = roomTypeMap[doorType] || [doorType]
      console.log('Looking for room types:', possibleTypes)
      
      // Find room of this type
      const room = rooms.find(r => possibleTypes.some(type => r.room_type === type || r.room_type.includes(type)))
      
      if (room) {
        console.log('Navigating to room:', room.room_id)
        navigate(`/room/${room.room_id}`)
      } else {
        console.log('No room found, using first available room')
        // If no rooms loaded yet, try to navigate anyway
        if (rooms.length === 0) {
          console.log('No rooms loaded, navigating to default')
          navigate(`/room/${doorType}_default`)
        } else {
          navigate(`/room/${rooms[0].room_id}`)
        }
      }
    })

    // Show welcome message
    setTimeout(() => {
      if (user) {
        gameScene.showSpeechBubble(
          user.id,
          "Welcome! I'm Atlas. Click on a door to enter a room!",
          5000
        )
      }
    }, 1000)
  }

  if (!user || loading) {
    return <LoadingSpinner message="Loading tutorial..." />
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <h1 className="text-4xl font-bold text-white mb-2">Tutorial Hallway</h1>
          <p className="text-gray-300">
            Choose a door to enter a room. Each room has a different vibe and AI personality!
          </p>
        </motion.div>

        {/* Game Canvas */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden shadow-2xl"
        >
          <GameCanvas
            roomId="tutorial_hallway"
            userId={user.id}
            username={user.username}
            avatarStyle={user.avatar_style}
            avatarColor={user.avatar_color}
            onMove={() => {}}
            onReady={handleSceneReady}
          />
        </motion.div>

        {/* Instructions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4"
        >
          <div className="bg-gray-800/50 backdrop-blur-sm rounded-lg border border-gray-700 p-4">
            <div className="text-3xl mb-2">🎓</div>
            <div className="text-white font-medium">Study Group</div>
            <div className="text-gray-400 text-sm">Collaborative learning</div>
          </div>
          <div className="bg-gray-800/50 backdrop-blur-sm rounded-lg border border-gray-700 p-4">
            <div className="text-3xl mb-2">🤝</div>
            <div className="text-white font-medium">Support Circle</div>
            <div className="text-gray-400 text-sm">Safe space for sharing</div>
          </div>
          <div className="bg-gray-800/50 backdrop-blur-sm rounded-lg border border-gray-700 p-4">
            <div className="text-3xl mb-2">🎮</div>
            <div className="text-white font-medium">Casual Lounge</div>
            <div className="text-gray-400 text-sm">Hang out and chill</div>
          </div>
          <div className="bg-gray-800/50 backdrop-blur-sm rounded-lg border border-gray-700 p-4">
            <div className="text-3xl mb-2">🏠</div>
            <div className="text-white font-medium">Private Room</div>
            <div className="text-gray-400 text-sm">Solo chat with AI</div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

