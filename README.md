# DollarClub Trading Platform

A robust trading platform where users authenticate via IBKR OAuth, upload multiple trading strategy scripts, and execute them concurrently on the server.

## Architecture

- **Backend**: FastAPI with Celery task queue
- **Frontend**: React with Vite
- **Database**: PostgreSQL
- **Message Broker**: Redis
- **Deployment**: Ubuntu VPS

## Features

- IBKR OAuth authentication
- Multi-script upload and management
- Concurrent script execution
- Real-time execution logs
- Resource limits and safety checks
- Secure deployment with HTTPS

## Project Structure

```
DollarClub/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   └── tasks/          # Celery tasks
│   ├── requirements.txt
│   └── main.py
├── frontend/               # React Vite frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API services
│   │   └── utils/          # Utilities
│   ├── package.json
│   └── vite.config.js
├── deployment/             # Deployment configurations
│   ├── nginx/
│   ├── systemd/
│   └── docker-compose.yml
└── scripts/               # User uploaded scripts storage
```

## Quick Start

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Database Setup
```bash
# PostgreSQL setup
createdb dollarclub
python -m alembic upgrade head
```

### Celery Worker
```bash
cd backend
celery -A app.tasks worker --loglevel=info
```

## Environment Variables

Create `.env` files in both backend and frontend directories with appropriate configuration.

## Deployment

See `deployment/` directory for Ubuntu VPS deployment instructions.
