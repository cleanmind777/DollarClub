#!/usr/bin/env python3
"""
Setup script to create .env file for DollarClub backend
"""

import os
import secrets

def create_env_file():
    """Create .env file with proper configuration"""
    
    env_content = f"""# Application Configuration
APP_NAME=DollarClub Trading Platform
DEBUG=true
SECRET_KEY={secrets.token_urlsafe(32)}

# Database Configuration
# Update with your PostgreSQL credentials
DATABASE_URL=postgresql://postgres:your_password_here@localhost/dollarclub

# Redis Configuration (Required for Celery)
REDIS_URL=redis://localhost:6379/0

# Google OAuth Configuration
# Get credentials from: https://console.cloud.google.com/
# 1. Create project
# 2. Enable Google+ API
# 3. Create OAuth 2.0 credentials
# 4. Add authorized redirect URI: http://localhost:8001/auth/google/callback
# 5. Copy Client ID and Client Secret below
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8001/auth/google/callback

# IBKR OAuth Configuration (Secondary Integration - Optional)
IBKR_CLIENT_ID=
IBKR_CLIENT_SECRET=
IBKR_REDIRECT_URI=http://localhost:8001/auth/ibkr/connect

# Script Execution Configuration
MAX_SCRIPT_SIZE=10485760       # 10MB
MAX_EXECUTION_TIME=3600        # 1 hour (3600 seconds)
MAX_CONCURRENT_SCRIPTS=5

# File Storage Configuration
SCRIPTS_DIR=scripts
UPLOAD_DIR=uploads

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
"""

    env_path = os.path.join(os.path.dirname(__file__), '.env')
    
    if os.path.exists(env_path):
        response = input('.env file already exists. Overwrite? (y/N): ')
        if response.lower() != 'y':
            print('Cancelled. .env file not modified.')
            return
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print('✅ .env file created successfully!')
    print(f'📁 Location: {env_path}')
    print()
    print('⚠️  IMPORTANT: Update the following in .env:')
    print('   1. DATABASE_URL - Your PostgreSQL password')
    print('   2. GOOGLE_CLIENT_ID - From Google Cloud Console')
    print('   3. GOOGLE_CLIENT_SECRET - From Google Cloud Console')
    print()
    print('📖 See GOOGLE_OAUTH_SETUP.md for detailed setup instructions')

if __name__ == '__main__':
    create_env_file()

