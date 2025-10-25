// User types
export interface User {
  id: string
  username: string
  email?: string
  avatar_style: string
  avatar_color: string
  mood_icon: string
  bio?: string
  engagement_score: number
  total_messages: number
  rooms_joined: number
  is_active: boolean
  is_guest: boolean
  created_at: string
  last_seen: string
}

export interface UserCreate {
  username: string
  email?: string
  password?: string
  avatar_style?: string
  avatar_color?: string
  mood_icon?: string
  bio?: string
  is_guest?: boolean
}

// Room types
export interface Room {
  id: string
  room_id: string
  name: string
  room_type: 'study_group' | 'support_circle' | 'casual_lounge' | 'private' | 'tutorial'
  ai_persona: string
  description?: string
  max_users: number
  is_public: boolean
  active_users_count: number
  total_messages: number
  created_at: string
}

// Message types
export interface Message {
  message_id: string
  room_id: string
  user_id?: string
  username: string
  message: string
  content?: string
  message_type: 'user' | 'ai' | 'system'
  ai_persona?: string
  ai_trigger?: string
  sentiment?: string
  timestamp: string
  avatar_style?: string
  avatar_color?: string
}

// Position types for avatar movement
export interface Position {
  x: number
  y: number
}

// Socket events
export interface SocketEvents {
  connect: () => void
  disconnect: () => void
  user_joined: (data: UserJoinedData) => void
  user_left: (data: UserLeftData) => void
  new_message: (message: Message) => void
  user_typing: (data: TypingData) => void
  avatar_moved: (data: AvatarMovedData) => void
  room_joined: (data: RoomJoinedData) => void
  error: (data: { message: string }) => void
}

export interface UserJoinedData {
  user_id: string
  username: string
  avatar_style: string
  avatar_color: string
  timestamp: string
}

export interface UserLeftData {
  user_id: string
  username: string
  timestamp: string
}

export interface TypingData {
  username: string
  is_typing: boolean
}

export interface AvatarMovedData {
  user_id: string
  position: Position
}

export interface RoomJoinedData {
  room_id: string
  message: string
  conversation_history: Message[]
  active_users: string[]
}

// Avatar styles
export type AvatarStyle = 'human' | 'cat' | 'robot' | 'alien'
export type AvatarColor = 'blue' | 'red' | 'green' | 'purple' | 'orange' | 'pink'
export type MoodIcon = '😊' | '😐' | '😔' | '😤' | '🤔' | '😴'

