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
    })

    this.socket.on('disconnect', (reason) => {
      console.log('❌ Socket disconnected, reason:', reason)
    })

    this.socket.on('connect_error', (error) => {
      console.error('❌ Socket connection error:', error)
    })

    this.socket.on('error', (data) => {
      console.error('❌ Socket error:', data)
    })

    // Multi-agent system events
    this.socket.on('user_banned', (data) => {
      console.log('🚫 User banned:', data)
      this.emit('user_banned', data)
    })

    this.socket.on('user_muted', (data) => {
      console.log('🔇 User muted:', data)
      this.emit('user_muted', data)
    })

    this.socket.on('moderation_warning', (data) => {
      console.log('⚠️ Moderation warning:', data)
      this.emit('moderation_warning', data)
    })

    this.socket.on('crisis_resources', (data) => {
      console.log('🚨 Crisis resources:', data)
      this.emit('crisis_resources', data)
    })

    // Register catch-all listener for debugging
    this.socket.onAny((eventName, ...args) => {
      console.log(`🔔 Socket.IO event received: ${eventName}`, args)
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
    console.log('📤 Sending message via socket:', this.socket.id, data)
    this.socket.emit('send_message', data)
    console.log('✅ Message emitted to server')
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

  leaveRoom(roomId: string, userId: string) {
    if (!this.socket) return
    this.socket.emit('leave_room', { room_id: roomId, user_id: userId })
  }

  // Event listener management - register directly on socket
  on(event: string, callback: Function) {
    if (!this.socket) {
      console.warn(`Cannot register listener for '${event}': socket not initialized`)
      return
    }

    // Track callbacks to prevent duplicates
    if (!this.listeners.has(event)) {
      this.listeners.set(event, [])
    }
    
    const callbacks = this.listeners.get(event)!
    if (callbacks.includes(callback)) {
      console.log(`⚠️ Listener for '${event}' already registered, skipping`)
      return
    }
    
    callbacks.push(callback)
    
    // Register directly on socket.io with wrapper for debugging
    const wrappedCallback = (...args: any[]) => {
      console.log(`🎯 Event '${event}' triggered with data:`, args)
      callback(...args)
    }
    
    this.socket.on(event, wrappedCallback as any)
    console.log(`✅ Registered listener for: ${event}, socket ID: ${this.socket.id}`)
  }

  off(event: string, callback: Function) {
    const callbacks = this.listeners.get(event)
    if (callbacks) {
      const index = callbacks.indexOf(callback)
      if (index > -1) {
        callbacks.splice(index, 1)
      }
    }
    
    if (this.socket) {
      this.socket.off(event, callback as any)
    }
  }

  private emit(event: string, data?: any) {
    // This is for our custom events, not socket.io events
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

