import { useState } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { apiService } from '../services/apiService'
import { AvatarStyle, AvatarColor, MoodIcon } from '../types'

export default function AvatarCreation() {
  const navigate = useNavigate()
  const { setUser, setToken } = useAuthStore()

  const [username, setUsername] = useState('')
  const [avatarStyle, setAvatarStyle] = useState<AvatarStyle>('human')
  const [avatarColor, setAvatarColor] = useState<AvatarColor>('blue')
  const [moodIcon, setMoodIcon] = useState<MoodIcon>('😊')
  const [bio, setBio] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const avatarStyles: { style: AvatarStyle; emoji: string; label: string }[] = [
    { style: 'human', emoji: '👤', label: 'Human' },
    { style: 'cat', emoji: '🐱', label: 'Cat' },
    { style: 'robot', emoji: '🤖', label: 'Robot' },
    { style: 'alien', emoji: '👽', label: 'Alien' },
  ]

  const colors: AvatarColor[] = ['blue', 'red', 'green', 'purple', 'orange', 'pink']
  const moods: MoodIcon[] = ['😊', '😐', '😔', '😤', '🤔', '😴']

  const getColorClass = (color: AvatarColor) => {
    const colorMap: Record<AvatarColor, string> = {
      blue: 'bg-blue-500 border-blue-400',
      red: 'bg-red-500 border-red-400',
      green: 'bg-green-500 border-green-400',
      purple: 'bg-purple-500 border-purple-400',
      orange: 'bg-orange-500 border-orange-400',
      pink: 'bg-pink-500 border-pink-400',
    }
    return colorMap[color]
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!username.trim()) {
      setError('Please enter a username')
      return
    }

    setLoading(true)
    setError('')

    try {
      const response = await apiService.guestLogin({
        username: username.trim(),
        avatar_style: avatarStyle,
        avatar_color: avatarColor,
        mood_icon: moodIcon,
        bio: bio.trim() || undefined,
        is_guest: true,
      })

      // Save token and get user info
      setToken(response.access_token)
      localStorage.setItem('token', response.access_token)

      const user = await apiService.getCurrentUser()
      setUser(user)

      // Navigate to tutorial
      navigate('/tutorial')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create account. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-2xl w-full bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700 p-8"
      >
        <h1 className="text-4xl font-bold text-white text-center mb-8">
          Create Your Character
        </h1>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Avatar Preview */}
          <div className="flex flex-col items-center mb-8">
            <div className={`w-32 h-32 rounded-full ${getColorClass(avatarColor)} flex items-center justify-center mb-4 border-4`}>
              <span className="text-6xl">
                {avatarStyles.find(s => s.style === avatarStyle)?.emoji}
              </span>
            </div>
            <div className="text-4xl mb-2">{moodIcon}</div>
            {username && (
              <div className="text-white font-medium">{username}</div>
            )}
          </div>

          {/* Username */}
          <div>
            <label className="block text-white text-sm font-medium mb-2">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your username"
              maxLength={50}
              className="w-full px-4 py-3 bg-gray-900 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>

          {/* Avatar Style */}
          <div>
            <label className="block text-white text-sm font-medium mb-3">
              Avatar Style
            </label>
            <div className="grid grid-cols-4 gap-3">
              {avatarStyles.map(({ style, emoji, label }) => (
                <button
                  key={style}
                  type="button"
                  onClick={() => setAvatarStyle(style)}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    avatarStyle === style
                      ? 'border-purple-500 bg-purple-500/20'
                      : 'border-gray-600 bg-gray-900 hover:border-gray-500'
                  }`}
                >
                  <div className="text-4xl mb-2">{emoji}</div>
                  <div className="text-white text-xs">{label}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Color */}
          <div>
            <label className="block text-white text-sm font-medium mb-3">
              Color
            </label>
            <div className="grid grid-cols-6 gap-3">
              {colors.map((color) => (
                <button
                  key={color}
                  type="button"
                  onClick={() => setAvatarColor(color)}
                  className={`w-12 h-12 rounded-full ${getColorClass(color)} ${
                    avatarColor === color ? 'ring-4 ring-white' : ''
                  } transition-all`}
                />
              ))}
            </div>
          </div>

          {/* Mood */}
          <div>
            <label className="block text-white text-sm font-medium mb-3">
              Mood Icon
            </label>
            <div className="grid grid-cols-6 gap-3">
              {moods.map((mood) => (
                <button
                  key={mood}
                  type="button"
                  onClick={() => setMoodIcon(mood)}
                  className={`p-3 rounded-lg text-3xl transition-all ${
                    moodIcon === mood
                      ? 'bg-purple-500/20 ring-2 ring-purple-500'
                      : 'bg-gray-900 hover:bg-gray-800'
                  }`}
                >
                  {mood}
                </button>
              ))}
            </div>
          </div>

          {/* Bio */}
          <div>
            <label className="block text-white text-sm font-medium mb-2">
              Bio (optional)
            </label>
            <textarea
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              placeholder="Tell us about yourself..."
              maxLength={500}
              rows={3}
              className="w-full px-4 py-3 bg-gray-900 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
            />
          </div>

          {error && (
            <div className="p-3 bg-red-500/20 border border-red-500 rounded-lg text-red-400 text-sm">
              {error}
            </div>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={loading || !username.trim()}
            className="w-full px-6 py-4 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-semibold rounded-lg hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? 'Creating...' : 'ENTER THE REALM'}
            <ArrowRight className="w-5 h-5" />
          </button>
        </form>
      </motion.div>
    </div>
  )
}

