#!/bin/bash

# DollarClub Trading Platform Development Startup Script

echo "Starting DollarClub Trading Platform in Development Mode..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command_exists python3; then
    echo "Python 3 is required but not installed."
    exit 1
fi

if ! command_exists npm; then
    echo "Node.js/npm is required but not installed."
    exit 1
fi

if ! command_exists redis-server; then
    echo "Redis is required but not installed."
    exit 1
fi

if ! command_exists psql; then
    echo "PostgreSQL is required but not installed."
    exit 1
fi

# Start Redis
echo -e "${GREEN}Starting Redis...${NC}"
redis-server --daemonize yes

# Start PostgreSQL (if not running)
echo -e "${GREEN}Starting PostgreSQL...${NC}"
sudo systemctl start postgresql 2>/dev/null || true

# Set up backend
echo -e "${GREEN}Setting up backend...${NC}"
cd backend

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

# Run database migrations
echo -e "${GREEN}Running database migrations...${NC}"
alembic upgrade head

# Start backend in background
echo -e "${GREEN}Starting backend server...${NC}"
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start Celery worker in background
echo -e "${GREEN}Starting Celery worker...${NC}"
celery -A app.tasks worker --loglevel=info &
CELERY_PID=$!

cd ../frontend

# Set up frontend
echo -e "${GREEN}Setting up frontend...${NC}"
npm install

# Start frontend
echo -e "${GREEN}Starting frontend server...${NC}"
npm run dev &
FRONTEND_PID=$!

cd ..

echo ""
echo -e "${GREEN}All services started successfully!${NC}"
echo ""
echo "Services:"
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "Process IDs:"
echo "  Backend:  $BACKEND_PID"
echo "  Celery:   $CELERY_PID"
echo "  Frontend: $FRONTEND_PID"
echo ""
echo "To stop all services, press Ctrl+C"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping all services..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $CELERY_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    redis-cli shutdown 2>/dev/null || true
    echo "All services stopped."
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Wait for user input
read -p "Press Enter to stop all services..."
cleanup
