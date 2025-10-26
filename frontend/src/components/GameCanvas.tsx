import { useEffect, useRef } from 'react'
import Phaser from 'phaser'
import { GameScene } from '../game/GameScene'
import { createGameConfig } from '../game/config'
import { Position } from '../types'

interface GameCanvasProps {
  roomId: string
  userId: string
  username: string
  avatarStyle: string
  avatarColor: string
  onMove: (position: Position) => void
  onReady: (scene: GameScene) => void
}

export const GameCanvas = ({
  roomId,
  userId,
  username,
  avatarStyle,
  avatarColor,
  onMove,
  onReady,
}: GameCanvasProps) => {
  const gameRef = useRef<Phaser.Game | null>(null)
  const isInitialized = useRef(false)

  useEffect(() => {
    if (isInitialized.current) return

    // Create custom GameScene class that passes data
    class CustomGameScene extends GameScene {
      constructor() {
        super()
      }

      init(data: any) {
        super.init(data)
      }
    }

    // Create game instance
    const config = createGameConfig('game-canvas', CustomGameScene)
    gameRef.current = new Phaser.Game(config)
    
    isInitialized.current = true

    // Wait for scene to be ready
    const checkScene = setInterval(() => {
      const scene = gameRef.current?.scene.getScene('GameScene') as GameScene
      if (scene && scene.sys && scene.sys.settings) {
        clearInterval(checkScene)
        
        // Pass the onMove callback
        scene.scene.start('GameScene', { onMove })
        
        // Wait for create to complete
        scene.events.once('create', () => {
          // Create player after scene is fully created
          setTimeout(() => {
            scene.createPlayer(userId, username, avatarStyle, avatarColor, 400, 300)
            onReady(scene)
          }, 100)
        })
      }
    }, 100)

    // Cleanup
    return () => {
      clearInterval(checkScene)
      if (gameRef.current) {
        gameRef.current.destroy(true)
        gameRef.current = null
        isInitialized.current = false
      }
    }
  }, [])

  return (
    <div style={{
      width: '100%',
      height: '100%',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      overflow: 'hidden',
      position: 'relative'
    }}>
      <div 
        id="game-canvas" 
        style={{
          overflow: 'hidden',
          position: 'relative',
          contain: 'layout style paint',
          isolation: 'isolate'
        }}
      />
    </div>
  )
}

