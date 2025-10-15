#!/bin/bash

# Personal Assistant Startup Script

set -e

echo "🤖 Starting Personal Assistant..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from env.example..."
    cp env.example .env
    echo "📝 Please edit .env file with your API keys before continuing."
    echo "   Required: OPENAI_API_KEY, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, SENDGRID_API_KEY"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Build and start services
echo "🔨 Building Docker images..."
docker compose build

echo "🚀 Starting services..."
docker compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are healthy
echo "🏥 Checking service health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Web service is healthy"
else
    echo "❌ Web service is not responding"
    echo "📋 Check logs with: docker compose logs web"
    exit 1
fi

# Create demo data
echo "🌱 Creating demo data..."
docker compose exec -T web python scripts/seed_demo.py || echo "⚠️  Demo data creation failed (this is optional)"

echo ""
echo "🎉 Personal Assistant is ready!"
echo ""
echo "📱 Admin Interface: http://localhost:8000/admin"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🏥 Health Check: http://localhost:8000/health"
echo ""
echo "📋 Useful commands:"
echo "   View logs: docker compose logs -f"
echo "   Stop services: docker compose down"
echo "   Restart: docker compose restart"
echo ""
echo "🔧 For development with webhooks:"
echo "   docker compose --profile dev up -d"
echo "   (requires NGROK_AUTHTOKEN in .env)"
