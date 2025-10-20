# DollarClub Trading Platform - Deployment Guide

This guide covers deploying the DollarClub Trading Platform on an Ubuntu VPS.

## Prerequisites

- Ubuntu 20.04 or later
- Root access or sudo privileges
- Domain name pointing to your server
- IBKR API credentials

## Quick Deployment

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd DollarClub
   ```

2. **Configure environment variables**:
   ```bash
   cp deployment/env.example deployment/.env
   nano deployment/.env
   ```

3. **Run the deployment script**:
   ```bash
   cd deployment
   chmod +x deploy.sh
   ./deploy.sh
   ```

## Manual Deployment

### 1. System Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    postgresql \
    postgresql-contrib \
    redis-server \
    nginx \
    nodejs \
    npm \
    curl \
    git \
    ufw \
    certbot \
    python3-certbot-nginx
```

### 2. Database Setup

```bash
# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE dollarclub;
CREATE USER dollarclub_user WITH ENCRYPTED PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE dollarclub TO dollarclub_user;
\q
EOF
```

### 3. Application Setup

```bash
# Create application user
sudo useradd -r -s /bin/false dollarclub

# Create directories
sudo mkdir -p /opt/dollarclub/{backend,frontend,scripts,uploads,logs}
sudo chown -R dollarclub:dollarclub /opt/dollarclub

# Copy application files
sudo cp -r backend/* /opt/dollarclub/backend/
sudo cp -r frontend/* /opt/dollarclub/frontend/

# Set up Python environment
sudo -u dollarclub python3.11 -m venv /opt/dollarclub/venv
sudo -u dollarclub /opt/dollarclub/venv/bin/pip install -r /opt/dollarclub/backend/requirements.txt

# Run database migrations
cd /opt/dollarclub/backend
sudo -u dollarclub /opt/dollarclub/venv/bin/alembic upgrade head

# Build frontend
cd /opt/dollarclub/frontend
sudo -u dollarclub npm install
sudo -u dollarclub npm run build
```

### 4. Service Configuration

```bash
# Copy systemd service files
sudo cp deployment/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload

# Enable and start services
sudo systemctl enable dollarclub-backend
sudo systemctl enable dollarclub-celery
sudo systemctl enable dollarclub-frontend
sudo systemctl start dollarclub-backend
sudo systemctl start dollarclub-celery
sudo systemctl start dollarclub-frontend
```

### 5. Nginx Configuration

```bash
# Copy nginx configuration
sudo cp deployment/nginx/nginx.conf /etc/nginx/sites-available/dollarclub
sudo ln -sf /etc/nginx/sites-available/dollarclub /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Restart nginx
sudo systemctl restart nginx
```

### 6. SSL Certificate

```bash
# Install SSL certificate
sudo certbot --nginx -d yourdomain.com --non-interactive --agree-tos --email admin@yourdomain.com
```

## Environment Configuration

Create `/opt/dollarclub/backend/.env`:

```env
# Database
DATABASE_URL=postgresql://dollarclub_user:password@localhost/dollarclub

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-super-secret-key
DEBUG=false

# IBKR OAuth
IBKR_CLIENT_ID=your-client-id
IBKR_CLIENT_SECRET=your-client-secret
IBKR_REDIRECT_URI=https://yourdomain.com/api/auth/ibkr/callback

# Script execution
MAX_SCRIPT_SIZE=10485760
MAX_EXECUTION_TIME=3600
MAX_CONCURRENT_SCRIPTS=5
```

## IBKR OAuth Setup

1. **Create IBKR Developer Account**:
   - Visit [IBKR Developer Portal](https://www.interactivebrokers.com/en/software/am/am/reports/index.php)
   - Create a new application
   - Note your Client ID and Client Secret

2. **Configure OAuth Settings**:
   - Set redirect URI to: `https://yourdomain.com/api/auth/ibkr/callback`
   - Configure required scopes: `read write`

3. **Update Environment Variables**:
   - Add IBKR credentials to your `.env` file
   - Restart the backend service

## Security Considerations

### Firewall Configuration

```bash
# Configure UFW
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### File Permissions

```bash
# Set proper permissions
sudo chown -R dollarclub:dollarclub /opt/dollarclub
sudo chmod -R 755 /opt/dollarclub
sudo chmod -R 700 /opt/dollarclub/scripts
sudo chmod -R 700 /opt/dollarclub/uploads
```

### Regular Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Python dependencies
sudo -u dollarclub /opt/dollarclub/venv/bin/pip install --upgrade -r /opt/dollarclub/backend/requirements.txt

# Update Node.js dependencies
cd /opt/dollarclub/frontend
sudo -u dollarclub npm update
sudo -u dollarclub npm run build
```

## Monitoring and Logs

### Service Status

```bash
# Check service status
sudo systemctl status dollarclub-backend
sudo systemctl status dollarclub-celery
sudo systemctl status dollarclub-frontend
sudo systemctl status nginx
```

### View Logs

```bash
# Application logs
sudo journalctl -u dollarclub-backend -f
sudo journalctl -u dollarclub-celery -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Database Monitoring

```bash
# Connect to database
sudo -u postgres psql dollarclub

# Check database size
SELECT pg_size_pretty(pg_database_size('dollarclub'));

# Check active connections
SELECT count(*) FROM pg_stat_activity WHERE datname = 'dollarclub';
```

## Troubleshooting

### Common Issues

1. **Service won't start**:
   ```bash
   sudo journalctl -u dollarclub-backend --no-pager
   ```

2. **Database connection issues**:
   ```bash
   sudo systemctl status postgresql
   sudo -u postgres psql -c "SELECT version();"
   ```

3. **Redis connection issues**:
   ```bash
   sudo systemctl status redis-server
   redis-cli ping
   ```

4. **Nginx configuration errors**:
   ```bash
   sudo nginx -t
   sudo systemctl status nginx
   ```

### Performance Optimization

1. **Database Optimization**:
   ```bash
   # Increase PostgreSQL memory settings
   sudo nano /etc/postgresql/*/main/postgresql.conf
   ```

2. **Redis Optimization**:
   ```bash
   # Configure Redis memory settings
   sudo nano /etc/redis/redis.conf
   ```

3. **Nginx Optimization**:
   ```bash
   # Adjust worker processes
   sudo nano /etc/nginx/nginx.conf
   ```

## Backup and Recovery

### Database Backup

```bash
# Create backup
sudo -u postgres pg_dump dollarclub > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
sudo -u postgres psql dollarclub < backup_file.sql
```

### Application Backup

```bash
# Backup application files
sudo tar -czf dollarclub_backup_$(date +%Y%m%d_%H%M%S).tar.gz /opt/dollarclub

# Backup uploaded scripts
sudo tar -czf scripts_backup_$(date +%Y%m%d_%H%M%S).tar.gz /opt/dollarclub/scripts
```

## Support

For issues and questions:

1. Check the logs first
2. Verify environment configuration
3. Ensure all services are running
4. Check network connectivity
5. Review security settings

## Maintenance

### Regular Tasks

- **Daily**: Monitor service status and logs
- **Weekly**: Update system packages
- **Monthly**: Review and rotate logs
- **Quarterly**: Security updates and dependency updates

### Health Checks

The application includes health check endpoints:

- Backend: `https://yourdomain.com/api/health`
- Frontend: `https://yourdomain.com/`

Monitor these endpoints to ensure the application is running correctly.
