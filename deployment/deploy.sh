#!/bin/bash

# DollarClub Trading Platform Deployment Script
# This script deploys the application on Ubuntu VPS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="dollarclub"
APP_DIR="/opt/$APP_NAME"
VENV_DIR="$APP_DIR/venv"
SERVICE_USER="dollarclub"
DOMAIN="${DOMAIN:-yourdomain.com}"

echo -e "${GREEN}Starting DollarClub deployment...${NC}"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}This script should not be run as root${NC}" 
   exit 1
fi

# Update system packages
echo -e "${YELLOW}Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# Install required packages
echo -e "${YELLOW}Installing required packages...${NC}"
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

# Create application user
echo -e "${YELLOW}Creating application user...${NC}"
sudo useradd -r -s /bin/false $SERVICE_USER || true

# Create application directory
echo -e "${YELLOW}Creating application directories...${NC}"
sudo mkdir -p $APP_DIR/{backend,frontend,scripts,uploads,logs}
sudo chown -R $SERVICE_USER:$SERVICE_USER $APP_DIR

# Clone or copy application code
echo -e "${YELLOW}Setting up application code...${NC}"
if [ -d ".git" ]; then
    # If this is a git repository, copy the files
    sudo cp -r ../backend/* $APP_DIR/backend/
    sudo cp -r ../frontend/* $APP_DIR/frontend/
else
    echo -e "${RED}Please ensure you're running this from the deployment directory${NC}"
    exit 1
fi

# Set up Python virtual environment
echo -e "${YELLOW}Setting up Python virtual environment...${NC}"
sudo -u $SERVICE_USER python3.11 -m venv $VENV_DIR
sudo -u $SERVICE_USER $VENV_DIR/bin/pip install --upgrade pip
sudo -u $SERVICE_USER $VENV_DIR/bin/pip install -r $APP_DIR/backend/requirements.txt

# Configure PostgreSQL
echo -e "${YELLOW}Configuring PostgreSQL...${NC}"
sudo -u postgres psql << EOF
CREATE DATABASE dollarclub;
CREATE USER dollarclub_user WITH ENCRYPTED PASSWORD '$(openssl rand -base64 32)';
GRANT ALL PRIVILEGES ON DATABASE dollarclub TO dollarclub_user;
\q
EOF

# Configure Redis
echo -e "${YELLOW}Configuring Redis...${NC}"
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Run database migrations
echo -e "${YELLOW}Running database migrations...${NC}"
cd $APP_DIR/backend
sudo -u $SERVICE_USER $VENV_DIR/bin/alembic upgrade head

# Build frontend
echo -e "${YELLOW}Building frontend...${NC}"
cd $APP_DIR/frontend
sudo -u $SERVICE_USER npm install
sudo -u $SERVICE_USER npm run build

# Copy systemd service files
echo -e "${YELLOW}Setting up systemd services...${NC}"
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload

# Configure Nginx
echo -e "${YELLOW}Configuring Nginx...${NC}"
sudo cp nginx/nginx.conf /etc/nginx/sites-available/$APP_NAME
sudo ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Configure firewall
echo -e "${YELLOW}Configuring firewall...${NC}"
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# Start services
echo -e "${YELLOW}Starting services...${NC}"
sudo systemctl enable $APP_NAME-backend
sudo systemctl enable $APP_NAME-celery
sudo systemctl enable $APP_NAME-frontend
sudo systemctl enable nginx

sudo systemctl start $APP_NAME-backend
sudo systemctl start $APP_NAME-celery
sudo systemctl start $APP_NAME-frontend
sudo systemctl restart nginx

# Set up SSL certificate
if [ "$DOMAIN" != "yourdomain.com" ]; then
    echo -e "${YELLOW}Setting up SSL certificate...${NC}"
    sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN
fi

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Update environment variables in $APP_DIR/backend/.env"
echo "2. Configure IBKR OAuth credentials"
echo "3. Restart services: sudo systemctl restart $APP_NAME-backend $APP_NAME-celery"
echo "4. Visit https://$DOMAIN to access the application"
