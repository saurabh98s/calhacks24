import Phaser from 'phaser'
import { PlayerController } from './PlayerController'
import { GAME_CONFIG } from './config'
import { Position } from '../types'

interface Avatar {
  userId: string
  username: string
  sprite: Phaser.GameObjects.Sprite
  nameText: Phaser.GameObjects.Text
  speechBubble?: Phaser.GameObjects.Container
}

export class GameScene extends Phaser.Scene {
  private player!: PlayerController
  private avatars: Map<string, Avatar> = new Map()
  private cursors!: Phaser.Types.Input.Keyboard.CursorKeys
  private moveCallback?: (position: Position) => void
  private clickToMove: boolean = true

  constructor() {
    super({ key: 'GameScene' })
  }

  init(data: any) {
    this.moveCallback = data.onMove
  }

  preload() {
    // Create simple colored squares for avatars (placeholder)
    this.createAvatarTextures()
    
    // Create door textures for tutorial hallway
    this.createDoorTextures()
  }

  create() {
    // Set up world bounds with buffer to prevent overflow
    this.physics.world.setBounds(0, 0, GAME_CONFIG.WIDTH, GAME_CONFIG.HEIGHT)
    
    // Set camera bounds to prevent scrolling/viewport movement
    this.cameras.main.setBounds(0, 0, GAME_CONFIG.WIDTH, GAME_CONFIG.HEIGHT)
    this.cameras.main.setScroll(0, 0)

    // Create background
    this.add.rectangle(
      GAME_CONFIG.WIDTH / 2,
      GAME_CONFIG.HEIGHT / 2,
      GAME_CONFIG.WIDTH,
      GAME_CONFIG.HEIGHT,
      0x16213e
    )

    // Create floor
    const floor = this.add.rectangle(
      GAME_CONFIG.WIDTH / 2,
      GAME_CONFIG.HEIGHT - 50,
      GAME_CONFIG.WIDTH,
      100,
      0x0f3460
    )

    // Set up input
    this.cursors = this.input.keyboard!.createCursorKeys()

    // Click to move
    this.input.on('pointerdown', (pointer: Phaser.Input.Pointer) => {
      if (this.clickToMove && this.player) {
        this.player.moveTo(pointer.x, pointer.y)
      }
    })
  }

  update(time: number, delta: number) {
    if (this.player) {
      this.player.update(this.cursors)
    }
  }

  // Create player avatar
  createPlayer(userId: string, username: string, avatarStyle: string, avatarColor: string, x: number, y: number) {
    this.player = new PlayerController(this, userId, username, avatarStyle, avatarColor, x, y)
    
    // Set move callback
    if (this.moveCallback) {
      this.player.setMoveCallback(this.moveCallback)
    }

    return this.player
  }

  // Add other player avatar
  addAvatar(userId: string, username: string, avatarStyle: string, avatarColor: string, x: number, y: number) {
    if (this.avatars.has(userId)) {
      return
    }

    const texture = this.getAvatarTexture(avatarStyle, avatarColor)
    const sprite = this.add.sprite(x, y, texture)
    sprite.setScale(GAME_CONFIG.SPRITE_SCALE)

    // Add improved name label with better styling
    const nameText = this.add.text(x, y - 45, username, {
      fontSize: '14px',
      color: '#ffffff',
      backgroundColor: '#00000099',
      padding: { x: 8, y: 4 },
      fontFamily: 'Arial, sans-serif',
      fontStyle: 'bold'
    })
    nameText.setOrigin(0.5)
    nameText.setStroke('#000000', 2)
    nameText.setShadow(0, 2, '#000000', 2, false, true)
    
    // Add idle animation (constrained to prevent UI jump)
    this.tweens.add({
      targets: sprite,
      y: y - 2,  // Reduced movement to prevent overflow
      duration: 800,
      ease: 'Sine.easeInOut',
      yoyo: true,
      repeat: -1
    })
    
    // Ensure sprite and text stay within bounds
    sprite.setDepth(10)
    nameText.setDepth(11)  // Name above sprite

    this.avatars.set(userId, {
      userId,
      username,
      sprite,
      nameText,
    })
  }

  // Update avatar position
  updateAvatarPosition(userId: string, position: Position) {
    const avatar = this.avatars.get(userId)
    if (avatar) {
      // Smooth movement using tween
      this.tweens.add({
        targets: avatar.sprite,
        x: position.x,
        y: position.y,
        duration: 200,
        ease: 'Power2',
      })

      this.tweens.add({
        targets: avatar.nameText,
        x: position.x,
        y: position.y - 45,
        duration: 200,
        ease: 'Power2',
      })
    }
  }

