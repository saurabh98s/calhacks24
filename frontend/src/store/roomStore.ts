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

export const useRoomStore = create<RoomState>((set) => ({
  currentRoom: null,
  rooms: [],
  messages: [],
  activeUsers: [],
  typingUsers: [],
  
  setCurrentRoom: (room) => set({ currentRoom: room }),
  
  setRooms: (rooms) => set({ rooms }),
  
  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message]
  })),
  
  setMessages: (messages) => set({ messages }),
  
  setActiveUsers: (users) => set({ activeUsers: users }),
  
  addTypingUser: (username) => set((state) => ({
    typingUsers: [...new Set([...state.typingUsers, username])]
  })),
  
  removeTypingUser: (username) => set((state) => ({
    typingUsers: state.typingUsers.filter(u => u !== username)
  })),
  
  clearMessages: () => set({ messages: [] }),
}))

