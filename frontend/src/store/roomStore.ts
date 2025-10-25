import { create } from 'zustand'
import { Room, Message } from '../types'

interface UserMetadata {
  user_id: string
  username: string
  avatar_style: string
  avatar_color: string
  mood_icon?: string
}

interface RoomState {
  currentRoom: Room | null
  rooms: Room[]
  messages: Message[]
  activeUsers: string[]
  activeUsersMetadata: Map<string, UserMetadata>
  typingUsers: string[]
  
  setCurrentRoom: (room: Room | null) => void
  setRooms: (rooms: Room[]) => void
  addMessage: (message: Message) => void
  setMessages: (messages: Message[]) => void
  setActiveUsers: (users: string[]) => void
  setActiveUsersMetadata: (metadata: UserMetadata[]) => void
  addUserMetadata: (metadata: UserMetadata) => void
  removeUserMetadata: (userId: string) => void
  addTypingUser: (username: string) => void
  removeTypingUser: (username: string) => void
  clearMessages: () => void
}

export const useRoomStore = create<RoomState>((set, get) => ({
  currentRoom: null,
  rooms: [],
  messages: [],
  activeUsers: [],
  activeUsersMetadata: new Map(),
  typingUsers: [],
  
  setCurrentRoom: (room) => set({ currentRoom: room }),
  
  setRooms: (rooms) => set({ rooms }),
  
  addMessage: (message) => {
    const state = get()
    const currentMessages = state.messages
    
    // Check for duplicates
    const isDuplicate = currentMessages.some(m => {
      // Exact ID match
      if (m.message_id === message.message_id) return true
      
      // Near-duplicate: same user, same content, within 2 seconds
      if (m.username === message.username) {
        const sameContent = (m.message === message.message || m.content === message.content)
        if (sameContent) {
          const timeDiff = Math.abs(new Date(m.timestamp).getTime() - new Date(message.timestamp).getTime())
          return timeDiff < 2000
        }
      }
      return false
    })
    
    if (!isDuplicate) {
      console.log('💾 Adding message to store:', message.message_id, message.message)
      // Create NEW array reference to trigger React re-render
      set({ messages: [...currentMessages, message] })
    } else {
      console.log('⚠️ Duplicate message skipped:', message.message_id)
    }
  },
  
  setMessages: (messages) => set({ messages: Array.isArray(messages) ? messages : [] }),
  
  setActiveUsers: (users) => set({ activeUsers: Array.isArray(users) ? users : [] }),
  
  setActiveUsersMetadata: (metadata) => {
    const map = new Map<string, UserMetadata>()
    metadata.forEach(user => {
      map.set(user.user_id, user)
    })
    set({ activeUsersMetadata: map })
  },
  
  addUserMetadata: (metadata) => set((state) => {
    const newMap = new Map(state.activeUsersMetadata)
    newMap.set(metadata.user_id, metadata)
    return { activeUsersMetadata: newMap }
  }),
  
  removeUserMetadata: (userId) => set((state) => {
    const newMap = new Map(state.activeUsersMetadata)
    newMap.delete(userId)
    return { activeUsersMetadata: newMap }
  }),
  
  addTypingUser: (username) => set((state) => ({
    typingUsers: [...new Set([...state.typingUsers, username])]
  })),
  
  removeTypingUser: (username) => set((state) => ({
    typingUsers: state.typingUsers.filter(u => u !== username)
  })),
  
  clearMessages: () => set({ messages: [] }),
}))

