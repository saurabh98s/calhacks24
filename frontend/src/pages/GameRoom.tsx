import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowLeft, Users as UsersIcon } from 'lucide-react'

import { GameCanvas } from '../components/GameCanvas'
import { ChatPanel } from '../components/ChatPanel'
import { UserList } from '../components/UserList'
import { LoadingSpinner } from '../components/LoadingSpinner'

import { useAuthStore } from '../store/authStore'
import { useRoomStore } from '../store/roomStore'
import { useGameStore } from '../store/gameStore'

import { socketService } from '../services/socketService'
import { apiService } from '../services/apiService'
import { GameScene } from '../game/GameScene'
import { Position, Message } from '../types'

export default function GameRoom() {
  const { roomId } = useParams<{ roomId: string }>()
  const navigate = useNavigate()
  
  const { user, token } = useAuthStore()
  const { currentRoom, setCurrentRoom, messages, addMessage, setMessages, activeUsers, setActiveUsers } = useRoomStore()
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

    initializeRoom()

    return () => {
      cleanup()
    }
  }, [roomId, user, token])

  const initializeRoom = async () => {
    try {
      console.log('🚀 Initializing room:', roomId)
      
      // Load room data
      const room = await apiService.getRoom(roomId!)
      console.log('✅ Room loaded:', room)
      setCurrentRoom(room)

      // Connect socket and wait for connection
      if (!socketInitialized.current) {
        console.log('🔌 Connecting to WebSocket...')
        const socket = socketService.connect(token!)
        
        // Wait for socket to connect
        await new Promise<void>((resolve, reject) => {
          const timeout = setTimeout(() => {
            reject(new Error('Socket connection timeout'))
          }, 5000)

          socket.on('connect', () => {
            console.log('✅ Socket connected')
            clearTimeout(timeout)
            resolve()
          })

          socket.on('connect_error', (err: any) => {
            console.error('❌ Socket connection error:', err)
            clearTimeout(timeout)
            reject(err)
          })

          // If already connected, resolve immediately
          if (socket.connected) {
            console.log('✅ Socket already connected')
            clearTimeout(timeout)
            resolve()
          }
        })

        setupSocketListeners()
        socketInitialized.current = true
      }

      // Small delay to ensure socket is ready
      await new Promise(resolve => setTimeout(resolve, 500))

      // Join room via socket
      console.log('🚪 Joining room via socket...')
      socketService.joinRoom({
        room_id: roomId!,
        user_id: user!.id,
        username: user!.username,
        avatar_style: user!.avatar_style,
        avatar_color: user!.avatar_color,
      })

      setLoading(false)
    } catch (err: any) {
      console.error('❌ Failed to initialize room:', err)
      setError(err.message || 'Failed to load room')
      setLoading(false)
    }
  }

  const setupSocketListeners = () => {
    // Connection events
    socketService.on('connect', () => {
      console.log('✅ Connected to server')
    })

    socketService.on('disconnect', () => {
      console.log('❌ Disconnected from server')
    })

    // Room joined
    socketService.on('room_joined', (data: any) => {
      console.log('🚪 Joined room:', data)
      
      // Load conversation history
      if (data.conversation_history) {
        setMessages(data.conversation_history)
      }
      
      // Set active users
      if (data.active_users) {
        setActiveUsers(data.active_users)
      }
    })

    // User joined
    socketService.on('user_joined', (data: any) => {
      console.log('👤 User joined:', data)
      
      // Add avatar to game
      if (scene && data.user_id !== user!.id) {
        scene.addAvatar(
          data.user_id,
          data.username,
          data.avatar_style,
          data.avatar_color,
          400,
          300
        )
      }
      
      // Update active users list
      setActiveUsers([...activeUsers, data.user_id])
    })

    // User left
    socketService.on('user_left', (data: any) => {
      console.log('👋 User left:', data)
      
      // Remove avatar from game
      if (scene) {
        scene.removeAvatar(data.user_id)
      }
      
      // Update active users list
      setActiveUsers(activeUsers.filter(id => id !== data.user_id))
    })

    // New message
    socketService.on('new_message', (message: Message) => {
      console.log('💬 New message:', message)
      addMessage(message)
      
      // Show speech bubble in game
      if (scene) {
        const content = message.message || message.content || ''
        scene.showSpeechBubble(message.user_id || 'ai', content, 3000)
      }
    })

    // Avatar moved
    socketService.on('avatar_moved', (data: any) => {
      if (scene && data.user_id !== user!.id) {
        scene.updateAvatarPosition(data.user_id, data.position)
      }
    })

    // Error
    socketService.on('error', (data: any) => {
      console.error('Socket error:', data)
      setError(data.message)
    })
  }

  const cleanup = () => {
    // Don't disconnect socket, just clean up local state
    clearAvatars()
    setMessages([])
    setCurrentRoom(null)
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
    if (!socketService.isConnected() || !roomId) return

    socketService.sendMessage({
      room_id: roomId,
      user_id: user!.id,
      username: user!.username,
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
    <div className="h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 overflow-hidden">
      {/* Header */}
      <div className="h-16 bg-gray-900/80 backdrop-blur-sm border-b border-gray-700 flex items-center px-6">
        <button
          onClick={handleBack}
          className="flex items-center gap-2 text-white hover:text-purple-400 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          <span>Back</span>
        </button>
        
        <div className="flex-1 text-center">
          <h1 className="text-xl font-bold text-white">
            {currentRoom?.name || 'Room'}
          </h1>
          <p className="text-sm text-gray-400">
            {currentRoom?.description}
          </p>
        </div>

        <button
          onClick={() => setShowUserList(!showUserList)}
          className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-colors md:hidden"
        >
          <UsersIcon className="w-5 h-5" />
          <span>{activeUsers.length}</span>
        </button>
      </div>

      {/* Main Content */}
      <div className="h-[calc(100vh-4rem)] grid grid-cols-1 md:grid-cols-12 gap-4 p-4">
        {/* Game Canvas */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="md:col-span-6 h-full"
        >
          <div className="h-full bg-gray-800 rounded-xl border border-gray-700 overflow-hidden shadow-2xl">
            <GameCanvas
              roomId={roomId!}
              userId={user.id}
              username={user.username}
              avatarStyle={user.avatar_style}
              avatarColor={user.avatar_color}
              onMove={handleMove}
              onReady={handleSceneReady}
            />
          </div>
        </motion.div>

        {/* Chat Panel */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="md:col-span-4 h-full"
        >
          <ChatPanel
            messages={messages}
            onSendMessage={handleSendMessage}
            onTyping={handleTyping}
            currentUsername={user.username}
          />
        </motion.div>

        {/* User List */}
        {showUserList && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="md:col-span-2 h-full hidden md:block"
          >
            <UserList
              users={activeUsers.map(userId => ({
                userId,
                username: userId === user.id ? user.username : 'User',
                avatarStyle: user.avatar_style,
                avatarColor: user.avatar_color,
                isActive: true,
              }))}
              currentUserId={user.id}
            />
          </motion.div>
        )}
      </div>
    </div>
  )
}

