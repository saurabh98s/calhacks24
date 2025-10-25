import { motion } from 'framer-motion'

interface User {
  userId: string
  username: string
  avatarColor?: string
  isAI?: boolean
}

interface ActiveUsersPanelProps {
  users: User[]
  currentUserId: string
}

export const ActiveUsersPanel = ({ users, currentUserId }: ActiveUsersPanelProps) => {
  // Add AI user
  const allUsers = [
    { userId: 'ai_atlas', username: 'Atlas', avatarColor: 'purple', isAI: true },
    ...users
  ]

  const getAvatarColor = (user: User) => {
    if (user.isAI) return 'from-purple-500 to-pink-500'
    return user.avatarColor === 'blue' 
      ? 'from-blue-500 to-cyan-500'
      : user.avatarColor === 'green'
      ? 'from-green-500 to-emerald-500'
      : user.avatarColor === 'red'
      ? 'from-red-500 to-orange-500'
      : 'from-indigo-500 to-purple-500'
  }

  return (
    <div className="h-full bg-gray-900/80 backdrop-blur-sm rounded-lg border border-gray-700 p-6">
      <h2 className="text-lg font-semibold text-white mb-6">Active Users</h2>
      
      <div className="space-y-6">
        {allUsers.map((user, index) => (
          <motion.div
            key={user.userId}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className="flex flex-col items-center gap-2"
          >
            {/* 2D Avatar Circle */}
            <div className="relative">
              <motion.div
                animate={{ 
                  scale: [1, 1.05, 1],
                  rotate: user.isAI ? [0, 5, -5, 0] : 0
                }}
                transition={{ 
                  duration: 2, 
                  repeat: Infinity,
                  repeatType: 'reverse'
                }}
                className={`w-16 h-16 rounded-full bg-gradient-to-br ${getAvatarColor(user)} flex items-center justify-center text-white font-bold text-2xl shadow-lg ${
                  user.userId === currentUserId ? 'ring-4 ring-blue-400' : ''
                }`}
              >
                {user.username.charAt(0).toUpperCase()}
              </motion.div>
              
              {/* Active indicator */}
              <div className="absolute bottom-0 right-0 w-4 h-4 bg-green-500 rounded-full border-2 border-gray-900"></div>
              
              {/* AI Badge */}
              {user.isAI && (
                <div className="absolute -top-1 -right-1 bg-purple-600 text-white text-xs px-1.5 py-0.5 rounded-full font-semibold">
                  AI
                </div>
              )}
            </div>
            
            {/* Username */}
            <div className="text-center">
              <p className={`text-sm font-medium ${
                user.userId === currentUserId ? 'text-blue-400' : 'text-white'
              }`}>
                {user.username}
              </p>
              {user.userId === currentUserId && (
                <p className="text-xs text-gray-400">(You)</p>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}

