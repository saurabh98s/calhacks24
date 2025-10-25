import { create } from 'zustand'
import { Position } from '../types'

interface Avatar {
  userId: string
  username: string
  position: Position
  avatarStyle: string
  avatarColor: string
}

interface GameState {
  avatars: Map<string, Avatar>
  myPosition: Position
  isMoving: boolean
  
  addAvatar: (avatar: Avatar) => void
  removeAvatar: (userId: string) => void
  updateAvatarPosition: (userId: string, position: Position) => void
  setMyPosition: (position: Position) => void
  setIsMoving: (isMoving: boolean) => void
  clearAvatars: () => void
}

export const useGameStore = create<GameState>((set) => ({
  avatars: new Map(),
  myPosition: { x: 400, y: 300 },
  isMoving: false,
  
  addAvatar: (avatar) => set((state) => {
    const newAvatars = new Map(state.avatars)
    newAvatars.set(avatar.userId, avatar)
    return { avatars: newAvatars }
  }),
  
  removeAvatar: (userId) => set((state) => {
    const newAvatars = new Map(state.avatars)
    newAvatars.delete(userId)
    return { avatars: newAvatars }
  }),
  
  updateAvatarPosition: (userId, position) => set((state) => {
    const newAvatars = new Map(state.avatars)
    const avatar = newAvatars.get(userId)
    if (avatar) {
      newAvatars.set(userId, { ...avatar, position })
    }
    return { avatars: newAvatars }
  }),
  
  setMyPosition: (position) => set({ myPosition: position }),
  
  setIsMoving: (isMoving) => set({ isMoving }),
  
  clearAvatars: () => set({ avatars: new Map() }),
}))

