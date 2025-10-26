import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { GameCanvas } from '../components/GameCanvas'
import { useAuthStore } from '../store/authStore'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { ModerationNotifications } from '../components/ModerationNotifications'
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
      { x: 150, y: 300, type: 'dnd', label: '🎲' },
      { x: 300, y: 300, type: 'aa', label: '🤝' },
      { x: 450, y: 300, type: 'therapy', label: '💚' },
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
      console.log('No room found for types:', searchTypes)
      // Fallback to first available room or private
      const fallbackRoom = rooms.find(r => r.room_type === 'private') || rooms[0]
      if (fallbackRoom) {
        navigate(`/room/${fallbackRoom.room_id}`)
      }
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
      type: 'dnd', 
      icon: '🎲', 
      label: 'DUNGEONS & DRAGONS', 
      description: 'EPIC ADVENTURE!',
      color: '#4ECDC4',
      searchTypes: ['dnd', 'dungeons']
    },
    { 
      type: 'aa', 
      icon: '🤝', 
      label: 'ALCOHOLICS ANONYMOUS', 
      description: 'SAFE RECOVERY!',
      color: '#95E1D3',
      searchTypes: ['alcoholics_anonymous', 'aa']
    },
    { 
      type: 'therapy', 
      icon: '💚', 
      label: 'GROUP THERAPY', 
      description: 'HEALING SPACE!',
      color: '#FFE66D',
      searchTypes: ['group_therapy', 'therapy']
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
    <div className="min-h-screen overflow-auto" style={{
      background: 'linear-gradient(135deg, #4ECDC4 0%, #95E1D3 50%, #FFE66D 100%)',
      position: 'relative'
    }}>
      {/* Animated background */}
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundImage: `url("data:image/svg+xml,%3Csvg width='50' height='50' xmlns='http://www.w3.org/2000/svg'%3E%3Crect width='50' height='50' fill='rgba(255,255,255,0.05)'/%3E%3Crect x='20' y='20' width='10' height='10' fill='rgba(255,255,255,0.1)'/%3E%3C/svg%3E")`,
        animation: 'float 20s linear infinite',
        zIndex: 0,
        pointerEvents: 'none'
      }} />

      <div style={{ 
        position: 'relative', 
        zIndex: 1,
        minHeight: '100vh',
        padding: '24px'
      }}>
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          style={{ textAlign: 'center', marginBottom: '24px' }}
        >
          <h1 className="pixel-title" style={{
            fontSize: 'clamp(20px, 5vw, 36px)',
            color: '#FFF',
            textShadow: '4px 4px 0 #000'
          }}>
            🏰 CHOOSE YOUR REALM 🏰
          </h1>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="pixel-subtitle"
            style={{
              fontSize: 'clamp(8px, 1.5vw, 12px)',
              color: '#FFF',
              textShadow: '2px 2px 0 #000',
              marginTop: '12px'
            }}
          >
            🎮 CLICK A DOOR TO ENTER 🎮
            <br />
            ⚔️ EACH REALM HAS UNIQUE AI! ⚔️
          </motion.p>
        </motion.div>

        {/* Main Layout: Sidebar + Canvas */}
        <div style={{
          display: 'flex',
          flexDirection: 'row',
          gap: '24px',
          maxWidth: '1400px',
          margin: '0 auto',
          alignItems: 'flex-start'
        }}>
          {/* Sidebar with Room Selection */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
            style={{
              width: '300px',
              flexShrink: 0,
              display: 'flex',
              flexDirection: 'column',
              gap: '16px'
            }}
          >
            {roomTypes.map((room, index) => {
              const isSelected = selectedRoom === room.type
              const roomData = rooms.find(r => room.searchTypes.some(type => r.room_type === type || r.room_type.includes(type)))
              
              return (
                <motion.button
                  key={room.type}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ 
                    opacity: 1, 
                    x: 0,
                    scale: isSelected ? 1.05 : 1
                  }}
                  transition={{ delay: 0.4 + index * 0.1, type: "spring" }}
                  whileHover={{ scale: 1.08 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => handleRoomSelect(room.type, room.searchTypes, index)}
                  className="pixel-panel"
                  style={{
                    padding: '16px',
                    background: isSelected ? room.color : '#FFF',
                    cursor: 'pointer',
                    textAlign: 'center',
                    position: 'relative',
                    overflow: 'hidden',
                    border: isSelected ? '4px solid #000' : '3px solid #000',
                    boxShadow: isSelected 
                      ? '6px 6px 0 #000' 
                      : '4px 4px 0 #000'
                  }}
                >
                  {/* Selected indicator */}
                  {isSelected && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ 
                        scale: [1, 1.2, 1],
                      }}
                      transition={{
                        duration: 0.6,
                        repeat: Infinity,
                      }}
                      style={{
                        position: 'absolute',
                        top: '-8px',
                        left: '50%',
                        transform: 'translateX(-50%)',
                        fontSize: '24px',
                        zIndex: 3
                      }}
                    >
                      ⭐
                    </motion.div>
                  )}
                  
                  {/* Content */}
                  <div style={{ position: 'relative', zIndex: 1 }}>
                    <motion.div
                      animate={{
                        y: isSelected ? [0, -8, 0] : [0, -4, 0],
                      }}
                      transition={{
                        duration: isSelected ? 0.8 : 1.5,
                        repeat: Infinity,
                        ease: "easeInOut"
                      }}
                      style={{
                        fontSize: '48px',
                        marginBottom: '12px',
                        filter: isSelected ? 'drop-shadow(0 0 8px ' + room.color + ')' : 'none'
                      }}
                    >
                      {room.icon}
                    </motion.div>

                    <div style={{
                      fontFamily: 'Press Start 2P, cursive',
                      fontSize: '10px',
                      color: isSelected ? (room.type === 'therapy' ? '#000' : '#FFF') : '#000',
                      marginBottom: '8px',
                      lineHeight: '1.6',
                      textShadow: isSelected ? '2px 2px 0 #000' : 'none'
                    }}>
                      {room.label}
                    </div>

                    <div className="pixel-badge" style={{
                      display: 'inline-block',
                      padding: '4px 8px',
                      fontSize: '8px',
                      background: isSelected ? '#FFE66D' : room.color,
                      color: '#000',
                      border: '2px solid #000',
                    }}>
                      {isSelected ? '✓ READY' : room.description}
                    </div>

                    {/* Player count */}
                    {roomData && (
                      <div style={{
                        marginTop: '8px',
                        fontSize: '8px',
                        fontFamily: 'Press Start 2P, cursive',
                        color: isSelected ? (room.type === 'therapy' ? '#000' : '#FFF') : '#666'
                      }}>
                        👥 {roomData.active_users_count || 0} ONLINE
                      </div>
                    )}
                  </div>
                </motion.button>
              )
            })}
          </motion.div>

          {/* Game Canvas - Center/Right */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.4 }}
            className="pixel-panel pixel-game-border"
            style={{
              flex: 1,
              background: '#000',
              padding: '8px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              minHeight: '600px',
              maxHeight: '600px',
              overflow: 'hidden',
              position: 'relative',
              contain: 'layout style paint'
            }}
          >
            <div style={{
              width: '100%',
              height: '100%',
              overflow: 'hidden',
              position: 'relative',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <GameCanvas
                roomId="tutorial_hallway"
                userId={user.id}
                username={user.username}
                avatarStyle={user.avatar_style}
                avatarColor={user.avatar_color}
                onMove={() => {}}
                onReady={handleSceneReady}
              />
            </div>
          </motion.div>
        </div>

        {/* Game Instructions */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="pixel-panel"
          style={{
            marginTop: '24px',
            padding: '20px',
            background: 'rgba(255, 255, 255, 0.95)',
            border: '4px solid #000',
            boxShadow: '4px 4px 0 #000',
            maxWidth: '1400px',
            margin: '24px auto 0'
          }}
        >
          <div style={{
            textAlign: 'center',
            fontFamily: 'Press Start 2P, cursive'
          }}>
            <div style={{
              fontSize: 'clamp(10px, 2vw, 12px)',
              color: '#000',
              marginBottom: '16px'
            }}>
              🎮 HOW TO PLAY 🎮
            </div>
            
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
              gap: '12px',
              fontSize: 'clamp(7px, 1.5vw, 9px)',
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
                marginTop: '12px',
                fontSize: 'clamp(7px, 1.5vw, 9px)',
                color: '#666'
              }}
            >
              ⭐ CLASSIC 8-BIT ADVENTURE AWAITS! ⭐
            </motion.div>
          </div>
        </motion.div>
      </div>

      {/* Multi-Agent Moderation Notifications */}
      <ModerationNotifications />
    </div>
  )
}

