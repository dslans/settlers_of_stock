#!/bin/bash

# Settlers of Stock Development Setup Script

echo "🏗️  Setting up Settlers of Stock development environment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create environment files if they don't exist
if [ ! -f backend/.env ]; then
    echo "📝 Creating backend environment file..."
    cp backend/.env.example backend/.env
    echo "✅ Created backend/.env - please update with your configuration"
fi

if [ ! -f frontend/.env.local ]; then
    echo "📝 Creating frontend environment file..."
    cat > frontend/.env.local << EOF
REACT_APP_API_URL=http://localhost:8000
EOF
    echo "✅ Created frontend/.env.local"
fi

# Build and start the development environment
echo "🐳 Building and starting Docker containers..."
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is running at http://localhost:8000"
    echo "📚 API Documentation: http://localhost:8000/docs"
else
    echo "⚠️  Backend may still be starting up..."
fi

if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is running at http://localhost:3000"
else
    echo "⚠️  Frontend may still be starting up..."
fi

echo ""
echo "🎉 Setup complete! Your development environment is ready."
echo ""
echo "📋 Quick commands:"
echo "  - View logs: docker-compose logs -f"
echo "  - Stop services: docker-compose down"
echo "  - Restart services: docker-compose restart"
echo ""
echo "🔗 Access your application:"
echo "  - Frontend: http://localhost:3000"
echo "  - Backend API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"