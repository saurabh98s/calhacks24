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
    // Set up world bounds
    this.physics.world.setBounds(0, 0, GAME_CONFIG.WIDTH, GAME_CONFIG.HEIGHT)

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

    // Add name label
    const nameText = this.add.text(x, y - 40, username, {
      fontSize: '12px',
      color: '#ffffff',
      backgroundColor: '#000000',
      padding: { x: 4, y: 2 },
    })
    nameText.setOrigin(0.5)

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
        ease: 'Linear',
      })

      this.tweens.add({
        targets: avatar.nameText,
        x: position.x,
        y: position.y - 40,
        duration: 200,
        ease: 'Linear',
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

  // Create avatar textures (colored squares as placeholders)
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
        
        // Draw avatar shape based on style
        if (style === 'human') {
          graphics.fillStyle(colorValue, 1)
          graphics.fillCircle(16, 16, 14)
          graphics.fillRect(10, 24, 12, 6)
        } else if (style === 'cat') {
          graphics.fillStyle(colorValue, 1)
          graphics.fillCircle(16, 18, 12)
          graphics.fillTriangle(8, 10, 12, 4, 10, 12)
          graphics.fillTriangle(24, 10, 20, 4, 22, 12)
        } else if (style === 'robot') {
          graphics.fillStyle(colorValue, 1)
          graphics.fillRect(8, 10, 16, 16)
          graphics.fillRect(6, 18, 4, 8)
          graphics.fillRect(22, 18, 4, 8)
        } else {
          graphics.fillStyle(colorValue, 1)
          graphics.fillEllipse(16, 16, 12, 18)
          graphics.fillCircle(12, 14, 3)
          graphics.fillCircle(20, 14, 3)
        }
        
        graphics.generateTexture(key, 32, 32)
        graphics.destroy()
      })
    })
  }

  private createDoorTextures() {
    const doorTypes = ['study', 'support', 'casual', 'private']
    const doorColors = [0x6366f1, 0x10b981, 0xf59e0b, 0x8b5cf6]

    doorTypes.forEach((type, index) => {
      const graphics = this.make.graphics({ x: 0, y: 0, add: false })
      graphics.fillStyle(doorColors[index], 1)
      graphics.fillRoundedRect(0, 0, 60, 80, 8)
      graphics.lineStyle(3, 0x000000, 1)
      graphics.strokeRoundedRect(0, 0, 60, 80, 8)
      
      // Door knob
      graphics.fillStyle(0xffd700, 1)
      graphics.fillCircle(45, 40, 4)
      
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

