#!/bin/bash

# Development helper script for Settlers of Stock

case "$1" in
    "start")
        echo "🚀 Starting development environment..."
        docker-compose up
        ;;
    "build")
        echo "🏗️  Building containers..."
        docker-compose build
        ;;
    "stop")
        echo "🛑 Stopping development environment..."
        docker-compose down
        ;;
    "restart")
        echo "🔄 Restarting development environment..."
        docker-compose restart
        ;;
    "logs")
        echo "📋 Showing logs..."
        docker-compose logs -f
        ;;
    "test-backend")
        echo "🧪 Running backend tests..."
        cd backend && python -m pytest
        ;;
    "test-frontend")
        echo "🧪 Running frontend tests..."
        cd frontend && npm test -- --run
        ;;
    "install-backend")
        echo "📦 Installing backend dependencies..."
        cd backend && pip install -r requirements.txt
        ;;
    "install-frontend")
        echo "📦 Installing frontend dependencies..."
        cd frontend && npm install
        ;;
    "clean")
        echo "🧹 Cleaning up containers and volumes..."
        docker-compose down -v
        docker system prune -f
        ;;
    *)
        echo "🎯 Settlers of Stock Development Helper"
        echo ""
        echo "Usage: ./dev.sh [command]"
        echo ""
        echo "Commands:"
        echo "  start           Start development environment"
        echo "  build           Build containers"
        echo "  stop            Stop development environment"
        echo "  restart         Restart development environment"
        echo "  logs            Show container logs"
        echo "  test-backend    Run backend tests"
        echo "  test-frontend   Run frontend tests"
        echo "  install-backend Install backend dependencies"
        echo "  install-frontend Install frontend dependencies"
        echo "  clean           Clean up containers and volumes"
        echo ""
        ;;
esac