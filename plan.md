# Technical Design Document: Multiplayer AI Chat Arena

**Project Name:** Talk To Me  


***

## 1. Executive Summary

**ChatRealm** is a gamified, real-time multiplayer chat platform where users enter virtual "rooms" as avatars, interact with an AI character that maintains individual user context, group dynamics, and conversation flow across diverse scenarios (study groups, support groups, casual hangouts).

**Core Innovation:**
- **Spatial chat UI** - Users "walk" into rooms like a 2D game
- **Context-aware AI** - Tracks each user's emotional state, participation level, conversation history
- **Universal adaptability** - AI persona adapts to room type (AA meeting moderator, study TA, casual bartender)

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND LAYER                        │
│  React + Phaser.js (Game Engine) + Socket.io-client        │
│  - 2D Avatar Movement                                       │
│  - Real-time Chat UI                                        │
│  - Emotion Indicators                                       │
└─────────────────┬───────────────────────────────────────────┘
                  │ WebSocket (Socket.io)
                  │ REST API (HTTP)
┌─────────────────▼───────────────────────────────────────────┐
│                       BACKEND LAYER                          │
│  Python (FastAPI) + Socket.io Server + Redis + PostgreSQL  │
│  - WebSocket Manager                                        │
│  - AI Orchestration Service                                 │
│  - User State Manager                                       │
│  - Room Manager                                             │
└─────────────────┬───────────────────────────────────────────┘
                  │ HTTPS
