#!/bin/bash

# STT Agent Containerized System Startup Script

echo "🎤 Starting STT AI Agent Containerized System..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install docker-compose."
    exit 1
fi

echo "🏗️  Building and starting services..."

# Build and start services
docker-compose up --build -d

echo "⏳ Waiting for services to be healthy..."

# Wait for services to be healthy
timeout=120
elapsed=0
while [ $elapsed -lt $timeout ]; do
    if docker-compose ps | grep -q "healthy"; then
        echo "✅ Services are healthy!"
        break
    fi
    sleep 5
    elapsed=$((elapsed + 5))
    echo "   Waiting... ($elapsed/$timeout seconds)"
done

if [ $elapsed -ge $timeout ]; then
    echo "⚠️  Timeout waiting for services to be healthy"
    echo "📋 Service status:"
    docker-compose ps
    exit 1
fi

echo ""
echo "🚀 STT AI Agent System is running!"
echo ""
echo "📡 Service endpoints:"
echo "   • Core STT Service:     http://localhost:8000"
echo "   • Knowledge Base:       http://localhost:8001"
echo "   • Ollama:              http://localhost:11434"
echo ""
echo "📖 API Documentation:"
echo "   • STT Core API docs:    http://localhost:8000/docs"
echo "   • Knowledge Base docs:  http://localhost:8001/docs"
echo ""
echo "🔧 Useful commands:"
echo "   • View logs:           docker-compose logs -f"
echo "   • Stop services:       docker-compose down"
echo "   • Restart:             docker-compose restart"
echo ""

# Test if services are responding
echo "🧪 Testing service connectivity..."

# Test knowledge base
if curl -s http://localhost:8001/health > /dev/null; then
    echo "   ✅ Knowledge Base service responding"
else
    echo "   ❌ Knowledge Base service not responding"
fi

# Test STT core
if curl -s http://localhost:8000/health > /dev/null; then
    echo "   ✅ STT Core service responding"
else
    echo "   ❌ STT Core service not responding"
fi

echo ""
echo "🎉 System startup complete!"
