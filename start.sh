#!/bin/bash

echo "🚀 Starting ChatRealm..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from env.example..."
    cp env.example .env
    echo "✅ Created .env file. Please edit it with your API keys before continuing."
    echo ""
    echo "Required keys:"
    echo "  - JANITOR_AI_API_KEY (from https://janitorai.com/hackathon)"
    echo "  - ANTHROPIC_API_KEY (from https://console.anthropic.com/)"
    echo "  - SECRET_KEY (generate with: openssl rand -hex 32)"
    echo ""
    read -p "Press Enter after updating .env to continue..."
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "🐳 Starting Docker containers..."
docker-compose down
docker-compose up -d --build

echo ""
echo "⏳ Waiting for services to start..."
sleep 10

echo ""
echo "🔍 Checking service health..."

# Check backend
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is running"
else
    echo "❌ Backend is not responding"
fi

# Check frontend
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend is running"
else
    echo "❌ Frontend is not responding"
fi

echo ""
echo "📝 Initializing default rooms..."
echo "Please visit http://localhost:8000/docs"
echo "And call POST /api/rooms/initialize-defaults"
echo "(You'll need to login first to get a token)"

echo ""
echo "🎉 ChatRealm is ready!"
echo ""
echo "Access the application at:"
echo "  - Main App: http://localhost:80"
echo "  - Frontend: http://localhost:3000"
echo "  - Backend API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop: docker-compose down"

