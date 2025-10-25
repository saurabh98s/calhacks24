import { motion } from 'framer-motion'
import { Smile, Meh, Frown, AlertCircle } from 'lucide-react'

interface EmotionIndicatorProps {
  sentiment: 'positive' | 'neutral' | 'negative' | 'frustrated'
  username: string
}

export const EmotionIndicator = ({ sentiment, username }: EmotionIndicatorProps) => {
  const getEmotionConfig = () => {
    switch (sentiment) {
      case 'positive':
        return {
          icon: Smile,
          color: 'text-green-400',
          bg: 'bg-green-500/20',
          label: 'Positive',
        }
      case 'neutral':
        return {
          icon: Meh,
          color: 'text-gray-400',
          bg: 'bg-gray-500/20',
          label: 'Neutral',
        }
      case 'negative':
        return {
          icon: Frown,
          color: 'text-yellow-400',
          bg: 'bg-yellow-500/20',
          label: 'Confused',
        }
      case 'frustrated':
        return {
          icon: AlertCircle,
          color: 'text-red-400',
          bg: 'bg-red-500/20',
          label: 'Needs Help',
        }
      default:
        return {
          icon: Meh,
          color: 'text-gray-400',
          bg: 'bg-gray-500/20',
          label: 'Neutral',
        }
    }
  }

  const config = getEmotionConfig()
  const Icon = config.icon

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`flex items-center gap-2 px-3 py-2 rounded-lg ${config.bg} border border-gray-700`}
    >
      <Icon className={`w-4 h-4 ${config.color}`} />
      <div className="text-xs">
        <div className="text-gray-400">{username}</div>
        <div className={`font-medium ${config.color}`}>{config.label}</div>
      </div>
    </motion.div>
  )
}

