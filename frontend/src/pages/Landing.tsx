import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import '../styles/retro-game.css'

export default function Landing() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{
      background: 'linear-gradient(135deg, #FF6B6B 0%, #FFE66D 50%, #4ECDC4 100%)',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Animated pixel clouds */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' xmlns='http://www.w3.org/2000/svg'%3E%3Crect width='60' height='60' fill='rgba(255,255,255,0.05)'/%3E%3Crect x='20' y='20' width='20' height='20' fill='rgba(255,255,255,0.1)'/%3E%3C/svg%3E")`,
        animation: 'float 20s linear infinite',
      }} />

      <div className="pixel-container" style={{ maxWidth: '900px', zIndex: 1 }}>
        {/* Game title screen panel */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, type: "spring" }}
          className="pixel-panel pixel-game-border"
          style={{
            background: 'rgba(255, 255, 255, 0.98)',
            textAlign: 'center'
          }}
        >
          {/* Title with pixel art styling */}
          <motion.h1
            className="pixel-title"
            style={{
              fontSize: 'clamp(24px, 8vw, 48px)',
              marginBottom: '32px',
              color: '#000',
              textShadow: '6px 6px 0 #FF6B6B, -2px -2px 0 #4ECDC4'
            }}
            animate={{
              textShadow: [
                '6px 6px 0 #FF6B6B, -2px -2px 0 #4ECDC4',
                '6px 6px 0 #4ECDC4, -2px -2px 0 #FF6B6B',
                '6px 6px 0 #FFE66D, -2px -2px 0 #FF6B6B',
                '6px 6px 0 #FF6B6B, -2px -2px 0 #4ECDC4'
              ]
            }}
            transition={{ duration: 4, repeat: Infinity }}
          >
            ⚔️ ChatRealm ⚔️
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="pixel-subtitle"
            style={{
              fontSize: 'clamp(10px, 2vw, 14px)',
              marginBottom: '40px',
              color: '#000',
              lineHeight: '1.8'
            }}
          >
            🎮 WALK INTO CONVERSATIONS 🎮
            <br />
            🤖 TALK WITH AI ATLAS 🤖
            <br />
            ⭐ MAKE EVERY CHAT ALIVE ⭐
          </motion.p>

          {/* Animated pixel characters */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="pixel-panel-gradient"
            style={{
              padding: '32px',
              marginBottom: '40px',
              minHeight: '200px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '24px',
              flexWrap: 'wrap',
              border: '6px solid #000',
              boxShadow: 'inset 0 0 20px rgba(0,0,0,0.2)'
            }}
          >
            {[
              { emoji: '👤', label: 'PLAYER', color: '#FF6B6B' },
              { emoji: '🐱', label: 'FRIEND', color: '#FFE66D' },
              { emoji: '🤖', label: 'ATLAS', color: '#4ECDC4' },
              { emoji: '👽', label: 'GUEST', color: '#AA96DA' }
            ].map((character, i) => (
              <motion.div
                key={i}
                className="pixel-avatar"
                animate={{
                  y: [0, -15, 0],
                  rotate: [0, 5, -5, 0]
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  delay: i * 0.3,
                  ease: "easeInOut"
                }}
                style={{
                  width: '80px',
                  height: '80px',
                  fontSize: '40px',
                  background: character.color,
                  position: 'relative'
                }}
              >
                {character.emoji}
                <div style={{
                  position: 'absolute',
                  bottom: '-24px',
                  left: '50%',
                  transform: 'translateX(-50%)',
                  fontSize: '8px',
                  whiteSpace: 'nowrap',
                  color: '#FFF',
                  textShadow: '2px 2px 0 #000'
                }}>
                  {character.label}
                </div>
              </motion.div>
            ))}
          </motion.div>

          {/* Stat display */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.7 }}
            style={{
              display: 'flex',
              gap: '16px',
              justifyContent: 'center',
              flexWrap: 'wrap',
              marginBottom: '32px'
            }}
          >
            {[
              { icon: '🎭', label: 'AVATARS', value: '∞' },
              { icon: '💬', label: 'ROOMS', value: '24/7' },
              { icon: '🤖', label: 'AI HOST', value: 'ATLAS' }
            ].map((stat, i) => (
              <div key={i} className="pixel-badge" style={{
                padding: '8px 16px',
                fontSize: 'clamp(8px, 1.5vw, 10px)',
                background: i === 0 ? '#FF6B6B' : i === 1 ? '#FFE66D' : '#4ECDC4',
                color: i === 1 ? '#000' : '#FFF'
              }}>
                {stat.icon} {stat.label}: {stat.value}
              </div>
            ))}
          </motion.div>

          {/* Start button */}
          <motion.button
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.9, type: "spring", stiffness: 200 }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => navigate('/avatar')}
            className="pixel-btn pixel-btn-accent"
            style={{
              fontSize: 'clamp(12px, 2vw, 16px)',
              padding: 'clamp(12px, 2vw, 16px) clamp(24px, 4vw, 40px)',
              marginBottom: '24px',
              background: '#FFE66D',
              animation: 'pulse 2s ease-in-out infinite'
            }}
          >
            ⚡ PRESS START ⚡
          </motion.button>

          {/* Instructions */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.1 }}
            style={{
              fontSize: 'clamp(8px, 1.5vw, 12px)',
              color: '#666',
              lineHeight: '2'
            }}
          >
            <p style={{ fontFamily: 'Press Start 2P, cursive' }}>
              🎮 ENTER ROOMS AS AVATARS<br />
              💭 CHAT WITH CONTEXT-AWARE AI<br />
              🌐 REAL-TIME MULTIPLAYER MAGIC
            </p>
          </motion.div>

          {/* Pixel art decoration */}
          <motion.div
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 2, repeat: Infinity }}
            style={{
              marginTop: '24px',
              fontSize: '16px',
              color: '#FF6B6B'
            }}
          >
            ★ ★ ★
          </motion.div>
        </motion.div>

        {/* Footer */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.3 }}
          style={{
            textAlign: 'center',
            marginTop: '24px',
            fontSize: 'clamp(8px, 1.5vw, 10px)',
            color: '#FFF',
            textShadow: '2px 2px 0 #000'
          }}
        >
          <p style={{ fontFamily: 'Press Start 2P, cursive' }}>
            © 2025 CHATREALM - POWERED BY ATLAS AI
          </p>
        </motion.div>
      </div>

      {/* Add floating animation */}
      <style>{`
        @keyframes float {
          from { background-position: 0 0; }
          to { background-position: 60px 60px; }
        }
      `}</style>
    </div>
  )
}