┌─────────────────▼───────────────────────────────────────────┐
│                      AI INFERENCE LAYER                      │
│  Janitor AI API (https://janitorai.com/hackathon/...)      │
│  - Context: 25,000 tokens                                   │
│  - OpenAI-compatible format                                 │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                       DATA LAYER                             │
│  Redis (Hot State)          PostgreSQL (Persistent)         │
│  - Active users             - User profiles                  │
│  - Room state               - Chat history                   │
│  - Conversation graph       - Room templates                 │
│  - AI response queue        - Analytics (Do it at the end)   │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Docker Architecture

```
docker-compose.yml structure:

services:
  - frontend (React + Nginx)
  - backend (FastAPI + Python 3.11)
  - redis (State cache)
  - postgres (Persistent storage)
  - nginx (Reverse proxy)
```

***

## 3. Technology Stack

### 3.1 Frontend

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | React 18 + TypeScript | UI components, state management |
| **Game Engine** | Phaser.js 3.60+ | 2D avatar movement, spatial chat |
| **Real-time** | Socket.io-client | WebSocket communication |
| **State** | Zustand | Lightweight global state |
| **Styling** | TailwindCSS + Framer Motion | Responsive UI + animations |
| **Icons** | Lucide React | Consistent icon system |

### 3.2 Backend

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | FastAPI 0.104+ | Async API, WebSocket support |
| **WebSocket** | python-socketio | Bidirectional real-time comms |
| **Task Queue** | Celery + Redis | Async AI response processing |
| **ORM** | SQLAlchemy 2.0 | Database interactions |
| **Validation** | Pydantic v2 | Request/response schemas |
| **Auth** | JWT (PyJWT) | Stateless authentication |

### 3.3 Infrastructure

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Containerization** | Docker + Docker Compose | Isolated, reproducible environments |
| **Cache** | Redis 7.2 | Session state, room data, AI queue |
| **Database** | PostgreSQL 15 | User profiles, chat history |
| **Web Server** | Nginx | Static files, reverse proxy |

***

## 4. User Experience Design

### 4.1 Gamified Onboarding Flow

#### **Stage 1: Landing (0-15 seconds)**

```
┌────────────────────────────────────────────────────┐
│                  CHATREALM                         │
│                                                    │
│         [Animated pixel-art world preview]         │
│                                                    │
│     "Walk into conversations. Talk with AI.        │
│           Make every chat feel alive."             │
│                                                    │
│           [START YOUR JOURNEY] 🚀                  │
└────────────────────────────────────────────────────┘
```

**Visual Style:**
- Soft gradient background (warm colors)
- Floating particle effects
- Subtle background music (optional toggle)
- Preview: 3-4 avatar silhouettes moving in mini-world

***

#### **Stage 2: Avatar Creation (15-45 seconds)**

```
┌─────────────────────────────────────────────────────┐
│  Create Your Character                              │
│                                                     │
│  ┌─────────────┐                                   │
│  │   [Avatar]  │  ← Customizable sprite            │
│  │   Preview   │                                   │
│  └─────────────┘                                   │
│                                                     │
│  Name: [_______________]                            │
│                                                     │
│  Avatar Style:                                      │
│  🧑 [Human] 🐱 [Cat] 🤖 [Robot] 👽 [Alien]        │
│                                                     │
│  Mood Icon (for emotion tracking):                 │
│  😊 😐 😔 😤 🤔 😴                                  │
│                                                     │
│  Bio (optional): [____________________]             │
│                                                     │
│  [ENTER THE REALM] →                               │
└─────────────────────────────────────────────────────┘
```

**Technical Implementation:**
- Avatar sprites: 32x32px pixel art (8 base styles × 6 color variants)
- Real-time preview updates as user selects options
- LocalStorage saves preferences for returning users

***

#### **Stage 3: Tutorial Hallway (45-120 seconds)**

**User spawns in "Tutorial Hallway"** - a horizontal corridor with doors

```
Visual Layout:

Background: Cozy hallway, wooden floor, ambient lighting

┌──────────────────────────────────────────────────────────┐
│                                                          │
│  [Door 1]      [Door 2]       [Door 3]      [Your Room] │
│   STUDY        SUPPORT        CASUAL         PRIVATE     │
│   GROUP        CIRCLE         LOUNGE                     │
│                                                          │
│              [Your Avatar] ← can walk left/right        │
│                                                          │
│  💬 "Welcome! I'm Atlas, your guide. Use ← → arrows    │
│      or click to walk. Enter any door to start!"        │
└──────────────────────────────────────────────────────────┘
```

**Atlas (AI Tutorial Guide) - Interactive Walkthrough:**

1. **Movement Tutorial:**
   - Atlas appears as floating orb: *"Try walking to the Study Group door!"*
   - User moves avatar using arrow keys or click-to-move
   - Atlas: *"Perfect! You'll walk like this in all rooms."*

2. **Chat Basics:**
   - Atlas: *"Press ENTER to chat. Try saying hello!"*
   - User types message → appears in speech bubble above avatar
   - Atlas responds: *"Great! I heard you. Now let's try a real room."*

3. **Room Selection:**
   - Atlas: *"Each door leads to a different vibe:*
     - *🎓 Study Group - Collaborative learning*
     - *🤝 Support Circle - Safe space for sharing*
     - *🎮 Casual Lounge - Hang out, chill*
     - *🏠 Private Room - Solo chat with AI*
   - *Which interests you?"*

4. **First Room Entry:**
   - User walks to chosen door
   - Screen transition: Door opens with particle effect
   - **Spawn into chosen room with other live users**

***

#### **Stage 4: First Room Experience (2-5 minutes)**

**User enters "Study Group" (example)**

```
Room Layout (Top-down 2D):

┌──────────────────────────────────────────────────────────┐
│  📚 Study Group - Biology 101                            │
│  👥 5 users online        🤖 AI: Dr. Chen                │
├──────────────────────────────────────────────────────────┤
│                                                          │
│   [Table]  ← Central gathering point                    │
│   [Book]                                                 │
│                                                          │
│    👤Sarah    👤Mike    👤You    👤Carlos               │
│                                                          │
│   [Whiteboard] ← Interactive element                    │
│                                                          │
│   🤖 Dr. Chen (AI) - standing at whiteboard             │
│                                                          │
├──────────────────────────────────────────────────────────┤
│  Chat Panel (right side):                               │
│  ─────────────────────────────                          │
│  Dr. Chen: "Welcome! We're discussing cell division.     │
│             Jump in anytime!"                            │
│                                                          │
│  Sarah: "Can someone explain mitosis vs meiosis?"        │
│                                                          │
│  [Type your message here...]                            │
└──────────────────────────────────────────────────────────┘
```

**AI's Dynamic Greeting (personalized to user):**

```python
# Backend logic
if user.is_first_time:
    ai_prompt = f"""
    New user '{user.name}' just entered the Study Group room.
    Current conversation: discussing cell division (mitosis/meiosis).
    Other users: Sarah (asking questions), Mike (helping), Carlos (listening).
    
    Welcome {user.name} warmly, acknowledge they're new, briefly explain 
    current topic, and invite participation WITHOUT overwhelming them.
    """
    
    # AI Response Example:
    # "Hey {user.name}! Great to see you. I'm Dr. Chen, your AI study buddy. 
    #  Sarah just asked about mitosis vs meiosis - perfect timing! 
    #  Feel free to listen or jump in with questions. No pressure! 😊"
```

**Participation Prompt (if user silent for 1 minutes):**

```
Dr. Chen (AI): "@{user.name}, you've been quiet - following along okay? 
               Any questions about what we've covered?"
```

***

### 4.2 Core Gameplay Loop

```
┌─────────────────────────────────────────────────────────┐
│  1. Enter Room (spatial movement)                       │
│  2. AI greets + assesses user mood/context              │
│  3. User participates in conversation                   │
│  4. AI tracks: sentiment, participation, topic flow     │
│  5. AI intervenes: answers questions, moderates, prompts│
│  6. User gains "engagement score" (gamification)        │
│  7. Unlock new rooms/features based on activity         │
└─────────────────────────────────────────────────────────┘
```

***

## 5. AI Context Management System

### 5.1 User State Tracking

**Per-User Memory Schema (Redis):**

```python
user_context = {
    "user_id": "user_123",
    "name": "Sarah",
    "avatar": "cat_blue",
    "current_room": "study_group_bio101",
    "joined_at": "2025-10-25T00:30:00Z",
    
    # Emotional State (for every conversation you need to constantly update the user analytics about the state of the users mind)
    "sentiment": {
        "current": "neutral",  # Options: positive, neutral, negative, frustrated
        "history": [
            {"timestamp": "00:32", "sentiment": "positive", "trigger": "question_answered"},
            {"timestamp": "00:35", "sentiment": "frustrated", "trigger": "confused_response"}
        ]
    },
    
    # Participation Metrics
    "participation": {
        "message_count": 8,
        "last_message_time": "00:38:15",
        "silence_duration": 120,  # seconds
        "engagement_score": 0.7,  # 0-1 scale
        "is_active": True
    },
    
    # Conversation Context
    "conversation_history": [
        {"time": "00:32", "message": "What's the difference between mitosis and meiosis?"},
        {"time": "00:35", "message": "I'm still confused about the chromosome count"}
    ],
    
    # Learned Preferences
    "preferences": {
        "learning_style": "visual",  # inferred from "can you show a diagram?"
        "question_frequency": "high",
        "topics_discussed": ["cell_division", "chromosomes", "genetics"]
    }
}
```

***

### 5.2 Room-Level State Tracking

**Room Context Schema (Redis):**

```python
room_state = {
    "room_id": "study_group_bio101",
    "room_type": "study_group",
    "ai_persona": "dr_chen",
    "created_at": "2025-10-25T00:00:00Z",
    
    # Active Users
    "users": [
        {"id": "user_123", "name": "Sarah", "status": "active"},
        {"id": "user_456", "name": "Mike", "status": "idle"},
        {"id": "user_789", "name": "Carlos", "status": "active"}
    ],
    
    # Conversation Flow
    "conversation_graph": {
        "current_topic": "cell_division",
        "topic_history": ["intro", "mitosis_basics", "meiosis_basics", "comparison"],
        "threads": [
            {
                "id": "thread_1",
                "participants": ["sarah", "dr_chen"],
                "topic": "chromosome_count_confusion",
                "status": "active",
                "priority": "high"  # Sarah is confused, needs resolution
            },
            {
                "id": "thread_2",
                "participants": ["mike", "carlos"],
                "topic": "side_discussion_examples",
                "status": "active",
                "priority": "low"
            }
        ]
    },
    
    # Group Dynamics
    "dynamics": {
        "dominant_speaker": "sarah",  # highest message count
        "quiet_users": ["carlos"],  # < 3 messages in 10 min
        "sentiment_average": 0.6,  # group mood
        "conflict_detected": False,
        "needs_moderation": False
    },
    
    # AI Intervention Queue
    "ai_queue": [
        {
            "trigger": "user_confusion",
            "target_user": "sarah",
            "priority": "high",
            "action": "clarify_explanation"
        },
        {
            "trigger": "silence_threshold",
            "target_user": "carlos",
            "priority": "medium",
            "action": "engagement_prompt"
        }
    ]
}
```

***

### 5.3 AI Prompt Construction System

**Dynamic Prompt Builder (Python Backend):**

```python
class AIPromptOrchestrator:
    def __init__(self, room_id: str):
        self.room = get_room_state(room_id)
        self.users = get_all_user_contexts(room_id)
        self.history = get_conversation_history(room_id, limit=20)
    
    def build_prompt(self, trigger: str, target_user: str = None) -> dict:
        """
        Constructs context-aware prompt for Janitor AI API
        """
        
        # Base System Prompt (varies by room type)
        system_prompt = self._get_base_persona()
        
        # Dynamic Context Injection
        context = f"""
ROOM STATE:
- Type: {self.room['room_type']}
- Current topic: {self.room['conversation_graph']['current_topic']}
- Active users: {len(self.room['users'])}
- Group mood: {self._get_mood_description()}

USER STATES:
{self._format_user_states()}

CONVERSATION THREADS:
{self._format_threads()}

RECENT MESSAGES (last 20):
{self._format_history()}

CURRENT TRIGGER: {trigger}
{f"TARGET USER: {target_user}" if target_user else ""}

YOUR OBJECTIVE:
{self._get_objective_for_trigger(trigger, target_user)}
"""
        
        return {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "system", "content": context},
                *self._format_history_as_messages(),
                {"role": "user", "content": self._get_trigger_prompt(trigger)}
            ]
        }
    
    def _get_base_persona(self) -> str:
        """Returns persona based on room type"""
        personas = {
            "study_group": """You are Dr. Chen, an encouraging AI teaching assistant.
PERSONALITY: Patient, knowledgeable, uses analogies, celebrates small wins.
ROLE: Answer questions, create practice problems, ensure everyone understands.
CONSTRAINTS: 
- Keep responses under 3 sentences unless explaining complex topics
- Use encouraging language
- Check for understanding before moving forward
- Adapt explanations to user's apparent level
""",
            
            "support_circle": """You are Sam, an AI counselor trained in active listening.
PERSONALITY: Empathetic, non-judgmental, validating, calm.
ROLE: Facilitate sharing, validate emotions, prevent harmful content.
CONSTRAINTS:
- Never give medical advice
- Escalate crisis situations immediately
- Maintain confidentiality references
- Use reflective listening techniques
""",
            
            "casual_lounge": """You are Rex, a charismatic AI bartender.
PERSONALITY: Witty, warm, great storyteller, socially aware.
ROLE: Keep conversation flowing, tell stories, lighten mood, facilitate connections.
CONSTRAINTS:
- Keep energy appropriate to group vibe
- Don't dominate conversation
- Reference user interests naturally
"""
        }
        return personas.get(self.room['room_type'], personas['casual_lounge'])
    
    def _format_user_states(self) -> str:
        """Formats user context for AI"""
        states = []
        for user in self.users:
            state = f"""
- {user['name']}:
  * Mood: {user['sentiment']['current']}
  * Participation: {user['participation']['message_count']} messages, 
    last active {user['participation']['silence_duration']}s ago
  * Engagement: {'🟢 Active' if user['participation']['is_active'] else '🔴 Quiet'}
  * Recent focus: {', '.join(user['preferences']['topics_discussed'][-3:])}
"""
            if user['sentiment']['current'] == 'frustrated':
                state += f"  * ⚠️ NEEDS ATTENTION: User seems confused/frustrated\n"
            
            states.append(state)
        
        return "\n".join(states)
    
    def _get_objective_for_trigger(self, trigger: str, target_user: str) -> str:
        """Returns specific instruction based on trigger type"""
        objectives = {
            "direct_mention": f"User {target_user} asked you a direct question. Answer clearly and helpfully.",
            
            "user_confusion": f"User {target_user} is confused. Clarify the current topic with a different explanation approach.",
            
            "silence_threshold": f"User {target_user} has been quiet for >2 minutes. Gently check in and invite participation.",
            
            "conflict_detected": f"Tension detected between users. De-escalate with humor/empathy and redirect.",
            
            "group_silence": "No one has spoken for 45 seconds. Break silence with engaging question or interesting fact.",
            
            "new_user_joined": f"User {target_user} just entered. Welcome warmly, brief context on current topic, invite participation.",
            
            "topic_exhausted": "Current topic seems exhausted. Suggest natural transition or ask group what to explore next."
        }
        
        return objectives.get(trigger, "Respond naturally to maintain conversation flow.")
```

***

### 5.4 AI Response Flow

```
┌─────────────────────────────────────────────────────────┐
│  1. TRIGGER DETECTION                                   │
│     - User sends message                                │
│     - System detects pattern (silence, confusion, etc)  │
│     ↓                                                   │
│  2. PRIORITY ASSESSMENT                                 │
│     - High: Direct @mention, crisis, confusion          │
│     - Medium: Questions, topic shifts                   │
│     - Low: Ambient engagement, icebreakers              │
│     ↓                                                   │
│  3. CONTEXT GATHERING                                   │
│     - Fetch room state from Redis                       │
│     - Fetch all user contexts                           │
│     - Get last 20 messages                              │
│     ↓                                                   │
│  4. PROMPT CONSTRUCTION                                 │
│     - Build dynamic prompt (see above)                  │
│     - Total tokens: ~2000-4000 (well under 25k limit)   │
│     ↓                                                   │
│  5. API CALL (Janitor AI)                               │
│     - POST https://janitorai.com/hackathon/completions  │
│     - Stream response                                   │
│     ↓                                                   │
│  6. RESPONSE PROCESSING                                 │
│     - Parse AI response                                 │
│     - Extract: message, target users, actions           │
│     ↓                                                   │
│  7. STATE UPDATE                                        │
│     - Update conversation history                       │
│     - Update user contexts (sentiment analysis)         │
│     - Update room state                                 │
│     ↓                                                   │
│  8. BROADCAST                                           │
│     - Send to all users via WebSocket                   │
│     - Display in chat + avatar speech bubble            │
└─────────────────────────────────────────────────────────┘
```

***

## 6. Technical Implementation

### 6.1 Project Structure

```
chatrealm/
├── docker-compose.yml
├── .env.example
├── README.md
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── public/
│   │   ├── assets/
│   │   │   ├── sprites/          # Avatar sprites
│   │   │   ├── rooms/            # Room backgrounds
│   │   │   ├── sounds/           # Audio effects
│   │   │   └── ui/               # UI elements
│   │   └── index.html
│   │
│   └── src/
│       ├── components/
│       │   ├── Avatar.tsx
│       │   ├── ChatPanel.tsx
│       │   ├── RoomCanvas.tsx
│       │   ├── UserList.tsx
│       │   └── EmotionIndicator.tsx
│       │
│       ├── game/
│       │   ├── GameScene.ts      # Phaser scene management
│       │   ├── PlayerController.ts
│       │   ├── RoomManager.ts
│       │   └── AnimationController.ts
│       │
│       ├── services/
│       │   ├── socketService.ts  # WebSocket client
│       │   ├── apiService.ts     # REST API calls
│       │   └── authService.ts
│       │
│       ├── store/
│       │   ├── userStore.ts      # Zustand stores
│       │   ├── roomStore.ts
│       │   └── chatStore.ts
│       │
│       ├── types/
│       │   ├── User.ts
│       │   ├── Room.ts
│       │   └── Message.ts
│       │
│       └── App.tsx
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pyproject.toml
│   │
│   ├── app/
│   │   ├── main.py               # FastAPI entry point
│   │   ├── config.py             # Environment config
│   │   │
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── auth.py
│   │   │   │   ├── rooms.py
│   │   │   │   └── users.py
│   │   │   └── websocket.py      # Socket.io handlers
│   │   │
│   │   ├── services/
│   │   │   ├── ai_service.py     # Janitor AI integration
│   │   │   ├── room_service.py
│   │   │   ├── user_service.py
│   │   │   └── context_manager.py # AI context building
│   │   │
│   │   ├── models/
│   │   │   ├── user.py           # SQLAlchemy models
│   │   │   ├── room.py
│   │   │   └── message.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── user_schema.py    # Pydantic schemas
│   │   │   ├── room_schema.py
│   │   │   └── message_schema.py
│   │   │
│   │   ├── core/
│   │   │   ├── redis_client.py
│   │   │   ├── database.py
│   │   │   └── security.py
│   │   │
│   │   └── utils/
│   │       ├── sentiment_analyzer.py
│   │       ├── trigger_detector.py
│   │       └── prompt_builder.py
│   │
│   └── tests/
│       ├── test_ai_service.py
│       ├── test_websocket.py
│       └── test_context_manager.py
│
├── nginx/
│   ├── Dockerfile
│   └── nginx.conf
│
└── monitoring/
    ├── prometheus.yml
    └── grafana/
        └── dashboards/
```

***

### 8.2 User Engagement Metrics

- **Average session time** per room
- **Message count** per user per session
- **AI intervention frequency**
- **Sentiment trend** (positive vs negative)
