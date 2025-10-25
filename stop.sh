#!/bin/bash

echo "🛑 Stopping ChatRealm..."

docker-compose down

echo "✅ All services stopped"
echo ""
echo "To remove all data: docker-compose down -v"

