import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { GameCanvas } from '../components/GameCanvas'
import { useAuthStore } from '../store/authStore'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { GameScene } from '../game/GameScene'
import { apiService } from '../services/apiService'
import { Room } from '../types'
import '../styles/retro-game.css'

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

  const [selectedRoom, setSelectedRoom] = useState<string | null>(null)

  const handleSceneReady = (gameScene: GameScene) => {
    console.log('Scene ready, setting up tutorial')
    setScene(gameScene)

    // Create doors for different room types - positioned for Mario-style walking
    const doors = [
      { x: 150, y: 300, type: 'study', label: '🎓' },
      { x: 300, y: 300, type: 'support', label: '🤝' },
      { x: 450, y: 300, type: 'casual', label: '🎮' },
      { x: 600, y: 300, type: 'private', label: '🏠' },
    ]

    gameScene.createDoors(doors)
    console.log('Doors created')

    // Listen for door clicks
    gameScene.events.on('door-clicked', (doorType: string) => {
      console.log('Door clicked event received:', doorType)
      handleDoorActivation(doorType, ['study_group', 'study'])
    })

    // Show welcome message with game instructions
    setTimeout(() => {
      if (user) {
        gameScene.showSpeechBubble(
          user.id,
          "🎮 Click a realm below, then walk to its door! 🎮",
          5000
        )
      }
    }, 1000)
  }

  const handleDoorActivation = (doorType: string, searchTypes: string[]) => {
    console.log('Door activated:', doorType, 'Looking for:', searchTypes)
    const room = rooms.find(r => searchTypes.some(type => r.room_type === type || r.room_type.includes(type)))
    
    if (room) {
      console.log('🎉 Entering room:', room.room_id)
      // Add a small delay for dramatic effect
      setTimeout(() => {
        navigate(`/room/${room.room_id}`)
      }, 500)
    } else {
      console.log('No room found, using default')
      setTimeout(() => {
        navigate(`/room/${doorType}_default`)
      }, 500)
    }
  }

  const handleRoomSelect = (roomType: string, searchTypes: string[], doorIndex: number) => {
    setSelectedRoom(roomType)
    console.log('🎯 Room selected:', roomType, 'Door index:', doorIndex)
    
    if (scene && user) {
      // Show instruction bubble
      scene.showSpeechBubble(
        user.id,
        `🚶 Walking to ${roomType.toUpperCase()} door...`,
        2000
      )

      // TODO: In future, make character actually walk to door
      // For now, activate after a short delay
      setTimeout(() => {
        if (scene && user) {
          scene.showSpeechBubble(
            user.id,
            `🎉 Entering ${roomType.toUpperCase()}!`,
            1500
          )
        }
        handleDoorActivation(roomType, searchTypes)
      }, 2000)
    } else {
      // Fallback if scene not ready
      handleDoorActivation(roomType, searchTypes)
    }
  }

  if (!user || loading) {
    return <LoadingSpinner message="Loading tutorial..." />
  }

  const roomTypes = [
    { 
      type: 'study', 
      icon: '🎓', 
      label: 'STUDY GROUP', 
      description: 'LEARN TOGETHER!',
      color: '#4ECDC4',
      searchTypes: ['study_group', 'study']
    },
    { 
      type: 'support', 
      icon: '🤝', 
      label: 'SUPPORT CIRCLE', 
      description: 'SHARE & CARE!',
      color: '#95E1D3',
      searchTypes: ['support_circle', 'support']
    },
    { 
      type: 'casual', 
      icon: '🎮', 
      label: 'CASUAL LOUNGE', 
      description: 'CHILL & CHAT!',
      color: '#FFE66D',
      searchTypes: ['casual_lounge', 'casual']
    },
    { 
      type: 'private', 
      icon: '🏠', 
      label: 'PRIVATE ROOM', 
      description: 'SOLO WITH AI!',
      color: '#AA96DA',
      searchTypes: ['private', 'private_room']
    },
  ]

  return (
    <div className="min-h-screen p-4" style={{
      background: 'linear-gradient(135deg, #4ECDC4 0%, #95E1D3 50%, #FFE66D 100%)',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Animated background */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundImage: `url("data:image/svg+xml,%3Csvg width='50' height='50' xmlns='http://www.w3.org/2000/svg'%3E%3Crect width='50' height='50' fill='rgba(255,255,255,0.05)'/%3E%3Crect x='20' y='20' width='10' height='10' fill='rgba(255,255,255,0.1)'/%3E%3C/svg%3E")`,
        animation: 'float 20s linear infinite',
      }} />

      <div className="pixel-container" style={{ maxWidth: '1200px', zIndex: 1 }}>
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          style={{ textAlign: 'center', marginBottom: '32px' }}
        >
          <h1 className="pixel-title" style={{
            fontSize: 'clamp(24px, 6vw, 42px)',
            color: '#FFF',
            textShadow: '6px 6px 0 #000'
          }}>
            🏰 CHOOSE YOUR REALM 🏰
          </h1>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="pixel-subtitle"
            style={{
              fontSize: 'clamp(10px, 2vw, 14px)',
              color: '#FFF',
              textShadow: '2px 2px 0 #000',
              marginTop: '16px'
            }}
          >
            🎮 CLICK A DOOR TO ENTER 🎮
            <br />
            ⚔️ EACH REALM HAS UNIQUE AI! ⚔️
          </motion.p>
        </motion.div>

        {/* Game Canvas */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 }}
          className="pixel-panel pixel-game-border"
          style={{
            background: '#000',
            padding: '8px',
            marginBottom: '32px'
          }}
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

        {/* Interactive Room Selection - Mario Style! */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '24px'
          }}
        >
          {roomTypes.map((room, index) => {
            const isSelected = selectedRoom === room.type
            const roomData = rooms.find(r => room.searchTypes.some(type => r.room_type === type || r.room_type.includes(type)))
            
            return (
              <motion.button
                key={room.type}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ 
                  opacity: 1, 
                  scale: isSelected ? 1.08 : 1,
                  y: isSelected ? -8 : 0
                }}
                transition={{ delay: 0.6 + index * 0.1, type: "spring", stiffness: 200 }}
                whileHover={{ scale: 1.05, y: -5 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => handleRoomSelect(room.type, room.searchTypes, index)}
                className="pixel-panel"
                style={{
                  padding: '24px',
                  background: isSelected ? room.color : '#FFF',
                  cursor: 'pointer',
                  textAlign: 'center',
                  position: 'relative',
                  overflow: 'hidden',
                  border: isSelected ? '6px solid #000' : '4px solid #000',
                  boxShadow: isSelected 
                    ? '8px 8px 0 #000, 0 0 0 4px ' + room.color 
                    : '4px 4px 0 #000'
                }}
              >
                {/* Animated background glow */}
                <motion.div
                  animate={{
                    opacity: isSelected ? [0.5, 0.8, 0.5] : [0.2, 0.4, 0.2]
                  }}
                  transition={{
                    duration: 1.5,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: room.color,
                    opacity: 0.2,
                    zIndex: 0
                  }}
                />

                {/* Selected indicator - Mario coin style */}
                {isSelected && (
                  <motion.div
                    initial={{ scale: 0, rotate: -180 }}
                    animate={{ 
                      scale: [1, 1.2, 1],
                      rotate: [0, 360]
                    }}
                    transition={{
                      scale: { duration: 0.5, repeat: Infinity },
                      rotate: { duration: 2, repeat: Infinity, ease: "linear" }
                    }}
                    style={{
                      position: 'absolute',
                      top: '-12px',
                      left: '50%',
                      transform: 'translateX(-50%)',
                      fontSize: '32px',
                      zIndex: 3
                    }}
                  >
                    🟡
                  </motion.div>
                )}
                
                {/* Content */}
                <div style={{ position: 'relative', zIndex: 1 }}>
                  <motion.div
                    animate={{
                      y: isSelected ? [0, -15, 0] : [0, -8, 0],
                      rotate: [0, 5, -5, 0]
                    }}
                    transition={{
                      duration: isSelected ? 0.8 : 2,
                      repeat: Infinity,
                      ease: "easeInOut"
                    }}
                    style={{
                      fontSize: 'clamp(48px, 10vw, 72px)',
                      marginBottom: '16px',
                      filter: isSelected ? 'drop-shadow(0 0 10px ' + room.color + ')' : 'none'
                    }}
                  >
                    {room.icon}
                  </motion.div>

                  <div style={{
                    fontFamily: 'Press Start 2P, cursive',
                    fontSize: 'clamp(10px, 2vw, 14px)',
                    color: isSelected ? (room.type === 'casual' ? '#000' : '#FFF') : '#000',
                    marginBottom: '12px',
                    lineHeight: '1.8',
                    textShadow: isSelected ? '2px 2px 0 #000' : 'none'
                  }}>
                    {room.label}
                  </div>

                  <div className="pixel-badge" style={{
                    display: 'inline-block',
                    padding: '6px 12px',
                    fontSize: 'clamp(8px, 1.5vw, 10px)',
                    background: isSelected ? '#FFE66D' : room.color,
                    color: '#000',
                    border: '2px solid #000',
                    animation: isSelected ? 'pulse 1s ease-in-out infinite' : 'none'
                  }}>
                    {isSelected ? '🎯 SELECTED!' : room.description}
                  </div>

                  {/* Player count */}
                  {roomData && (
                    <motion.div
                      animate={{ opacity: [0.7, 1, 0.7] }}
                      transition={{ duration: 2, repeat: Infinity }}
                      style={{
                        marginTop: '12px',
                        fontSize: 'clamp(8px, 1.5vw, 10px)',
                        fontFamily: 'Press Start 2P, cursive',
                        color: isSelected ? (room.type === 'casual' ? '#000' : '#FFF') : '#666'
                      }}
                    >
                      👥 {roomData.active_users_count || 0} ONLINE
                    </motion.div>
                  )}

                  {/* Game instruction when selected */}
                  {isSelected && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      style={{
                        marginTop: '12px',
                        fontSize: 'clamp(8px, 1.5vw, 10px)',
                        fontFamily: 'Press Start 2P, cursive',
                        color: room.type === 'casual' ? '#000' : '#FFF',
                        textShadow: '2px 2px 0 #000'
                      }}
                    >
                      🚶 WALKING...
                    </motion.div>
                  )}
                </div>

                {/* Animated corner sparkle */}
                <motion.div
                  animate={{
                    opacity: [0, 1, 0],
                    rotate: [0, 180, 360],
                    scale: isSelected ? [1, 1.5, 1] : 1
                  }}
                  transition={{
                    duration: isSelected ? 1 : 3,
                    repeat: Infinity,
                    delay: index * 0.5
                  }}
                  style={{
                    position: 'absolute',
                    top: '8px',
                    right: '8px',
                    fontSize: isSelected ? '24px' : '16px',
                    zIndex: 2
                  }}
                >
                  ⭐
                </motion.div>

                {/* Mario-style "?" block indicator */}
                {!isSelected && (
                  <motion.div
                    animate={{
                      y: [0, -5, 0]
                    }}
                    transition={{
                      duration: 1,
                      repeat: Infinity,
                      ease: "easeInOut"
                    }}
                    style={{
                      position: 'absolute',
                      bottom: '8px',
                      right: '8px',
                      fontSize: '20px',
                      opacity: 0.7
                    }}
                  >
                    ❓
                  </motion.div>
                )}
              </motion.button>
            )
          })}
        </motion.div>

        {/* Game Instructions - Mario Style */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1 }}
          className="pixel-panel"
          style={{
            marginTop: '32px',
            padding: '24px',
            background: 'rgba(255, 255, 255, 0.95)',
            border: '4px solid #000',
            boxShadow: '6px 6px 0 #000'
          }}
        >
          <div style={{
            textAlign: 'center',
            fontFamily: 'Press Start 2P, cursive'
          }}>
            <div style={{
              fontSize: 'clamp(10px, 2vw, 14px)',
              color: '#000',
              marginBottom: '16px'
            }}>
              🎮 HOW TO PLAY 🎮
            </div>
            
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '16px',
              fontSize: 'clamp(8px, 1.5vw, 10px)',
              lineHeight: '2'
            }}>
              <div style={{ color: '#4ECDC4' }}>
                1️⃣ CLICK A REALM
              </div>
              <div style={{ color: '#FF6B6B' }}>
                2️⃣ WATCH CHARACTER WALK
              </div>
              <div style={{ color: '#FFE66D' }}>
                3️⃣ ENTER THE DOOR
              </div>
              <div style={{ color: '#AA96DA' }}>
                4️⃣ MEET ATLAS AI!
              </div>
            </div>

            <motion.div
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 2, repeat: Infinity }}
              style={{
                marginTop: '16px',
                fontSize: 'clamp(8px, 1.5vw, 10px)',
                color: '#666'
              }}
            >
              ⭐ CLASSIC 8-BIT ADVENTURE AWAITS! ⭐
            </motion.div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

