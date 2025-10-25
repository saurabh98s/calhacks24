import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowLeft, Users as UsersIcon } from 'lucide-react'

import { GameCanvas } from '../components/GameCanvas'
import { ChatPanel } from '../components/ChatPanel'
import { UserList } from '../components/UserList'
import { ActiveUsersPanel } from '../components/ActiveUsersPanel'
import { LoadingSpinner } from '../components/LoadingSpinner'

import { useAuthStore } from '../store/authStore'
import { useRoomStore } from '../store/roomStore'
import { useGameStore } from '../store/gameStore'

import { socketService } from '../services/socketService'
import { apiService } from '../services/apiService'
import { GameScene } from '../game/GameScene'
import { Position, Message } from '../types'
import '../styles/retro-game.css'

export default function GameRoom() {
  const { roomId } = useParams<{ roomId: string }>()
  const navigate = useNavigate()
  
  const { user, token } = useAuthStore()
  const { currentRoom, setCurrentRoom, messages, addMessage, setMessages, activeUsers, setActiveUsers, activeUsersMetadata, setActiveUsersMetadata, addUserMetadata, removeUserMetadata, addTypingUser, removeTypingUser, typingUsers } = useRoomStore()
  const { addAvatar, removeAvatar, updateAvatarPosition, clearAvatars } = useGameStore()
  
  const [scene, setScene] = useState<GameScene | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showUserList, setShowUserList] = useState(true)
  
  const socketInitialized = useRef(false)

  useEffect(() => {
    if (!user || !token || !roomId) {
      navigate('/avatar')
      return
    }

    // 🔄 CLEAR EVERYTHING ON MOUNT FOR FRESH START
    console.log('🔄 Clearing messages and users for fresh start')
    setMessages([])
    setActiveUsers([])
    setActiveUsersMetadata(new Map())
    clearAvatars()

    initializeRoom()

    return () => {
      cleanup()
    }
  }, [roomId, user, token])

  const initializeRoom = async () => {
    try {
      // Load room data
      const room = await apiService.getRoom(roomId!)
      setCurrentRoom(room)

      // Connect socket FIRST and wait for connection
      if (!socketInitialized.current) {
        const socket = socketService.connect(token!)
        
        // Wait for socket to connect
        await new Promise<void>((resolve, reject) => {
          const timeout = setTimeout(() => reject(new Error('Socket connection timeout')), 5000)

          if (socket.connected) {
            clearTimeout(timeout)
            resolve()
          } else {
            socket.once('connect', () => {
              clearTimeout(timeout)
              resolve()
            })
            socket.once('connect_error', (err: any) => {
              clearTimeout(timeout)
              reject(err)
            })
          }
        })

        // Setup socket listeners AFTER connection is established
        setupSocketListeners()
        socketInitialized.current = true
      }

      // Join room via socket
      socketService.joinRoom({
        room_id: roomId!,
        user_id: user!.id,
        username: user!.username,
        avatar_style: user!.avatar_style,
        avatar_color: user!.avatar_color,
      })

      setLoading(false)
    } catch (err: any) {
      console.error('Failed to initialize room:', err)
      setError(err.message || 'Failed to load room')
      setLoading(false)
    }
  }

  const setupSocketListeners = () => {
    // Room joined
    socketService.on('room_joined', (data: any) => {
      console.log('🔌 Room joined event received:', data)
      console.log('Active users:', data.active_users)
      console.log('Active users metadata:', data.active_users_metadata)
      
      // 🚫 DON'T LOAD OLD CONVERSATION HISTORY - FRESH START ONLY
      console.log('🚫 Skipping conversation history for fresh start')
      // Messages stay empty for fresh room experience
      
      // Build final active users list - ALWAYS include current user
      let finalActiveUsers: string[] = []
      
      if (data.active_users && Array.isArray(data.active_users)) {
        console.log('✅ Received active users from backend:', data.active_users)
        finalActiveUsers = [...data.active_users]
      } else {
        console.warn('⚠️ Received empty or invalid active_users array')
      }
      
      // CRITICAL: Ensure current user is in the list
      if (user && !finalActiveUsers.includes(user.id)) {
        console.log('✅ Current user NOT in backend list - adding:', user.id, user.username)
        finalActiveUsers.push(user.id)
      } else if (user) {
        console.log('✅ Current user already in backend list:', user.id, user.username)
      }
      
      console.log('📊 Final active users list:', finalActiveUsers)
      setActiveUsers(finalActiveUsers)
      
      // Store full user metadata
      if (data.active_users_metadata && Array.isArray(data.active_users_metadata)) {
        setActiveUsersMetadata(data.active_users_metadata)
        console.log('👥 Active users metadata stored:', data.active_users_metadata)
      }
      
      // CRITICAL: Ensure current user's metadata is available
      if (user) {
        const currentUserMetadata = {
          user_id: user.id,
          username: user.username,
          avatar_style: user.avatar_style,
          avatar_color: user.avatar_color,
          mood_icon: user.mood_icon
        }
        addUserMetadata(currentUserMetadata)
        console.log('✅ Added current user metadata:', currentUserMetadata)
      }
    })

    // User joined
    socketService.on('user_joined', (data: any) => {
      console.log('👋 User joined event received:', data)
      
      if (scene && data.user_id !== user!.id) {
        scene.addAvatar(
          data.user_id,
          data.username,
          data.avatar_style || 'human',
          data.avatar_color || 'blue',
          400,
          300
        )
      }
      
      // CRITICAL: Get CURRENT state from store, not captured closure value
      const currentActiveUsers = useRoomStore.getState().activeUsers
      console.log('📊 Current active users before adding:', currentActiveUsers)
      
      if (!currentActiveUsers.includes(data.user_id)) {
        console.log('➕ Adding new user to active users:', data.user_id, data.username)
        setActiveUsers([...currentActiveUsers, data.user_id])
      } else {
        console.log('✅ User already in active users:', data.user_id)
      }
      
      // Store user metadata
      addUserMetadata({
        user_id: data.user_id,
        username: data.username,
        avatar_style: data.avatar_style || 'human',
        avatar_color: data.avatar_color || 'blue',
        mood_icon: data.mood_icon
      })
    })

    // User left
    socketService.on('user_left', (data: any) => {
      console.log('👋 User left event received:', data)
      
      if (scene) {
        scene.removeAvatar(data.user_id)
      }
      
      // CRITICAL: Get CURRENT state from store, not captured closure value
      const currentActiveUsers = useRoomStore.getState().activeUsers
      console.log('📊 Current active users before removing:', currentActiveUsers)
      
      const updatedUsers = currentActiveUsers.filter((id: string) => id !== data.user_id)
      console.log('➖ Removing user from active users:', data.user_id)
      console.log('📊 Updated active users after removing:', updatedUsers)
      setActiveUsers(updatedUsers)
      removeUserMetadata(data.user_id)
    })

    // New message - CRITICAL: This must trigger UI update
    socketService.on('new_message', (message: Message) => {
      console.log('📨 Received new_message event:', message)
      
      const formattedMessage: Message = {
        message_id: message.message_id || `msg_${Date.now()}_${Math.random()}`,
        room_id: message.room_id || roomId || '',
        user_id: message.user_id,
        username: message.username || 'Unknown',
        content: message.content || message.message || '',
        message: message.message || message.content || '',
        message_type: message.message_type || 'user',
        timestamp: message.timestamp || new Date().toISOString(),
      }
      
      console.log('✅ Adding message to store:', formattedMessage.message_id)
      
      // Add message to store (will check for duplicates)
      addMessage(formattedMessage)
      
      // Show speech bubble in game
      if (scene) {
        const userId = formattedMessage.user_id || 'ai'
        scene.showSpeechBubble(userId, formattedMessage.message, 3000)
      }
    })

    // Avatar moved
    socketService.on('avatar_moved', (data: any) => {
      if (scene && data.user_id !== user!.id) {
        scene.updateAvatarPosition(data.user_id, data.position)
      }
    })

    // Typing indicator
    socketService.on('user_typing', (data: any) => {
      if (data.username !== user!.username) {
        if (data.is_typing) {
          addTypingUser(data.username)
        } else {
          removeTypingUser(data.username)
        }
      }
    })

    // Error
    socketService.on('error', (data: any) => {
      setError(data.message)
    })
  }

  const cleanup = () => {
    // Leave room
    if (roomId && user) {
      socketService.leaveRoom(roomId, user.id)
    }
    
    // Clean up local state
    clearAvatars()
    setMessages([])
    setCurrentRoom(null)
    
    // Mark as not initialized so listeners can be set up again on next mount
    socketInitialized.current = false
  }

  const handleMove = (position: Position) => {
    if (!socketService.isConnected() || !roomId) return

    socketService.moveAvatar({
      room_id: roomId,
      user_id: user!.id,
      position,
    })
  }

  const handleSendMessage = (message: string) => {
    if (!socketService.isConnected() || !roomId || !user) {
      console.error('Cannot send message: socket not connected or missing data')
      return
    }

    console.log('📤 Sending message:', message)

    // Send to server (server will broadcast to all including sender)
    socketService.sendMessage({
      room_id: roomId,
      user_id: user.id,
      username: user.username,
      message,
    })
  }

  const handleTyping = (isTyping: boolean) => {
    if (!socketService.isConnected() || !roomId) return

    socketService.sendTyping({
      room_id: roomId,
      username: user!.username,
      is_typing: isTyping,
    })
  }

  const handleSceneReady = (gameScene: GameScene) => {
    setScene(gameScene)
  }

  const handleBack = () => {
    navigate('/tutorial')
  }

  if (!user || loading) {
    return <LoadingSpinner message="Loading room..." />
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 flex items-center justify-center p-4">
        <div className="bg-gray-800 rounded-lg border border-red-500 p-8 max-w-md text-center">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-white mb-4">Error</h2>
          <p className="text-gray-300 mb-6">{error}</p>
          <button
            onClick={() => navigate('/tutorial')}
            className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
          >
            Back to Tutorial
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen overflow-hidden" style={{
      background: 'linear-gradient(135deg, #95E1D3 0%, #4ECDC4 50%, #AA96DA 100%)',
      position: 'relative'
    }}>
      {/* Animated pixel background */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundImage: `url("data:image/svg+xml,%3Csvg width='40' height='40' xmlns='http://www.w3.org/2000/svg'%3E%3Crect width='40' height='40' fill='rgba(255,255,255,0.05)'/%3E%3Crect x='15' y='15' width='10' height='10' fill='rgba(255,255,255,0.1)'/%3E%3C/svg%3E")`,
        animation: 'float 20s linear infinite',
        zIndex: 0
      }} />

      {/* Header */}
      <div className="h-16 relative z-10" style={{
        background: 'rgba(255, 255, 255, 0.95)',
        borderBottom: '4px solid #000',
        boxShadow: '0 4px 0 #000',
        display: 'flex',
        alignItems: 'center',
        padding: '0 24px'
      }}>
        <motion.button
          onClick={handleBack}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="pixel-btn"
          style={{
            padding: '8px 16px',
            fontSize: '10px',
            background: '#FF6B6B'
          }}
        >
          ← BACK
        </motion.button>
        
        <div style={{ flex: 1, textAlign: 'center' }}>
          <h1 className="pixel-title" style={{
            fontSize: 'clamp(16px, 3vw, 20px)',
            color: '#000',
            textShadow: '3px 3px 0 #4ECDC4',
            marginBottom: '4px'
          }}>
            🎮 {currentRoom?.name || 'GAME ROOM'} 🎮
          </h1>
          <p style={{
            fontSize: 'clamp(8px, 1.5vw, 10px)',
            color: '#666',
            fontFamily: 'Press Start 2P, cursive'
          }}>
            {currentRoom?.description}
          </p>
        </div>

        <motion.button
          onClick={() => setShowUserList(!showUserList)}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="pixel-btn md:hidden"
          style={{
            padding: '8px 16px',
            fontSize: '10px',
            background: '#FFE66D',
            color: '#000',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <UsersIcon className="w-4 h-4" />
          <span>{activeUsers.length}</span>
        </motion.button>
      </div>

      {/* Main Content */}
      <div className="relative z-10" style={{
        height: 'calc(100vh - 4rem)',
        display: 'grid',
        gridTemplateColumns: '1fr',
        gap: '16px',
        padding: '16px'
      }}>
        <style>{`
          @media (min-width: 768px) {
            .game-room-grid {
              grid-template-columns: minmax(250px, 1fr) minmax(0, 3fr) !important;
            }
          }
        `}</style>
        <div className="game-room-grid" style={{
          display: 'grid',
          gridTemplateColumns: '1fr',
          gap: '16px',
          height: '100%',
          overflow: 'hidden'
        }}>
          {/* Active Users Panel */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            style={{ height: '100%', overflow: 'hidden' }}
          >
            <div className="pixel-panel" style={{
              background: 'rgba(255, 255, 255, 0.95)',
              height: '100%',
              padding: '16px',
              display: 'flex',
              flexDirection: 'column'
            }}>
              <ActiveUsersPanel
                users={(() => {
                  console.log('🎨 Rendering ActiveUsersPanel')
                  console.log('   Active users array:', activeUsers)
                  console.log('   Metadata map size:', activeUsersMetadata.size)
                  console.log('   Current user:', user.id, user.username)
                  
                  const mappedUsers = activeUsers.map((userId: string) => {
                    // Get metadata from the map
                    const metadata = activeUsersMetadata.get(userId)
                    
                    const userObj = {
                      userId,
                      username: userId === user.id 
                        ? user.username 
                        : metadata?.username || messages.find((m: Message) => m.user_id === userId)?.username || 'User',
                      avatarColor: userId === user.id
                        ? user.avatar_color
                        : metadata?.avatar_color || 'blue',
                    }
                    
                    console.log(`   User ${userId}: ${userObj.username} (${userObj.avatarColor})`)
                    return userObj
                  })
                  
                  console.log('   Total users to display:', mappedUsers.length)
                  return mappedUsers
                })()}
                currentUserId={user.id}
              />
            </div>
          </motion.div>

          {/* Chat Panel */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            style={{ height: '100%', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}
          >
            <ChatPanel
              messages={messages}
              onSendMessage={handleSendMessage}
              onTyping={handleTyping}
              currentUsername={user.username}
              typingUsers={typingUsers}
            />
          </motion.div>
        </div>
      </div>
    </div>
  )
}

