import { useState } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { apiService } from '../services/apiService'
import { AvatarStyle, AvatarColor, MoodIcon } from '../types'
import '../styles/retro-game.css'

export default function AvatarCreation() {
  const navigate = useNavigate()
  const { setUser, setToken } = useAuthStore()

  const [username, setUsername] = useState('')
  const [avatarStyle, setAvatarStyle] = useState<AvatarStyle>('human')
  const [avatarColor, setAvatarColor] = useState<AvatarColor>('blue')
  const [moodIcon, setMoodIcon] = useState<MoodIcon>('😊')
  const [bio, setBio] = useState('')
  const [linkedinUrl, setLinkedinUrl] = useState('')
  const [profileData, setProfileData] = useState<any>(null)
  const [showConfirmDialog, setShowConfirmDialog] = useState(false)
  const [scrapingLinkedIn, setScrapingLinkedIn] = useState(false)
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

  const getPixelColorClass = (color: AvatarColor) => {
    const colorMap: Record<AvatarColor, string> = {
      blue: '#4ECDC4',
      red: '#FF6B6B',
      green: '#95E1D3',
      purple: '#AA96DA',
      orange: '#FFE66D',
      pink: '#F38181',
    }
    return colorMap[color]
  }

  const handleScrapeLinkedIn = async () => {
    if (!linkedinUrl.trim()) {
      setError('Please enter a LinkedIn URL')
      return
    }

    setScrapingLinkedIn(true)
    setError('')

    try {
      const response = await fetch('http://localhost:8000/api/auth/scrape-linkedin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ linkedin_url: linkedinUrl.trim() })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to scrape LinkedIn profile')
      }

      const data = await response.json()
      setProfileData(data)
      setShowConfirmDialog(true)
    } catch (err: any) {
      setError(err.message || 'Failed to scrape LinkedIn profile. Please check the URL and try again.')
    } finally {
      setScrapingLinkedIn(false)
    }
  }

  const handleConfirmProfile = async () => {
    setShowConfirmDialog(false)
    await submitWithPersona()
  }

  const handleSkipLinkedIn = async () => {
    await submitWithPersona()
  }

  const submitWithPersona = async () => {
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
        linkedin_url: linkedinUrl.trim() || undefined,
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // If LinkedIn URL provided but not scraped yet, scrape first
    if (linkedinUrl.trim() && !profileData) {
      await handleScrapeLinkedIn()
    } else {
      await submitWithPersona()
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{
      background: 'linear-gradient(135deg, #AA96DA 0%, #F38181 50%, #FFE66D 100%)',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Animated background pixels */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundImage: `url("data:image/svg+xml,%3Csvg width='40' height='40' xmlns='http://www.w3.org/2000/svg'%3E%3Crect width='40' height='40' fill='rgba(255,255,255,0.05)'/%3E%3Crect x='15' y='15' width='10' height='10' fill='rgba(255,255,255,0.1)'/%3E%3C/svg%3E")`,
        animation: 'float 15s linear infinite',
      }} />

      <div className="pixel-container" style={{ maxWidth: '800px', zIndex: 1 }}>
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4, type: "spring" }}
          className="pixel-panel pixel-game-border"
          style={{
            background: 'rgba(255, 255, 255, 0.98)',
          }}
        >
          {/* Title */}
          <motion.h1
            className="pixel-title"
            style={{
              fontSize: 'clamp(20px, 5vw, 36px)',
              marginBottom: '32px',
              color: '#000',
            }}
            animate={{
              textShadow: [
                '4px 4px 0 #FF6B6B',
                '4px 4px 0 #4ECDC4',
                '4px 4px 0 #FFE66D',
                '4px 4px 0 #FF6B6B'
              ]
            }}
            transition={{ duration: 3, repeat: Infinity }}
          >
            🎭 CREATE YOUR CHARACTER 🎭
          </motion.h1>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {/* Avatar Preview - Cute animated display */}
            <motion.div
              className="pixel-panel-gradient"
              style={{
                padding: '32px',
                textAlign: 'center',
                border: '6px solid #000',
                boxShadow: 'inset 0 0 30px rgba(0,0,0,0.1)'
              }}
            >
              <motion.div
                animate={{
                  y: [0, -10, 0],
                  rotate: [0, 3, -3, 0]
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
                className="pixel-avatar pixel-avatar-large"
                style={{
                  width: '120px',
                  height: '120px',
                  fontSize: '60px',
                  background: getPixelColorClass(avatarColor),
                  margin: '0 auto 16px'
                }}
              >
                {avatarStyles.find(s => s.style === avatarStyle)?.emoji}
              </motion.div>
              
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 1.5, repeat: Infinity }}
                style={{ fontSize: '48px', marginBottom: '12px' }}
              >
                {moodIcon}
              </motion.div>
              
              {username && (
                <div className="pixel-badge" style={{
                  fontSize: '12px',
                  padding: '8px 16px',
                  background: '#FFE66D',
                  color: '#000'
                }}>
                  ⭐ {username} ⭐
                </div>
              )}
            </motion.div>

            {/* Username */}
            <div>
              <div className="pixel-subtitle" style={{
                fontSize: 'clamp(10px, 2vw, 12px)',
                marginBottom: '12px',
                color: '#000',
                textAlign: 'left'
              }}>
                📝 USERNAME
              </div>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="ENTER YOUR NAME..."
                maxLength={50}
                className="pixel-input"
                style={{ fontSize: 'clamp(10px, 2vw, 12px)' }}
              />
            </div>

            {/* Avatar Style */}
            <div>
              <div className="pixel-subtitle" style={{
                fontSize: 'clamp(10px, 2vw, 12px)',
                marginBottom: '16px',
                color: '#000',
                textAlign: 'left'
              }}>
                🎭 AVATAR STYLE
              </div>
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))',
                gap: '12px'
              }}>
                {avatarStyles.map(({ style, emoji, label }) => (
                  <motion.button
                    key={style}
                    type="button"
                    onClick={() => setAvatarStyle(style)}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="pixel-panel"
                    style={{
                      padding: '16px',
                      background: avatarStyle === style ? '#FFE66D' : '#FFF',
                      border: `4px solid ${avatarStyle === style ? '#FF6B6B' : '#000'}`,
                      cursor: 'pointer',
                      textAlign: 'center',
                      boxShadow: avatarStyle === style 
                        ? '6px 6px 0 #FF6B6B' 
                        : '4px 4px 0 #000'
                    }}
                  >
                    <div style={{ fontSize: 'clamp(32px, 8vw, 48px)', marginBottom: '8px' }}>
                      {emoji}
                    </div>
                    <div style={{
                      fontFamily: 'Press Start 2P, cursive',
                      fontSize: 'clamp(8px, 1.5vw, 10px)',
                      color: '#000'
                    }}>
                      {label.toUpperCase()}
                    </div>
                  </motion.button>
                ))}
              </div>
            </div>

            {/* Color */}
            <div>
              <div className="pixel-subtitle" style={{
                fontSize: 'clamp(10px, 2vw, 12px)',
                marginBottom: '16px',
                color: '#000',
                textAlign: 'left'
              }}>
                🎨 COLOR
              </div>
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(60px, 1fr))',
                gap: '12px'
              }}>
                {colors.map((color) => (
                  <motion.button
                    key={color}
                    type="button"
                    onClick={() => setAvatarColor(color)}
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    style={{
                      width: '100%',
                      height: '60px',
                      background: getPixelColorClass(color),
                      border: `4px solid ${avatarColor === color ? '#000' : '#000'}`,
                      cursor: 'pointer',
                      boxShadow: avatarColor === color 
                        ? '6px 6px 0 #000, inset 0 0 0 4px #FFF' 
                        : '4px 4px 0 #000'
                    }}
                  />
                ))}
              </div>
            </div>

            {/* Mood */}
            <div>
              <div className="pixel-subtitle" style={{
                fontSize: 'clamp(10px, 2vw, 12px)',
                marginBottom: '16px',
                color: '#000',
                textAlign: 'left'
              }}>
                😊 MOOD ICON
              </div>
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(70px, 1fr))',
                gap: '12px'
              }}>
                {moods.map((mood) => (
                  <motion.button
                    key={mood}
                    type="button"
                    onClick={() => setMoodIcon(mood)}
                    whileHover={{ scale: 1.1, rotate: 5 }}
                    whileTap={{ scale: 0.9 }}
                    className="pixel-panel"
                    style={{
                      padding: '12px',
                      fontSize: 'clamp(24px, 6vw, 36px)',
                      background: moodIcon === mood ? '#4ECDC4' : '#FFF',
                      border: `4px solid ${moodIcon === mood ? '#000' : '#000'}`,
                      cursor: 'pointer',
                      boxShadow: moodIcon === mood 
                        ? '6px 6px 0 #000' 
                        : '4px 4px 0 #000'
                    }}
                  >
                    {mood}
                  </motion.button>
                ))}
              </div>
            </div>

            {/* Bio */}
            <div>
              <div className="pixel-subtitle" style={{
                fontSize: 'clamp(10px, 2vw, 12px)',
                marginBottom: '12px',
                color: '#000',
                textAlign: 'left'
              }}>
                📖 BIO (OPTIONAL)
              </div>
              <textarea
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                placeholder="TELL US ABOUT YOURSELF..."
                maxLength={500}
                rows={3}
                className="pixel-input"
                style={{
                  fontSize: 'clamp(10px, 2vw, 12px)',
                  resize: 'none'
                }}
              />
            </div>

            {/* LinkedIn URL */}
            <div>
              <div className="pixel-subtitle" style={{
                fontSize: 'clamp(10px, 2vw, 12px)',
                marginBottom: '12px',
                color: '#000',
                textAlign: 'left'
              }}>
                🔗 LINKEDIN PROFILE (OPTIONAL)
              </div>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
                <input
                  type="url"
                  value={linkedinUrl}
                  onChange={(e) => setLinkedinUrl(e.target.value)}
                  placeholder="https://linkedin.com/in/username"
                  className="pixel-input"
                  style={{ fontSize: 'clamp(10px, 2vw, 12px)', flex: 1 }}
                />
                {linkedinUrl.trim() && !profileData && (
                  <motion.button
                    type="button"
                    onClick={handleScrapeLinkedIn}
                    disabled={scrapingLinkedIn}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="pixel-button"
                    style={{
                      padding: '12px 16px',
                      background: scrapingLinkedIn ? '#95E1D3' : '#4ECDC4',
                      fontSize: 'clamp(8px, 1.5vw, 10px)',
                      whiteSpace: 'nowrap'
                    }}
                  >
                    {scrapingLinkedIn ? '⏳ SCRAPING...' : '🔍 PREVIEW'}
                  </motion.button>
                )}
              </div>
              <div style={{
                fontSize: 'clamp(8px, 1.5vw, 10px)',
                color: '#666',
                marginTop: '8px',
                fontFamily: 'Press Start 2P, cursive'
              }}>
                {profileData ? '✅ PROFILE LOADED' : 'ADD YOUR LINKEDIN TO PERSONALIZE YOUR AI EXPERIENCE'}
              </div>
            </div>

            {error && (
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="pixel-panel"
                style={{
                  background: '#FF6B6B',
                  color: '#FFF',
                  padding: '16px',
                  fontSize: 'clamp(10px, 2vw, 12px)',
                  textAlign: 'center'
                }}
              >
                ⚠️ {error}
              </motion.div>
            )}

            {/* Submit */}
            <motion.button
              type="submit"
              disabled={loading || !username.trim()}
              whileHover={{ scale: loading ? 1 : 1.02 }}
              whileTap={{ scale: loading ? 1 : 0.98 }}
              className="pixel-btn pixel-btn-accent"
              style={{
                width: '100%',
                fontSize: 'clamp(12px, 2vw, 16px)',
                padding: 'clamp(16px, 3vw, 20px)',
                background: loading || !username.trim() ? '#AAA' : '#FFE66D',
                cursor: loading || !username.trim() ? 'not-allowed' : 'pointer',
                animation: loading || !username.trim() ? 'none' : 'pulse 2s ease-in-out infinite'
              }}
            >
              {loading ? '⏳ CREATING...' : '⚡ ENTER THE REALM ⚡'}
            </motion.button>
          </form>

          {/* Footer tip */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            style={{
              marginTop: '24px',
              textAlign: 'center',
              fontSize: 'clamp(8px, 1.5vw, 10px)',
              color: '#666',
              fontFamily: 'Press Start 2P, cursive'
            }}
          >
            💡 TIP: CHOOSE WISELY! YOUR CHARACTER REPRESENTS YOU! 💡
          </motion.div>
        </motion.div>
      </div>

      {/* LinkedIn Confirmation Dialog */}
      {showConfirmDialog && profileData && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.8)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px'
        }}>
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="pixel-panel pixel-game-border"
            style={{
              background: '#FFF',
              maxWidth: '600px',
              width: '100%',
              maxHeight: '80vh',
              overflow: 'auto'
            }}
          >
            <h2 className="pixel-title" style={{
              fontSize: 'clamp(14px, 3vw, 20px)',
              marginBottom: '24px',
              color: '#000'
            }}>
              ✅ CONFIRM YOUR PROFILE
            </h2>

            <div style={{
              background: 'black',
              padding: '16px',
              borderRadius: '8px',
              marginBottom: '24px',
              fontFamily: 'Press Start 2P, cursive',
              fontSize: 'clamp(8px, 1.5vw, 10px)',
              lineHeight: '1.8'
            }}>
              {profileData.full_name && (
                <div style={{ marginBottom: '12px' }}>
                  <strong>👤 NAME:</strong> {profileData.full_name}
                </div>
              )}
              {profileData.headline && (
                <div style={{ marginBottom: '12px' }}>
                  <strong>💼 HEADLINE:</strong> {profileData.headline}
                </div>
              )}
              {profileData.location && (
                <div style={{ marginBottom: '12px' }}>
                  <strong>📍 LOCATION:</strong> {profileData.location}
                </div>
              )}
              {profileData.company && (
                <div style={{ marginBottom: '12px' }}>
                  <strong>🏢 COMPANY:</strong> {profileData.company}
                </div>
              )}
              {profileData.persona && (
                <div style={{ marginTop: '16px', padding: '12px', background: 'black', borderRadius: '4px' }}>
                  <strong>🎯 AI PERSONA:</strong><br />
                  {profileData.persona}
                </div>
              )}
            </div>

            <div style={{
              fontSize: 'clamp(8px, 1.5vw, 10px)',
              color: '#666',
              marginBottom: '24px',
              fontFamily: 'Press Start 2P, cursive',
              lineHeight: '1.6'
            }}>
              ℹ️ THIS INFORMATION WILL BE USED TO PERSONALIZE YOUR AI INTERACTIONS. IS THIS CORRECT?
            </div>

            <div style={{ display: 'flex', gap: '12px' }}>
              <motion.button
                onClick={() => setShowConfirmDialog(false)}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="pixel-button"
                style={{
                  flex: 1,
                  padding: '16px',
                  background: '#FF6B6B',
                  fontSize: 'clamp(10px, 2vw, 12px)'
                }}
              >
                ❌ EDIT
              </motion.button>
              <motion.button
                onClick={handleConfirmProfile}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="pixel-button"
                style={{
                  flex: 1,
                  padding: '16px',
                  background: '#4ECDC4',
                  fontSize: 'clamp(10px, 2vw, 12px)'
                }}
              >
                ✅ CONFIRM
              </motion.button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}

