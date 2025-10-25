import Phaser from 'phaser'
import { GAME_CONFIG } from './config'
import { Position } from '../types'

export class PlayerController {
  private scene: Phaser.Scene
  private userId: string
  private username: string
  private sprite: Phaser.GameObjects.Sprite
  private nameText: Phaser.GameObjects.Text
  private body: Phaser.Physics.Arcade.Body
  private targetPosition: Position | null = null
  private moveCallback?: (position: Position) => void
  private moveThrottle: number = 0
  private readonly MOVE_THROTTLE_MS = 100

  constructor(
    scene: Phaser.Scene,
    userId: string,
    username: string,
    avatarStyle: string,
    avatarColor: string,
    x: number,
    y: number
  ) {
    this.scene = scene
    this.userId = userId
    this.username = username

    // Create sprite
    const texture = `${avatarStyle}_${avatarColor}`
    this.sprite = scene.add.sprite(x, y, texture)
    this.sprite.setScale(GAME_CONFIG.SPRITE_SCALE)

    // Add physics
    scene.physics.add.existing(this.sprite)
    this.body = this.sprite.body as Phaser.Physics.Arcade.Body
    this.body.setCollideWorldBounds(true)

    // Create name label
    this.nameText = scene.add.text(x, y - 40, username, {
      fontSize: '12px',
      color: '#ffffff',
      backgroundColor: '#000000',
      padding: { x: 4, y: 2 },
    })
    this.nameText.setOrigin(0.5)
  }

  update(cursors: Phaser.Types.Input.Keyboard.CursorKeys) {
    let velocityX = 0
    let velocityY = 0

    // Keyboard movement
    if (cursors.left.isDown) {
      velocityX = -GAME_CONFIG.MOVE_SPEED
    } else if (cursors.right.isDown) {
      velocityX = GAME_CONFIG.MOVE_SPEED
    }

    if (cursors.up.isDown) {
      velocityY = -GAME_CONFIG.MOVE_SPEED
    } else if (cursors.down.isDown) {
      velocityY = GAME_CONFIG.MOVE_SPEED
    }

    // Click-to-move
    if (this.targetPosition) {
      const distance = Phaser.Math.Distance.Between(
        this.sprite.x,
        this.sprite.y,
        this.targetPosition.x,
        this.targetPosition.y
      )

      if (distance < 5) {
        this.targetPosition = null
        this.body.setVelocity(0, 0)
      } else {
        const angle = Phaser.Math.Angle.Between(
          this.sprite.x,
          this.sprite.y,
          this.targetPosition.x,
          this.targetPosition.y
        )
        velocityX = Math.cos(angle) * GAME_CONFIG.MOVE_SPEED
        velocityY = Math.sin(angle) * GAME_CONFIG.MOVE_SPEED
      }
    }

    // Apply velocity
    this.body.setVelocity(velocityX, velocityY)

    // Update name position
    this.nameText.setPosition(this.sprite.x, this.sprite.y - 40)

    // Emit position updates (throttled)
    if ((velocityX !== 0 || velocityY !== 0) && this.moveCallback) {
      const now = Date.now()
      if (now - this.moveThrottle > this.MOVE_THROTTLE_MS) {
        this.moveThrottle = now
        this.moveCallback({
          x: this.sprite.x,
          y: this.sprite.y,
        })
      }
    }
  }

  moveTo(x: number, y: number) {
    this.targetPosition = { x, y }
  }

  setMoveCallback(callback: (position: Position) => void) {
    this.moveCallback = callback
  }

  getPosition(): Position {
    return {
      x: this.sprite.x,
      y: this.sprite.y,
    }
  }

  getUserId(): string {
    return this.userId
  }

  getSprite(): Phaser.GameObjects.Sprite {
    return this.sprite
  }

  destroy() {
    this.sprite.destroy()
    this.nameText.destroy()
  }
}