  // Remove avatar
  removeAvatar(userId: string) {
    const avatar = this.avatars.get(userId)
    if (avatar) {
      avatar.sprite.destroy()
      avatar.nameText.destroy()
      if (avatar.speechBubble) {
        avatar.speechBubble.destroy()
      }
      this.avatars.delete(userId)
    }
  }

  // Show speech bubble
  showSpeechBubble(userId: string, message: string, duration: number = 3000) {
    const avatar = this.player?.getUserId() === userId ? this.player.getSprite() : this.avatars.get(userId)?.sprite
    
    if (!avatar) return

    // Create speech bubble
    const bubbleWidth = Math.min(message.length * 8, 200)
    const bubbleHeight = 40
    const bubbleX = avatar.x
    const bubbleY = avatar.y - 60

    const bubble = this.add.graphics()
    bubble.fillStyle(0xffffff, 0.9)
    bubble.fillRoundedRect(bubbleX - bubbleWidth / 2, bubbleY - bubbleHeight / 2, bubbleWidth, bubbleHeight, 8)
    bubble.lineStyle(2, 0x000000, 1)
    bubble.strokeRoundedRect(bubbleX - bubbleWidth / 2, bubbleY - bubbleHeight / 2, bubbleWidth, bubbleHeight, 8)

    // Add triangle pointer
    const triangle = this.add.triangle(bubbleX, bubbleY + bubbleHeight / 2, 0, 0, 10, 15, -10, 15, 0xffffff)

    const text = this.add.text(bubbleX, bubbleY, message, {
      fontSize: '12px',
      color: '#000000',
      wordWrap: { width: bubbleWidth - 10 },
    })
    text.setOrigin(0.5)

    const container = this.add.container(0, 0, [bubble, triangle, text])

    // Auto-hide after duration
    this.time.delayedCall(duration, () => {
      container.destroy()
    })
  }

