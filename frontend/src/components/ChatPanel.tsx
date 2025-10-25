import { useState, useEffect, useRef } from 'react'
import { Send, Smile } from 'lucide-react'
import { Message } from '../types'
import { motion, AnimatePresence } from 'framer-motion'

interface ChatPanelProps {
  messages: Message[]
  onSendMessage: (message: string) => void
  onTyping: (isTyping: boolean) => void
  currentUsername: string
  typingUsers?: string[]
}

export const ChatPanel = ({ messages, onSendMessage, onTyping, currentUsername, typingUsers = [] }: ChatPanelProps) => {
  const [inputMessage, setInputMessage] = useState('')
  const [typingTimeout, setTypingTimeout] = useState<NodeJS.Timeout | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Debug: Log typing users when they change
  useEffect(() => {
    console.log('💬 ChatPanel typingUsers changed:', typingUsers)
  }, [typingUsers])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setInputMessage(value)

    // Typing indicator
    if (value.length > 0) {
      onTyping(true)

      // Clear previous timeout
      if (typingTimeout) {
        clearTimeout(typingTimeout)
      }

      // Set new timeout to stop typing indicator
      const timeout = setTimeout(() => {
        onTyping(false)
      }, 1000)
      setTypingTimeout(timeout)
    } else {
      onTyping(false)
    }
  }

  const handleSend = () => {
    if (inputMessage.trim()) {
      onSendMessage(inputMessage.trim())
      setInputMessage('')
      onTyping(false)
      
      if (typingTimeout) {
        clearTimeout(typingTimeout)
      }
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const getMessageStyle = (message: Message) => {
    if (message.message_type === 'ai') {
      return 'bg-purple-600/20 border-purple-500/50'
    } else if (message.message_type === 'system') {
      return 'bg-gray-600/20 border-gray-500/50 text-center'
    } else if (message.username === currentUsername) {
      return 'bg-blue-600/20 border-blue-500/50 ml-auto'
    }
    return 'bg-gray-700/30 border-gray-600/50'
  }

  return (
    <div className="flex flex-col h-full bg-gray-900/80 backdrop-blur-sm rounded-lg border border-gray-700">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-700">
        <h2 className="text-lg font-semibold text-white">Chat</h2>
      </div>

      {/* Messages - Scrollable Container */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3 scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800">
        {messages.length === 0 ? (
          <div className="text-center text-gray-400 py-8">
            No messages yet. Start the conversation!
          </div>
        ) : (
          <AnimatePresence mode="popLayout">
            {messages.map((message, index) => (
              <motion.div
                key={`${message.message_id}-${index}`}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                className={`max-w-[80%] px-4 py-2 rounded-lg border ${getMessageStyle(message)}`}
              >
                <div className="flex items-baseline gap-2 mb-1">
                  <span className="text-sm font-semibold text-white">
                    {message.username}
                  </span>
                  {message.message_type === 'ai' && (
                    <span className="text-xs text-purple-400">AI</span>
                  )}
                  <span className="text-xs text-gray-400 ml-auto">
                    {new Date(message.timestamp).toLocaleTimeString([], { 
                      hour: '2-digit', 
                      minute: '2-digit' 
                    })}
                  </span>
                </div>
                <p className="text-sm text-gray-200 break-words">
                  {message.message || message.content}
                </p>
              </motion.div>
            ))}
          </AnimatePresence>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Typing Indicator */}
      <AnimatePresence>
        {typingUsers.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="px-4 py-2 border-t border-gray-700/50"
          >
            <div className="flex items-center gap-2 text-sm text-gray-400">
              <div className="flex gap-1">
                <motion.span
                  animate={{ opacity: [0.5, 1, 0.5] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                >
                  •
                </motion.span>
                <motion.span
                  animate={{ opacity: [0.5, 1, 0.5] }}
                  transition={{ duration: 1.5, repeat: Infinity, delay: 0.3 }}
                >
                  •
                </motion.span>
                <motion.span
                  animate={{ opacity: [0.5, 1, 0.5] }}
                  transition={{ duration: 1.5, repeat: Infinity, delay: 0.6 }}
                >
                  •
                </motion.span>
              </div>
              <span>
                {typingUsers.length === 1 
                  ? `${typingUsers[0]} is typing...`
                  : typingUsers.length === 2
                  ? `${typingUsers[0]} and ${typingUsers[1]} are typing...`
                  : `${typingUsers[0]} and ${typingUsers.length - 1} others are typing...`
                }
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input */}
      <div className="px-4 py-3 border-t border-gray-700">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={inputMessage}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            className="flex-1 px-4 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleSend}
            disabled={!inputMessage.trim()}
            className="p-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-lg transition-colors"
          >
            <Send className="w-5 h-5 text-white" />
          </button>
        </div>
      </div>
    </div>
  )
}

