import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, AlertTriangle, Shield, Heart } from 'lucide-react'
import { socketService } from '../services/socketService'
import { UserModerationData, ModerationWarningData, CrisisResourcesData } from '../types'

interface Notification {
  id: string
  type: 'warning' | 'mute' | 'ban' | 'crisis'
  title: string
  message: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  timestamp: Date
  autoHide?: boolean
  duration?: number
}

export const ModerationNotifications = () => {
  const [notifications, setNotifications] = useState<Notification[]>([])

  useEffect(() => {
    // Listen for moderation events from multi-agent system
    const handleUserBanned = (data: UserModerationData) => {
      addNotification({
        id: `ban-${Date.now()}`,
        type: 'ban',
        title: '🚫 Account Banned',
        message: `You have been banned: ${data.reason}`,
        severity: 'critical',
        autoHide: false
      })
    }

    const handleUserMuted = (data: UserModerationData) => {
      addNotification({
        id: `mute-${Date.now()}`,
        type: 'mute',
        title: '🔇 Temporarily Muted',
        message: `You are muted for ${data.duration || 300} seconds: ${data.reason}`,
        severity: 'high',
        autoHide: true,
        duration: (data.duration || 300) * 1000
      })
    }

    const handleModerationWarning = (data: ModerationWarningData) => {
      addNotification({
        id: `warning-${Date.now()}`,
        type: 'warning',
        title: '⚠️ Moderation Warning',
        message: data.message,
        severity: data.severity,
        autoHide: true,
        duration: 8000
      })
    }

    const handleCrisisResources = (data: CrisisResourcesData) => {
      addNotification({
        id: `crisis-${Date.now()}`,
        type: 'crisis',
        title: '🚨 Crisis Support Available',
        message: data.message,
        severity: 'critical',
        autoHide: false
      })
    }

    // Register event listeners
    socketService.on('user_banned', handleUserBanned)
    socketService.on('user_muted', handleUserMuted)
    socketService.on('moderation_warning', handleModerationWarning)
    socketService.on('crisis_resources', handleCrisisResources)

    return () => {
      socketService.off('user_banned', handleUserBanned)
      socketService.off('user_muted', handleUserMuted)
      socketService.off('moderation_warning', handleModerationWarning)
      socketService.off('crisis_resources', handleCrisisResources)
    }
  }, [])

  const addNotification = (notification: Omit<Notification, 'timestamp'>) => {
    const newNotification: Notification = {
      ...notification,
      timestamp: new Date()
    }

    setNotifications(prev => [newNotification, ...prev])

    // Auto-hide after duration if specified
    if (notification.autoHide && notification.duration) {
      setTimeout(() => {
        removeNotification(newNotification.id)
      }, notification.duration)
    }
  }

  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id))
  }

  const getNotificationStyle = (type: Notification['type'], severity: Notification['severity']) => {
    const styles = {
      ban: {
        background: 'linear-gradient(135deg, #dc2626, #b91c1c)',
        border: '4px solid #7f1d1d',
        icon: <Shield className="w-6 h-6" />
      },
      mute: {
        background: 'linear-gradient(135deg, #ea580c, #dc2626)',
        border: '4px solid #7f1d1d',
        icon: <AlertTriangle className="w-6 h-6" />
      },
      warning: {
        background: 'linear-gradient(135deg, #f59e0b, #d97706)',
        border: '4px solid #78350f',
        icon: <AlertTriangle className="w-6 h-6" />
      },
      crisis: {
        background: 'linear-gradient(135deg, #7c3aed, #5b21b6)',
        border: '4px solid #581c87',
        icon: <Heart className="w-6 h-6" />
      }
    }

    return styles[type] || styles.warning
  }

  const getSeverityColor = (severity: Notification['severity']) => {
    const colors = {
      low: '#fbbf24',
      medium: '#f97316',
      high: '#ef4444',
      critical: '#7c2d12'
    }
    return colors[severity] || colors.medium
  }

  return (
    <div style={{
      position: 'fixed',
      top: '80px',
      right: '20px',
      zIndex: 9999,
      maxWidth: '400px',
      width: '100%'
    }}>
      <AnimatePresence>
        {notifications.map((notification) => {
          const style = getNotificationStyle(notification.type, notification.severity)

          return (
            <motion.div
              key={notification.id}
              initial={{ opacity: 0, x: 400, scale: 0.8 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 400, scale: 0.8 }}
              transition={{
                type: "spring",
                stiffness: 300,
                damping: 30
              }}
              style={{
                marginBottom: '12px'
              }}
            >
              <div style={{
                background: style.background,
                border: style.border,
                borderRadius: '8px',
                padding: '16px',
                boxShadow: '8px 8px 0 rgba(0,0,0,0.3)',
                position: 'relative',
                overflow: 'hidden'
              }}>
                {/* Animated background pulse for critical notifications */}
                {notification.severity === 'critical' && (
                  <motion.div
                    animate={{
                      opacity: [0.1, 0.3, 0.1],
                    }}
                    transition={{
                      duration: 2,
                      repeat: Infinity,
                      ease: "easeInOut"
                    }}
                    style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0,
                      bottom: 0,
                      background: 'radial-gradient(circle, rgba(255,255,255,0.3) 0%, transparent 70%)'
                    }}
                  />
                )}

                <div style={{
                  position: 'relative',
                  zIndex: 1,
                  display: 'flex',
                  gap: '12px',
                  alignItems: 'flex-start'
                }}>
                  <div style={{
                    color: '#fff',
                    fontSize: '24px',
                    filter: 'drop-shadow(2px 2px 0 rgba(0,0,0,0.5))'
                  }}>
                    {style.icon}
                  </div>

                  <div style={{ flex: 1 }}>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      marginBottom: '8px'
                    }}>
                      <h3 style={{
                        fontFamily: 'Press Start 2P, cursive',
                        fontSize: '12px',
                        color: '#fff',
                        textShadow: '2px 2px 0 rgba(0,0,0,0.5)',
                        margin: 0
                      }}>
                        {notification.title}
                      </h3>

                      <span style={{
                        fontSize: '8px',
                        background: getSeverityColor(notification.severity),
                        color: '#000',
                        padding: '2px 6px',
                        border: '2px solid #000',
                        borderRadius: '4px',
                        fontWeight: 'bold'
                      }}>
                        {notification.severity.toUpperCase()}
                      </span>
                    </div>

                    <p style={{
                      fontSize: '10px',
                      color: '#fff',
                      lineHeight: '1.4',
                      margin: 0,
                      textShadow: '1px 1px 0 rgba(0,0,0,0.5)'
                    }}>
                      {notification.message}
                    </p>

                    {/* Crisis resources */}
                    {notification.type === 'crisis' && (
                      <div style={{
                        marginTop: '12px',
                        padding: '8px',
                        background: 'rgba(255,255,255,0.2)',
                        border: '2px solid rgba(255,255,255,0.3)',
                        borderRadius: '4px'
                      }}>
                        <p style={{
                          fontSize: '8px',
                          color: '#fff',
                          margin: '0 0 8px 0',
                          fontWeight: 'bold'
                        }}>
                          Available Resources:
                        </p>
                        <div style={{ fontSize: '8px', color: '#fff' }}>
                          • 988 Suicide & Crisis Lifeline<br/>
                          • Crisis Text Line: HOME to 741741<br/>
                          • Emergency: 911
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Close button */}
                  <button
                    onClick={() => removeNotification(notification.id)}
                    style={{
                      background: 'rgba(255,255,255,0.2)',
                      border: '2px solid rgba(255,255,255,0.3)',
                      color: '#fff',
                      width: '24px',
                      height: '24px',
                      borderRadius: '50%',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '12px'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = 'rgba(255,255,255,0.3)'
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'rgba(255,255,255,0.2)'
                    }}
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </motion.div>
          )
        })}
      </AnimatePresence>
    </div>
  )
}
