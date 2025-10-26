# ChatRealm - Multiplayer AI Chat Arena

**ChatRealm** is a gamified, real-time multiplayer chat platform where users enter virtual "rooms" as avatars, interact with an AI character that maintains individual user context, group dynamics, and conversation flow across diverse scenarios (study groups, support groups, casual hangouts).

## 🌟 Core Features

- **Spatial Chat UI** - Users "walk" into rooms like a 2D game using Phaser.js
- **Context-Aware AI** - Tracks each user's emotional state, participation level, and conversation history
- **Universal Adaptability** - AI persona adapts to room type (study TA, support counselor, casual bartender)
- **Real-time Multiplayer** - WebSocket-based communication for instant updates
- **Gamified Experience** - Avatar customization, room exploration, and engagement tracking

## 🏗️ Architecture

### Frontend
- **React 18** + TypeScript - Modern UI framework
- **Phaser.js 3** - 2D game engine for avatar movement
- **Socket.io-client** - Real-time WebSocket communication
- **Zustand** - Lightweight state management
- **TailwindCSS** + Framer Motion - Styling and animations

### Backend
- **FastAPI** - High-performance async Python API
- **Socket.io** - Bidirectional real-time communication
- **PostgreSQL** - Persistent data storage
- **Redis** - Hot state cache for user/room context
- **SQLAlchemy 2.0** - Database ORM

### AI Integration
- **Janitor AI API** - Primary AI inference (25K token context)
- **Anthropic Claude** - Fallback and validation using Claude 3.5 Sonnet (200K token context)

### Infrastructure
- **Docker** + Docker Compose - Containerized services
- **Nginx** - Reverse proxy and load balancing

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)
- Janitor AI API Key
- Anthropic API Key (for Claude)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd hackathon-cal
```

2. **Set up environment variables**
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```env
JANITOR_AI_API_KEY=your-janitor-ai-key
ANTHROPIC_API_KEY=your-anthropic-api-key
SECRET_KEY=your-secret-key-generate-with-openssl
```

Get your Anthropic API key from: https://console.anthropic.com/

3. **Start the application with Docker Compose**
```bash
docker-compose up -d
```

This will start:
- **Frontend** on http://localhost:3000
- **Backend** on http://localhost:8000
- **Nginx** on http://localhost:80
- **PostgreSQL** on localhost:5432
- **Redis** on localhost:6379

4. **Initialize default rooms** (first time only)

Visit http://localhost:8000/docs and use the Swagger UI to call:
```
POST /api/rooms/initialize-defaults
```

Or use curl:
```bash
curl -X POST http://localhost:8000/api/rooms/initialize-defaults \
  -H "Authorization: Bearer YOUR_TOKEN"
```

5. **Access the application**

Open http://localhost:80 in your browser

## 🎮 User Flow

1. **Landing Page** - Welcome screen with animated preview
2. **Avatar Creation** - Customize your character (style, color, mood, bio)
3. **Tutorial Hallway** - Interactive guide showing how to navigate
4. **Room Selection** - Choose from:
   - 🎓 Study Group - Collaborative learning with Dr. Chen (AI)
   - 🤝 Support Circle - Safe space with Sam (AI counselor)
   - 🎮 Casual Lounge - Hang out with Rex (AI bartender)
   - 🏠 Private Room - Solo chat with AI
5. **Room Experience** - Chat, move around, interact with AI and users

## 🛠️ Development

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at http://localhost:3000

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend will be available at http://localhost:8000

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📁 Project Structure

```
chatrealm/
├── docker-compose.yml
├── .env.example
├── README.md
├── plan.md                    # Technical design document
│
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/             # Page components
│   │   ├── game/              # Phaser.js game engine
│   │   ├── services/          # API & Socket services
│   │   ├── store/             # Zustand state management
│   │   └── types/             # TypeScript types
│   ├── Dockerfile
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── api/               # REST API routes & WebSocket
│   │   ├── core/              # Database, Redis, Security
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   └── utils/             # Helper functions
│   ├── Dockerfile
│   └── requirements.txt
│
└── nginx/
    ├── Dockerfile
    └── nginx.conf
```

## 🔑 Key Components

### AI Context Management

The system tracks:
- **User Context**: Sentiment, participation, conversation history
- **Room Context**: Active users, conversation flow, group dynamics
- **AI Triggers**: Direct mentions, confusion detection, silence thresholds

### AI Persona System

Each room type has a unique AI personality:
- **Dr. Chen** (Study Group) - Patient teacher, uses analogies
- **Sam** (Support Circle) - Empathetic counselor, validates emotions
- **Rex** (Casual Lounge) - Charismatic storyteller, social facilitator
- **Atlas** (Tutorial) - Helpful guide, clear instructions

### Real-time Features

- Avatar movement synchronized across clients
- Instant message delivery with typing indicators
- Speech bubbles appear above avatars
- Dynamic user presence tracking

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_DB` | PostgreSQL database name | chatrealm |
| `POSTGRES_USER` | PostgreSQL username | chatrealm |
| `POSTGRES_PASSWORD` | PostgreSQL password | chatrealm_password |
| `REDIS_URL` | Redis connection URL | redis://redis:6379/0 |
| `SECRET_KEY` | JWT secret key | (generate with openssl) |
| `JANITOR_AI_API_KEY` | Janitor AI API key | (required) |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | (required) |
| `CORS_ORIGINS` | Allowed CORS origins | http://localhost:3000,http://localhost:80 |

### API Endpoints

- `GET /health` - Health check
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `POST /api/auth/guest` - Guest login
- `GET /api/rooms/` - List all rooms
- `POST /api/rooms/` - Create room
- `GET /api/users/me` - Get current user
- `PATCH /api/users/me` - Update user

Full API documentation: http://localhost:8000/docs

## 🐛 Troubleshooting

### Docker Issues

```bash
# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Reset database
docker-compose down -v
docker-compose up -d
```

### Connection Issues

- Ensure all services are running: `docker-compose ps`
- Check backend health: `curl http://localhost:8000/health`
- Verify Redis: `docker-compose exec redis redis-cli ping`
- Check PostgreSQL: `docker-compose exec postgres psql -U chatrealm -d chatrealm -c "SELECT 1"`

### WebSocket Issues

- Check browser console for Socket.io errors
- Verify backend WebSocket endpoint: `ws://localhost:8000/socket.io`
- Ensure CORS is properly configured

## 📝 License

This project is developed for the hackathon.

## 🙏 Acknowledgments

- **Fetch AI** for the AI inference API
- **Anthropic** for Claude 3.5 Sonnet AI capabilities
- **Phaser.js** for the excellent game engine
- **FastAPI** for the modern Python framework

## 📧 Support

For issues and questions:
1. Check the [plan.md](plan.md) for detailed technical documentation
2. Review Docker logs: `docker-compose logs`
3. Open an issue in the repository

---

**Built with ❤️ for the hackathon**

