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
  const { currentRoom, setCurrentRoom, messages, addMessage, setMessages, activeUsers, setActiveUsers, addTypingUser, removeTypingUser, typingUsers } = useRoomStore()
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
      if (data.conversation_history && Array.isArray(data.conversation_history)) {
        setMessages(data.conversation_history)
      }
      if (data.active_users && Array.isArray(data.active_users)) {
        setActiveUsers(data.active_users)
      }
    })

    // User joined
    socketService.on('user_joined', (data: any) => {
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
      setActiveUsers(prev => [...prev, data.user_id])
    })

    // User left
    socketService.on('user_left', (data: any) => {
      if (scene) {
        scene.removeAvatar(data.user_id)
      }
      setActiveUsers(prev => prev.filter(id => id !== data.user_id))
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
      console.log('👀 Typing event received:', data)
      console.log('Current user:', user!.username)
      
      if (data.username !== user!.username) {
        console.log('✅ Different user, updating typing state:', data.is_typing)
        if (data.is_typing) {
          addTypingUser(data.username)
          console.log('Added typing user:', data.username)
        } else {
          removeTypingUser(data.username)
          console.log('Removed typing user:', data.username)
        }
      } else {
        console.log('⚠️ Same user, ignoring typing event')
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
            typingUsers={typingUsers}
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

