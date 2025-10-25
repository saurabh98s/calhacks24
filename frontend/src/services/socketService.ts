import { io, Socket } from 'socket.io-client'
import { Message, Position } from '../types'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

class SocketService {
  private socket: Socket | null = null
  private listeners: Map<string, Function[]> = new Map()

  connect(token: string) {
    if (this.socket?.connected) {
      console.log('Socket already connected, reusing existing connection')
      return this.socket
    }

    console.log('Creating new socket connection to:', WS_URL)
    
    this.socket = io(WS_URL, {
      auth: { token },
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 10,
      timeout: 10000,
    })

    this.socket.on('connect', () => {
      console.log('✅ Socket connected, ID:', this.socket?.id)
      this.emit('connect')
    })

    this.socket.on('disconnect', (reason) => {
      console.log('❌ Socket disconnected, reason:', reason)
      this.emit('disconnect')
    })

    this.socket.on('connect_error', (error) => {
      console.error('❌ Socket connection error:', error)
      this.emit('error', { message: error.message })
    })

    this.socket.on('error', (data) => {
      console.error('❌ Socket error:', data)
      this.emit('error', data)
    })

    this.socket.on('user_joined', (data) => {
      console.log('👤 User joined:', data)
      this.emit('user_joined', data)
    })

    this.socket.on('user_left', (data) => {
      console.log('👋 User left:', data)
      this.emit('user_left', data)
    })

    this.socket.on('new_message', (message: Message) => {
      console.log('💬 New message:', message)
      this.emit('new_message', message)
    })

    this.socket.on('user_typing', (data) => {
      this.emit('user_typing', data)
    })

    this.socket.on('avatar_moved', (data) => {
      this.emit('avatar_moved', data)
    })

    this.socket.on('room_joined', (data) => {
      console.log('🚪 Room joined:', data)
      this.emit('room_joined', data)
    })

    return this.socket
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
    this.listeners.clear()
  }

  joinRoom(data: {
    room_id: string
    user_id: string
    username: string
    avatar_style: string
    avatar_color: string
  }) {
    if (!this.socket) {
      throw new Error('Socket not connected')
    }
    if (!this.socket.connected) {
      console.warn('Socket not connected, waiting...')
      this.socket.once('connect', () => {
        console.log('Socket connected, now joining room')
        this.socket!.emit('join_room', data)
      })
    } else {
      console.log('📤 Emitting join_room event:', data)
      this.socket.emit('join_room', data)
    }
  }

  sendMessage(data: {
    room_id: string
    user_id: string
    username: string
    message: string
  }) {
    if (!this.socket) {
      console.error('Cannot send message: Socket not initialized')
      throw new Error('Socket not connected')
    }
    if (!this.socket.connected) {
      console.error('Cannot send message: Socket not connected')
      throw new Error('Socket not connected')
    }
    console.log('📤 Sending message:', data)
    this.socket.emit('send_message', data)
  }

  sendTyping(data: {
    room_id: string
    username: string
    is_typing: boolean
  }) {
    if (!this.socket) {
      throw new Error('Socket not connected')
    }
    this.socket.emit('typing', data)
  }

  moveAvatar(data: {
    room_id: string
    user_id: string
    position: Position
  }) {
    if (!this.socket) {
      throw new Error('Socket not connected')
    }
    this.socket.emit('move_avatar', data)
  }

  // Event listener management
  on(event: string, callback: Function) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, [])
    }
    this.listeners.get(event)!.push(callback)
  }

  off(event: string, callback: Function) {
    const callbacks = this.listeners.get(event)
    if (callbacks) {
      const index = callbacks.indexOf(callback)
      if (index > -1) {
        callbacks.splice(index, 1)
      }
    }
  }

  private emit(event: string, data?: any) {
    const callbacks = this.listeners.get(event)
    if (callbacks) {
      callbacks.forEach(callback => callback(data))
    }
  }

  isConnected(): boolean {
    return this.socket?.connected || false
  }
}

export const socketService = new SocketService()

