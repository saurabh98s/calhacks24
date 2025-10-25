import axios, { AxiosInstance } from 'axios'
import { User, UserCreate, Room } from '../types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

class APIService {
  private api: AxiosInstance

  constructor() {
    this.api = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Add token to requests
    this.api.interceptors.request.use((config) => {
      const token = localStorage.getItem('token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })
  }

  // Auth endpoints
  async register(userData: UserCreate) {
    const response = await this.api.post('/api/auth/register', userData)
    return response.data
  }

  async login(username: string, password: string) {
    const response = await this.api.post('/api/auth/login', { username, password })
    return response.data
  }

  async guestLogin(userData: UserCreate) {
    const response = await this.api.post('/api/auth/guest', userData)
    return response.data
  }

  // User endpoints
  async getCurrentUser(): Promise<User> {
    const response = await this.api.get('/api/users/me')
    return response.data
  }

  async updateUser(userData: Partial<UserCreate>): Promise<User> {
    const response = await this.api.patch('/api/users/me', userData)
    return response.data
  }

  // Room endpoints
  async getRooms(roomType?: string): Promise<Room[]> {
    const params = roomType ? { room_type: roomType } : {}
    const response = await this.api.get('/api/rooms/', { params })
    return response.data
  }

  async getRoom(roomId: string): Promise<Room> {
    const response = await this.api.get(`/api/rooms/${roomId}`)
    return response.data
  }

  async createRoom(roomData: any): Promise<Room> {
    const response = await this.api.post('/api/rooms/', roomData)
    return response.data
  }

  async initializeDefaultRooms() {
    const response = await this.api.post('/api/rooms/initialize-defaults')
    return response.data
  }
}

export const apiService = new APIService()

