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
  const [showMentions, setShowMentions] = useState(false)
  const [mentionQuery, setMentionQuery] = useState('')
  const [mentionPosition, setMentionPosition] = useState(0)
  const [selectedMentionIndex, setSelectedMentionIndex] = useState(0)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Get unique usernames from messages for mentions (including AI)
  const getAvailableUsers = () => {
    const usernames = new Set<string>()
    
    // Add single AI persona
    usernames.add('Atlas')
    
    // Add other users
    messages.forEach(msg => {
      if (msg.username && msg.username !== currentUsername && msg.message_type !== 'ai') {
        usernames.add(msg.username)
      }
    })
    
    return Array.from(usernames)
  }

  // Filter users based on mention query
  const getFilteredUsers = () => {
    const users = getAvailableUsers()
    if (!mentionQuery) return users
    return users.filter(user => 
      user.toLowerCase().startsWith(mentionQuery.toLowerCase())
    )
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    const cursorPos = e.target.selectionStart || 0
    setInputMessage(value)

    // Check for @ mention
    const textBeforeCursor = value.slice(0, cursorPos)
    const lastAtSymbol = textBeforeCursor.lastIndexOf('@')
    
    if (lastAtSymbol !== -1 && lastAtSymbol < cursorPos) {
      const textAfterAt = textBeforeCursor.slice(lastAtSymbol + 1)
      // Check if there's no space after @ and cursor is still in mention
      if (!textAfterAt.includes(' ') && textAfterAt.length <= 20) {
        setShowMentions(true)
        setMentionQuery(textAfterAt)
        setMentionPosition(lastAtSymbol)
        setSelectedMentionIndex(0)
      } else {
        setShowMentions(false)
      }
    } else {
      setShowMentions(false)
    }

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

  const insertMention = (username: string) => {
    const beforeMention = inputMessage.slice(0, mentionPosition)
    const afterMention = inputMessage.slice(mentionPosition + mentionQuery.length + 1)
    const newMessage = `${beforeMention}@${username} ${afterMention}`
    setInputMessage(newMessage)
    setShowMentions(false)
    setMentionQuery('')
    
    // Focus back on input
    setTimeout(() => {
      inputRef.current?.focus()
    }, 0)
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
    // Handle mention dropdown navigation
    if (showMentions) {
      const filteredUsers = getFilteredUsers()
      
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedMentionIndex((prev) => 
          prev < filteredUsers.length - 1 ? prev + 1 : prev
        )
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedMentionIndex((prev) => prev > 0 ? prev - 1 : 0)
      } else if (e.key === 'Enter' || e.key === 'Tab') {
        e.preventDefault()
        if (filteredUsers.length > 0) {
          insertMention(filteredUsers[selectedMentionIndex])
        }
        return
      } else if (e.key === 'Escape') {
        setShowMentions(false)
        return
      }
    }
    
    // Normal enter to send
    if (e.key === 'Enter' && !e.shiftKey && !showMentions) {
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

  // Render message with highlighted mentions
  const renderMessageWithMentions = (text: string) => {
    const mentionRegex = /@(\w+)/g
    const parts = []
    let lastIndex = 0
    let match

    while ((match = mentionRegex.exec(text)) !== null) {
      // Add text before mention
      if (match.index > lastIndex) {
        parts.push(text.slice(lastIndex, match.index))
      }
      
      // Add mention with highlight
      const mentionedUser = match[1]
      const isCurrentUser = mentionedUser.toLowerCase() === currentUsername.toLowerCase()
      parts.push(
        <span 
          key={match.index}
          className={`font-semibold ${isCurrentUser ? 'text-blue-400 bg-blue-500/20 px-1 rounded' : 'text-purple-400'}`}
        >
          @{mentionedUser}
        </span>
      )
      
      lastIndex = match.index + match[0].length
    }
    
    // Add remaining text
    if (lastIndex < text.length) {
      parts.push(text.slice(lastIndex))
    }
    
    return parts.length > 0 ? parts : text
  }

  return (
    <div className="flex flex-col h-full bg-gray-900/80 backdrop-blur-sm rounded-lg border border-gray-700">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-700 flex-shrink-0">
        <h2 className="text-lg font-semibold text-white">Chat</h2>
      </div>

      {/* Messages - Scrollable Container */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden px-4 py-3 space-y-3 scrollbar-thin">
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
                  {renderMessageWithMentions(message.message || message.content)}
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
            className="px-4 py-2 border-t border-gray-700/50 flex-shrink-0"
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
      <div className="px-4 py-3 border-t border-gray-700 relative flex-shrink-0">
        {/* Mention Dropdown */}
        {showMentions && getFilteredUsers().length > 0 && (
          <div className="absolute bottom-full left-4 right-4 mb-2 bg-gray-800 border border-gray-600 rounded-lg shadow-xl max-h-48 overflow-y-auto z-50">
            {getFilteredUsers().map((username, index) => (
              <button
                key={username}
                onClick={() => insertMention(username)}
                className={`w-full px-4 py-2 text-left flex items-center gap-3 hover:bg-gray-700 transition-colors ${
                  index === selectedMentionIndex ? 'bg-gray-700' : ''
                }`}
              >
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white font-semibold text-sm">
                  {username.charAt(0).toUpperCase()}
                </div>
                <span className="text-white font-medium">{username}</span>
              </button>
            ))}
          </div>
        )}
        
        <div className="flex items-center gap-2">
          <input
            ref={inputRef}
            type="text"
            value={inputMessage}
            onChange={handleInputChange}
            onKeyDown={handleKeyPress}
            placeholder="Type your message... (@ to mention)"
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