  // Create Mario-style pixel-art avatar textures
  private createAvatarTextures() {
    const styles = ['human', 'cat', 'robot', 'alien']
    const colors = {
      blue: 0x3b82f6,
      red: 0xef4444,
      green: 0x10b981,
      purple: 0xa855f7,
      orange: 0xf97316,
      pink: 0xec4899,
    }

    styles.forEach(style => {
      Object.entries(colors).forEach(([colorName, colorValue]) => {
        const key = `${style}_${colorName}`
        const graphics = this.make.graphics({ x: 0, y: 0, add: false })
        
        // Draw Mario-style pixel perfect avatar
        if (style === 'human') {
          // Cap/Hair (darker shade)
          const darkColor = this.darkenColor(colorValue, 0.7)
          graphics.fillStyle(darkColor, 1)
          graphics.fillRect(8, 8, 32, 8)  // Hat brim
          graphics.fillRect(12, 4, 24, 4)  // Hat top
          
          // Face (skin tone)
          graphics.fillStyle(0xffdbac, 1)
          graphics.fillRect(12, 16, 24, 16)  // Face
          
          // Eyes (Mario style)
          graphics.fillStyle(0x000000, 1)
          graphics.fillRect(16, 20, 6, 6)  // Left eye
          graphics.fillRect(26, 20, 6, 6)  // Right eye
          graphics.fillStyle(0xffffff, 1)
          graphics.fillRect(18, 22, 2, 2)  // Eye shine left
          graphics.fillRect(28, 22, 2, 2)  // Eye shine right
          
          // Nose
          graphics.fillStyle(0xc68642, 1)
          graphics.fillRect(22, 26, 4, 4)
          
          // Shirt
          graphics.fillStyle(colorValue, 1)
          graphics.fillRect(14, 32, 20, 20)  // Torso
          
          // Arms
          graphics.fillStyle(colorValue, 0.9)
          graphics.fillRect(8, 36, 6, 12)  // Left arm
          graphics.fillRect(34, 36, 6, 12)  // Right arm
          
          // Hands (skin tone)
          graphics.fillStyle(0xffdbac, 1)
          graphics.fillRect(8, 48, 6, 4)
          graphics.fillRect(34, 48, 6, 4)
          
          // Pants (darker)
          graphics.fillStyle(darkColor, 1)
          graphics.fillRect(16, 52, 7, 12)  // Left leg
          graphics.fillRect(25, 52, 7, 12)  // Right leg
          
          // Shoes (black)
          graphics.fillStyle(0x8B4513, 1)
          graphics.fillRect(14, 60, 9, 4)
          graphics.fillRect(25, 60, 9, 4)
          
        } else if (style === 'cat') {
          // Ears (pixelated triangles)
          graphics.fillStyle(colorValue, 1)
          graphics.fillRect(10, 8, 6, 6)   // Left ear
          graphics.fillRect(32, 8, 6, 6)   // Right ear
          graphics.fillRect(12, 14, 4, 2)
          graphics.fillRect(32, 14, 4, 2)
          
          // Head
          graphics.fillRect(14, 16, 20, 16)  // Main head
          
          // Eyes (big cute anime style)
          graphics.fillStyle(0x000000, 1)
          graphics.fillRect(16, 20, 6, 8)   // Left eye
          graphics.fillRect(26, 20, 6, 8)   // Right eye
          graphics.fillStyle(0xffffff, 1)
          graphics.fillRect(19, 22, 2, 3)   // Left shine
          graphics.fillRect(29, 22, 2, 3)   // Right shine
          
          // Nose
          graphics.fillStyle(0xff69b4, 1)
          graphics.fillRect(22, 28, 4, 2)
          
          // Mouth/Whisker dots
          graphics.fillStyle(0x000000, 1)
          graphics.fillRect(14, 26, 2, 2)
          graphics.fillRect(32, 26, 2, 2)
          
          // Body
          graphics.fillStyle(colorValue, 1)
          graphics.fillRect(16, 32, 16, 20)
          
          // Belly (lighter)
          graphics.fillStyle(this.lightenColor(colorValue, 1.3), 1)
          graphics.fillRect(20, 36, 8, 12)
          
          // Paws
          graphics.fillStyle(colorValue, 1)
          graphics.fillRect(14, 52, 7, 8)   // Left paw
          graphics.fillRect(27, 52, 7, 8)   // Right paw
          
          // Tail
          graphics.fillRect(34, 36, 4, 16)
          graphics.fillRect(36, 48, 4, 8)
          
        } else if (style === 'robot') {
          // Antenna
          graphics.fillStyle(colorValue, 1)
          graphics.fillRect(22, 2, 4, 6)
          graphics.fillRect(20, 8, 8, 2)
          
          // Head (blocky)
          graphics.fillStyle(colorValue, 1)
          graphics.fillRect(14, 10, 20, 18)
          
          // Screen/Face panel (darker)
          graphics.fillStyle(0x000000, 0.3)
          graphics.fillRect(16, 12, 16, 14)
          
          // Eyes (LED/Screen)
          graphics.fillStyle(0x00ff00, 1)
          graphics.fillRect(18, 16, 5, 6)   // Left eye
          graphics.fillRect(25, 16, 5, 6)   // Right eye
          graphics.fillStyle(0x00ff00, 0.5)
          graphics.fillRect(19, 17, 3, 4)
          graphics.fillRect(26, 17, 3, 4)
          
          // Mouth (LED bar)
          graphics.fillStyle(0xff0000, 1)
          graphics.fillRect(20, 24, 8, 2)
          
          // Body
          graphics.fillStyle(colorValue, 1)
          graphics.fillRect(16, 28, 16, 20)
          
          // Chest plate (darker)
          graphics.fillStyle(this.darkenColor(colorValue, 0.7), 1)
          graphics.fillRect(20, 32, 8, 12)
          
          // Bolts
          graphics.fillStyle(0xcccccc, 1)
          graphics.fillRect(18, 14, 2, 2)
          graphics.fillRect(28, 14, 2, 2)
          graphics.fillRect(18, 30, 2, 2)
          graphics.fillRect(28, 30, 2, 2)
          
          // Arms (blocky)
          graphics.fillStyle(colorValue, 1)
          graphics.fillRect(10, 30, 6, 14)
          graphics.fillRect(32, 30, 6, 14)
          
          // Legs
          graphics.fillRect(18, 48, 6, 12)
          graphics.fillRect(24, 48, 6, 12)
          
        } else { // alien
          // Antenna balls
          graphics.fillStyle(colorValue, 1)
          graphics.fillRect(14, 2, 4, 2)
          graphics.fillRect(30, 2, 4, 2)
          graphics.fillRect(16, 4, 2, 6)
          graphics.fillRect(30, 4, 2, 6)
          
          // Large head (inverted teardrop)
          graphics.fillRect(12, 10, 24, 4)   // Top
          graphics.fillRect(10, 14, 28, 8)   // Middle wide
          graphics.fillRect(12, 22, 24, 6)   // Lower
          graphics.fillRect(16, 28, 16, 4)   // Bottom
          
          // Giant alien eyes (black)
          graphics.fillStyle(0x000000, 1)
          graphics.fillRect(14, 14, 8, 10)   // Left eye
          graphics.fillRect(26, 14, 8, 10)   // Right eye
          
          // Eye shine (white highlight)
          graphics.fillStyle(0xffffff, 1)
          graphics.fillRect(16, 16, 3, 4)
          graphics.fillRect(28, 16, 3, 4)
          
          // Small body (skinny)
          graphics.fillStyle(colorValue, 1)
          graphics.fillRect(18, 32, 12, 16)
          
          // Arms (very thin)
          graphics.fillRect(12, 34, 4, 12)
          graphics.fillRect(32, 34, 4, 12)
          
          // Three-fingered hands
          graphics.fillRect(10, 46, 6, 2)
          graphics.fillRect(32, 46, 6, 2)
          
          // Thin legs
          graphics.fillRect(19, 48, 4, 12)
          graphics.fillRect(25, 48, 4, 12)
          
          // Big feet
          graphics.fillRect(17, 60, 7, 4)
          graphics.fillRect(24, 60, 7, 4)
        }
        
        graphics.generateTexture(key, 48, 64)
        graphics.destroy()
      })
    })
  }

