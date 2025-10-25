import { create } from 'zustand'
import { Room, Message } from '../types'

interface RoomState {
  currentRoom: Room | null
  rooms: Room[]
  messages: Message[]
  activeUsers: string[]
  typingUsers: string[]
  
  setCurrentRoom: (room: Room | null) => void
  setRooms: (rooms: Room[]) => void
  addMessage: (message: Message) => void
  setMessages: (messages: Message[]) => void
  setActiveUsers: (users: string[]) => void
  addTypingUser: (username: string) => void
  removeTypingUser: (username: string) => void
  clearMessages: () => void
}

export const useRoomStore = create<RoomState>((set, get) => ({
  currentRoom: null,
  rooms: [],
  messages: [],
  activeUsers: [],
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
  
  addTypingUser: (username) => {
    console.log('🔵 roomStore.addTypingUser called with:', username)
    set((state) => {
      const newTypingUsers = [...new Set([...state.typingUsers, username])]
      console.log('🔵 New typingUsers state:', newTypingUsers)
      return { typingUsers: newTypingUsers }
    })
  },
  
  removeTypingUser: (username) => {
    console.log('🔴 roomStore.removeTypingUser called with:', username)
    set((state) => {
      const newTypingUsers = state.typingUsers.filter(u => u !== username)
      console.log('🔴 New typingUsers state:', newTypingUsers)
      return { typingUsers: newTypingUsers }
    })
  },
  
  clearMessages: () => set({ messages: [] }),
}))

