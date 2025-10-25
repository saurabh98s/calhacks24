import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { Sparkles } from 'lucide-react'

export default function Landing() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 flex items-center justify-center p-4">
      <div className="max-w-4xl w-full text-center">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <h1 className="text-6xl md:text-8xl font-bold text-white mb-6">
            ChatRealm
          </h1>
          
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.8 }}
            className="mb-8"
          >
            <p className="text-xl md:text-2xl text-gray-300 mb-4">
              Walk into conversations. Talk with AI.
            </p>
            <p className="text-lg text-gray-400">
              Make every chat feel alive.
            </p>
          </motion.div>

          {/* Animated preview area */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.6, duration: 0.8 }}
            className="mb-12 h-64 bg-gray-800/50 rounded-lg border border-gray-700 flex items-center justify-center backdrop-blur-sm"
          >
            <div className="flex gap-8">
              {['👤', '🐱', '🤖', '👽'].map((avatar, i) => (
                <motion.div
                  key={i}
                  animate={{
                    y: [0, -10, 0],
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    delay: i * 0.2,
                  }}
                  className="text-6xl"
                >
                  {avatar}
                </motion.div>
              ))}
            </div>
          </motion.div>

          <motion.button
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.9, duration: 0.8 }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => navigate('/avatar')}
            className="px-8 py-4 bg-gradient-to-r from-purple-600 to-blue-600 text-white text-xl font-semibold rounded-lg shadow-lg hover:shadow-xl transition-all flex items-center gap-3 mx-auto"
          >
            <Sparkles className="w-6 h-6" />
            START YOUR JOURNEY
          </motion.button>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.2, duration: 0.8 }}
            className="mt-12 text-gray-500 text-sm"
          >
            <p>Enter rooms as avatars • Chat with context-aware AI • Real-time multiplayer</p>
          </motion.div>
        </motion.div>
      </div>
    </div>
  )
}

