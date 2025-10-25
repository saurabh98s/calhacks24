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
      return {
        background: '#AA96DA',
        color: '#FFF',
        border: '3px solid #000',
        boxShadow: '4px 4px 0 #000'
      }
    } else if (message.message_type === 'system') {
      return {
        background: '#ECF0F1',
        color: '#000',
        border: '3px solid #000',
        boxShadow: '4px 4px 0 #000',
        textAlign: 'center' as const
      }
    } else if (message.username === currentUsername) {
      return {
        background: '#4ECDC4',
        color: '#FFF',
        border: '3px solid #000',
        boxShadow: '4px 4px 0 #000',
        marginLeft: 'auto'
      }
    }
    return {
      background: '#FFF',
      color: '#000',
      border: '3px solid #000',
      boxShadow: '4px 4px 0 #000'
    }
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
    <>
      <style>{`
        /* Custom scrollbar styling for chat messages */
        .chat-messages-container::-webkit-scrollbar {
          width: 8px;
        }
        .chat-messages-container::-webkit-scrollbar-track {
          background: rgba(0, 0, 0, 0.2);
          border-radius: 4px;
        }
        .chat-messages-container::-webkit-scrollbar-thumb {
          background: rgba(75, 85, 99, 0.8);
          border-radius: 4px;
        }
        .chat-messages-container::-webkit-scrollbar-thumb:hover {
          background: rgba(107, 114, 128, 1);
        }
        /* Firefox scrollbar */
        .chat-messages-container {
          scrollbar-width: thin;
          scrollbar-color: rgba(75, 85, 99, 0.8) rgba(0, 0, 0, 0.2);
        }
      `}</style>
      
      <div className="pixel-panel flex flex-col h-full" style={{
        background: 'rgba(255, 255, 255, 0.98)',
        border: '4px solid #000',
        boxShadow: '8px 8px 0 #000'
      }}>
        {/* Header */}
        <div className="px-4 py-3 flex-shrink-0" style={{
          borderBottom: '4px solid #000',
          background: '#FFE66D'
        }}>
          <h2 className="pixel-title" style={{
            fontSize: 'clamp(12px, 2vw, 14px)',
            color: '#000',
            textShadow: 'none'
          }}>
            💬 CHAT 💬
          </h2>
        </div>

        {/* Messages - Scrollable Container */}
        <div 
          className="chat-messages-container flex-1 overflow-y-auto overflow-x-hidden px-4 py-3 space-y-3"
          style={{
            scrollBehavior: 'smooth',
            maxHeight: '100%',
            minHeight: 0,
            WebkitOverflowScrolling: 'touch'
          }}
        >
        
        {messages.length === 0 ? (
          <div style={{
            textAlign: 'center',
            color: '#666',
            padding: '32px',
            fontFamily: 'Press Start 2P, cursive',
            fontSize: '10px',
            lineHeight: '2'
          }}>
            💬 NO MESSAGES YET!
            <br />
            🎮 START THE CHAT! 🎮
          </div>
        ) : (
          <AnimatePresence mode="popLayout">
            {messages.map((message, index) => {
              const messageStyle = getMessageStyle(message)
              return (
                <motion.div
                  key={`${message.message_id}-${index}`}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  style={{
                    maxWidth: '80%',
                    padding: '12px',
                    fontFamily: 'Press Start 2P, cursive',
                    ...messageStyle
                  }}
                >
                  <div style={{
                    display: 'flex',
                    alignItems: 'baseline',
                    gap: '8px',
                    marginBottom: '8px',
                    flexWrap: 'wrap'
                  }}>
                    <span style={{
                      fontSize: '10px',
                      fontWeight: 'bold',
                      color: messageStyle.color === '#FFF' ? '#FFE66D' : '#000'
                    }}>
                      {message.username}
                    </span>
                    {message.message_type === 'ai' && (
                      <span style={{
                        fontSize: '8px',
                        background: '#FFE66D',
                        color: '#000',
                        padding: '2px 6px',
                        border: '2px solid #000'
                      }}>
                        🤖 AI
                      </span>
                    )}
                    <span style={{
                      fontSize: '8px',
                      opacity: 0.7,
                      marginLeft: 'auto',
                      color: messageStyle.color
                    }}>
                      {new Date(message.timestamp).toLocaleTimeString([], { 
                        hour: '2-digit', 
                        minute: '2-digit' 
                      })}
                    </span>
                  </div>
                  <p style={{
                    fontSize: '10px',
                    lineHeight: '1.6',
                    wordBreak: 'break-word',
                    color: messageStyle.color
                  }}>
                    {renderMessageWithMentions(message.message || message.content)}
                  </p>
                </motion.div>
              )
            })}
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
            className="px-4 py-2 flex-shrink-0"
            style={{
              borderTop: '3px solid #000',
              background: '#FFE66D'
            }}
          >
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '8px',
              fontFamily: 'Press Start 2P, cursive',
              color: '#000'
            }}>
              <div style={{ display: 'flex', gap: '4px' }}>
                <motion.span
                  animate={{ opacity: [0.3, 1, 0.3] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                >
                  ●
                </motion.span>
                <motion.span
                  animate={{ opacity: [0.3, 1, 0.3] }}
                  transition={{ duration: 1.5, repeat: Infinity, delay: 0.3 }}
                >
                  ●
                </motion.span>
                <motion.span
                  animate={{ opacity: [0.3, 1, 0.3] }}
                  transition={{ duration: 1.5, repeat: Infinity, delay: 0.6 }}
                >
                  ●
                </motion.span>
              </div>
              <span>
                {typingUsers.length === 1 
                  ? `${typingUsers[0]} TYPING...`
                  : typingUsers.length === 2
                  ? `${typingUsers[0]} & ${typingUsers[1]} TYPING...`
                  : `${typingUsers[0]} +${typingUsers.length - 1} TYPING...`
                }
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input */}
      <div className="px-4 py-3 relative flex-shrink-0" style={{
        borderTop: '4px solid #000',
        background: '#FFF'
      }}>
        {/* Mention Dropdown */}
        {showMentions && getFilteredUsers().length > 0 && (
          <div className="pixel-panel" style={{
            position: 'absolute',
            bottom: '100%',
            left: '16px',
            right: '16px',
            marginBottom: '8px',
            background: '#FFF',
            border: '4px solid #000',
            boxShadow: '8px 8px 0 #000',
            maxHeight: '200px',
            overflowY: 'auto',
            zIndex: 50
          }}>
            {getFilteredUsers().map((username, index) => (
              <button
                key={username}
                onClick={() => insertMention(username)}
                style={{
                  width: '100%',
                  padding: '12px',
                  textAlign: 'left',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  background: index === selectedMentionIndex ? '#FFE66D' : '#FFF',
                  border: 'none',
                  borderBottom: '2px solid #000',
                  cursor: 'pointer',
                  fontFamily: 'Press Start 2P, cursive',
                  fontSize: '10px'
                }}
              >
                <div style={{
                  width: '32px',
                  height: '32px',
                  background: '#4ECDC4',
                  border: '3px solid #000',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#FFF',
                  fontWeight: 'bold'
                }}>
                  {username.charAt(0).toUpperCase()}
                </div>
                <span style={{ color: '#000' }}>{username}</span>
              </button>
            ))}
          </div>
        )}
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <input
            ref={inputRef}
            type="text"
            value={inputMessage}
            onChange={handleInputChange}
            onKeyDown={handleKeyPress}
            placeholder="TYPE MESSAGE... (@ MENTION)"
            className="pixel-input"
            style={{
              flex: 1,
              padding: '12px',
              fontSize: '10px',
              fontFamily: 'Press Start 2P, cursive'
            }}
          />
          <motion.button
            onClick={handleSend}
            disabled={!inputMessage.trim()}
            whileHover={{ scale: !inputMessage.trim() ? 1 : 1.05 }}
            whileTap={{ scale: !inputMessage.trim() ? 1 : 0.95 }}
            className="pixel-btn"
            style={{
              padding: '12px',
              background: inputMessage.trim() ? '#4ECDC4' : '#CCC',
              cursor: inputMessage.trim() ? 'pointer' : 'not-allowed'
            }}
          >
            <Send style={{ width: '16px', height: '16px', color: '#FFF' }} />
          </motion.button>
        </div>
      </div>
    </div>
    </>
  )
}