  // Helper function to darken colors
  private darkenColor(color: number, factor: number): number {
    const r = Math.floor(((color >> 16) & 0xFF) * factor)
    const g = Math.floor(((color >> 8) & 0xFF) * factor)
    const b = Math.floor((color & 0xFF) * factor)
    return (r << 16) | (g << 8) | b
  }

  // Helper function to lighten colors
  private lightenColor(color: number, factor: number): number {
    const r = Math.min(255, Math.floor(((color >> 16) & 0xFF) * factor))
    const g = Math.min(255, Math.floor(((color >> 8) & 0xFF) * factor))
    const b = Math.min(255, Math.floor((color & 0xFF) * factor))
    return (r << 16) | (g << 8) | b
  }

  private createDoorTextures() {
    // Updated door types: D&D, AA, Therapy, Private
    const doorConfigs = [
      { type: 'dnd', color: 0x8b4513, icon: '🎲' },           // Brown for D&D
      { type: 'aa', color: 0x10b981, icon: '💚' },            // Green for AA
      { type: 'therapy', color: 0x6366f1, icon: '🧠' },       // Blue for Therapy
      { type: 'private', color: 0x8b5cf6, icon: '🔒' }        // Purple for Private
    ]

    doorConfigs.forEach(({ type, color, icon }) => {
      const graphics = this.make.graphics({ x: 0, y: 0, add: false })
      
      // Door body
      graphics.fillStyle(color, 1)
      graphics.fillRoundedRect(0, 0, 60, 80, 8)
      
      // Door border
      graphics.lineStyle(3, 0x000000, 1)
      graphics.strokeRoundedRect(0, 0, 60, 80, 8)
      
      // Door knob
      graphics.fillStyle(0xffd700, 1)
      graphics.fillCircle(45, 40, 4)
      graphics.lineStyle(1, 0x000000, 1)
      graphics.strokeCircle(45, 40, 4)
      
      // Door panel accent
      graphics.lineStyle(2, 0x000000, 0.3)
      graphics.strokeRoundedRect(8, 10, 44, 60, 4)
      
      graphics.generateTexture(`door_${type}`, 60, 80)
      graphics.destroy()
    })
  }

  private getAvatarTexture(style: string, color: string): string {
    return `${style}_${color}`
  }

  // Create doors for tutorial hallway
  createDoors(doors: Array<{ x: number; y: number; type: string; label: string }>) {
    doors.forEach(door => {
      const doorSprite = this.add.sprite(door.x, door.y, `door_${door.type}`)
      doorSprite.setInteractive({ 
        useHandCursor: true,
        pixelPerfect: false,
        alphaTolerance: 1
      })
      doorSprite.setScale(1.2)
      
      const label = this.add.text(door.x, door.y + 60, door.label, {
        fontSize: '16px',
        color: '#ffffff',
        backgroundColor: '#000000aa',
        padding: { x: 8, y: 4 },
        align: 'center'
      })
      label.setOrigin(0.5)

      // Add hover effect
      doorSprite.on('pointerover', () => {
        doorSprite.setTint(0xaaaaaa)
        this.tweens.add({
          targets: doorSprite,
          scaleX: 1.3,
          scaleY: 1.3,
          duration: 200,
          ease: 'Power2'
        })
      })

      doorSprite.on('pointerout', () => {
        doorSprite.clearTint()
        this.tweens.add({
          targets: doorSprite,
          scaleX: 1.2,
          scaleY: 1.2,
          duration: 200,
          ease: 'Power2'
        })
      })

      doorSprite.on('pointerdown', () => {
        console.log('Door clicked:', door.type)
        
        // Visual feedback
        this.tweens.add({
          targets: doorSprite,
          scaleX: 1.1,
          scaleY: 1.1,
          duration: 100,
          yoyo: true,
          onComplete: () => {
            this.events.emit('door-clicked', door.type)
          }
        })
      })
    })
  }

  getPlayer(): PlayerController {
    return this.player
  }
}

