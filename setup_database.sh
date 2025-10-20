#!/bin/bash

# DollarClub Trading Platform Database Setup Script

echo "Setting up DollarClub Trading Platform Database..."

# Set database connection parameters
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-dollarclub}
DB_USER=${DB_USER:-postgres}
DB_PASSWORD=${DB_PASSWORD:-password}

echo ""
echo "Database Configuration:"
echo "Host: $DB_HOST"
echo "Port: $DB_PORT"
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo ""

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo "ERROR: psql command not found. Please install PostgreSQL client tools."
    echo "Ubuntu/Debian: sudo apt-get install postgresql-client"
    echo "CentOS/RHEL: sudo yum install postgresql"
    echo "macOS: brew install postgresql"
    exit 1
fi

# Set PGPASSWORD environment variable
export PGPASSWORD="$DB_PASSWORD"

echo "Creating database schema..."

# Run the initialization script
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f init_database.sql

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Database setup completed successfully!"
    echo ""
    echo "You can now:"
    echo "1. Start the backend server"
    echo "2. Run database migrations (if needed)"
    echo "3. Test the application"
else
    echo ""
    echo "❌ Database setup failed!"
    echo "Please check your database connection and try again."
    exit 1
fi

echo ""
