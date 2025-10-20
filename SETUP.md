# DollarClub Trading Platform - Setup Guide

## Overview

DollarClub is a robust trading platform that allows users to authenticate via IBKR OAuth, upload multiple trading strategy scripts, and execute them concurrently on the server. The platform features a modern React frontend with a FastAPI backend, powered by PostgreSQL, Redis, and Celery for task management.

## Architecture

- **Frontend**: React with Vite, TypeScript, Tailwind CSS
- **Backend**: FastAPI with Python 3.11
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Task Queue**: Celery with Redis broker
- **Authentication**: IBKR OAuth 2.0
- **Deployment**: Ubuntu VPS with Nginx, systemd services

## Features Implemented

### ✅ Completed Features

1. **User Authentication**
   - IBKR OAuth 2.0 integration
   - JWT token management
   - Secure session handling

2. **Script Management**
   - Multi-file upload support (Python, JavaScript, TypeScript)
   - File validation and size limits
   - Script metadata storage

3. **Concurrent Execution**
   - Celery task queue for parallel script execution
   - Resource limits and safety checks
   - Real-time status updates

4. **Modern UI**
   - Responsive React frontend
   - Drag-and-drop file upload
   - Real-time execution monitoring
   - Clean, professional design

5. **Production Deployment**
   - Ubuntu VPS deployment scripts
   - Nginx reverse proxy with SSL
   - Systemd service management
   - Security hardening

6. **Database Schema**
   - Users table with IBKR integration
   - Scripts table with execution tracking
   - Alembic migrations

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 13+
- Redis 6+
- Git

### Local Development

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd DollarClub
   ```

2. **Start all services** (Linux/Mac):
   ```bash
   chmod +x start-dev.sh
   ./start-dev.sh
   ```

   Or on Windows:
   ```cmd
   start-dev.bat
   ```

3. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Manual Setup

#### Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start the server
uvicorn main:app --reload
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

#### Celery Worker

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Start Celery worker
celery -A app.tasks worker --loglevel=info
```

## Configuration

### Environment Variables

#### Backend (.env)
```env
# Database
DATABASE_URL=postgresql://user:password@localhost/dollarclub

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-super-secret-key
DEBUG=true

# IBKR OAuth
IBKR_CLIENT_ID=your-client-id
IBKR_CLIENT_SECRET=your-client-secret
IBKR_REDIRECT_URI=http://localhost:8000/auth/ibkr/callback

# Script execution
MAX_SCRIPT_SIZE=10485760  # 10MB
MAX_EXECUTION_TIME=3600   # 1 hour
MAX_CONCURRENT_SCRIPTS=5
```

#### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000
```

### IBKR OAuth Setup

1. **Create IBKR Developer Account**:
   - Visit [IBKR Developer Portal](https://www.interactivebrokers.com/en/software/am/am/reports/index.php)
   - Create a new application
   - Note your Client ID and Client Secret

2. **Configure OAuth Settings**:
   - Set redirect URI to: `http://localhost:8000/auth/ibkr/callback`
   - Configure required scopes: `read write`

3. **Update Environment Variables**:
   - Add IBKR credentials to your `.env` file

## API Endpoints

### Authentication
- `GET /auth/ibkr/login` - Initiate IBKR OAuth flow
- `GET /auth/ibkr/callback` - OAuth callback handler
- `GET /auth/me` - Get current user info
- `POST /auth/logout` - Logout user

### Scripts
- `POST /scripts/upload` - Upload a script file
- `GET /scripts/list` - List user's scripts
- `GET /scripts/{script_id}` - Get script details
- `POST /scripts/{script_id}/execute` - Execute a script
- `GET /scripts/{script_id}/status` - Get execution status
- `POST /scripts/{script_id}/cancel` - Cancel execution
- `DELETE /scripts/{script_id}` - Delete a script

### Health
- `GET /health` - Health check endpoint

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    ibkr_user_id VARCHAR(100) UNIQUE NOT NULL,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Scripts Table
```sql
CREATE TABLE scripts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER,
    status script_status DEFAULT 'uploaded',
    execution_logs TEXT,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## Security Features

- **OAuth 2.0 Authentication**: Secure IBKR integration
- **JWT Tokens**: Stateless authentication
- **File Validation**: Type and size restrictions
- **Resource Limits**: Execution time and concurrency limits
- **SQL Injection Protection**: SQLAlchemy ORM
- **CORS Configuration**: Cross-origin request handling
- **Rate Limiting**: API request throttling (in production)
- **HTTPS**: SSL/TLS encryption (in production)

## Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed production deployment instructions.

### Quick Production Setup

1. **Configure environment**:
   ```bash
   cp deployment/env.example deployment/.env
   # Edit deployment/.env with production values
   ```

2. **Run deployment script**:
   ```bash
   cd deployment
   chmod +x deploy.sh
   ./deploy.sh
   ```

3. **Configure IBKR OAuth**:
   - Update redirect URI to your production domain
   - Update environment variables
   - Restart services

## Monitoring and Maintenance

### Service Management
```bash
# Check service status
sudo systemctl status dollarclub-backend
sudo systemctl status dollarclub-celery
sudo systemctl status dollarclub-frontend

# View logs
sudo journalctl -u dollarclub-backend -f
sudo journalctl -u dollarclub-celery -f
```

### Database Management
```bash
# Run migrations
cd backend
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"

# Backup database
sudo -u postgres pg_dump dollarclub > backup.sql
```

## Troubleshooting

### Common Issues

1. **Database Connection Issues**:
   - Check PostgreSQL service status
   - Verify connection string in .env
   - Ensure database exists and user has permissions

2. **Redis Connection Issues**:
   - Check Redis service status
   - Verify Redis URL in .env
   - Test connection: `redis-cli ping`

3. **Script Execution Issues**:
   - Check Celery worker status
   - Verify file permissions
   - Check execution logs

4. **Authentication Issues**:
   - Verify IBKR OAuth credentials
   - Check redirect URI configuration
   - Ensure HTTPS in production

### Debug Mode

Enable debug mode for development:
```env
DEBUG=true
```

This will provide detailed error messages and enable auto-reload.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions:

1. Check the documentation
2. Review the logs
3. Check GitHub issues
4. Create a new issue if needed

## Future Enhancements

- **Real-time Logs**: WebSocket support for live execution logs
- **Script Templates**: Pre-built trading strategy templates
- **Performance Analytics**: Execution performance metrics
- **Advanced Security**: Additional security features
- **Multi-language Support**: Support for more programming languages
- **API Rate Limiting**: Advanced rate limiting strategies
- **Monitoring Dashboard**: Real-time system monitoring
- **Backup Automation**: Automated backup systems
