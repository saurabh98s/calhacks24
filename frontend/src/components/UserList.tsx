import { Users, Circle } from 'lucide-react'
import { motion } from 'framer-motion'

interface UserInfo {
  userId: string
  username: string
  avatarStyle: string
  avatarColor: string
  isActive: boolean
}

interface UserListProps {
  users: UserInfo[]
  currentUserId: string
}

export const UserList = ({ users, currentUserId }: UserListProps) => {
  const getAvatarColorClass = (color: string) => {
    const colorMap: Record<string, string> = {
      blue: 'bg-blue-500',
      red: 'bg-red-500',
      green: 'bg-green-500',
      purple: 'bg-purple-500',
      orange: 'bg-orange-500',
      pink: 'bg-pink-500',
    }
    return colorMap[color] || 'bg-gray-500'
  }

  return (
    <div className="flex flex-col h-full bg-gray-900/80 backdrop-blur-sm rounded-lg border border-gray-700">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-700 flex items-center gap-2">
        <Users className="w-5 h-5 text-white" />
        <h2 className="text-lg font-semibold text-white">
          Users ({users.length})
        </h2>
      </div>

      {/* User List */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-2">
        {users.map((user) => (
          <motion.div
            key={user.userId}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -10 }}
            className={`flex items-center gap-3 px-3 py-2 rounded-lg ${
              user.userId === currentUserId
                ? 'bg-blue-600/20 border border-blue-500/50'
                : 'bg-gray-800/50 hover:bg-gray-800'
            } transition-colors`}
          >
            {/* Avatar */}
            <div className={`w-10 h-10 rounded-full ${getAvatarColorClass(user.avatarColor)} flex items-center justify-center`}>
              <span className="text-lg">
                {user.avatarStyle === 'cat' && '🐱'}
                {user.avatarStyle === 'robot' && '🤖'}
                {user.avatarStyle === 'alien' && '👽'}
                {user.avatarStyle === 'human' && '👤'}
              </span>
            </div>

            {/* Username */}
            <div className="flex-1">
              <div className="text-sm font-medium text-white">
                {user.username}
                {user.userId === currentUserId && (
                  <span className="ml-2 text-xs text-blue-400">(You)</span>
                )}
              </div>
            </div>

            {/* Status */}
            <Circle
              className={`w-3 h-3 ${
                user.isActive ? 'fill-green-500 text-green-500' : 'fill-gray-500 text-gray-500'
              }`}
            />
          </motion.div>
        ))}
      </div>
    </div>
  )
}

