"""
PostgreSQL Database Setup Script for DollarClub
This script helps you set up the PostgreSQL database and test the connection.
"""

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys

def get_credentials():
    """Get PostgreSQL credentials from user"""
    print("=" * 60)
    print("PostgreSQL Database Setup")
    print("=" * 60)
    
    host = input("Host [localhost]: ").strip() or "localhost"
    port = input("Port [5432]: ").strip() or "5432"
    user = input("PostgreSQL Username [postgres]: ").strip() or "postgres"
    password = input("PostgreSQL Password: ").strip()
    database = input("Database Name [dollarclub]: ").strip() or "dollarclub"
    
    return {
        'host': host,
        'port': port,
        'user': user,
        'password': password,
        'database': database
    }

def test_connection(creds):
    """Test connection to PostgreSQL"""
    print("\n🔍 Testing connection to PostgreSQL...")
    try:
        conn = psycopg2.connect(
            host=creds['host'],
            port=creds['port'],
            user=creds['user'],
            password=creds['password'],
            database='postgres'  # Connect to default postgres database first
        )
        conn.close()
        print("✅ Successfully connected to PostgreSQL!")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check your username and password")
        print("3. Verify PostgreSQL is listening on the specified port")
        return False

def create_database(creds):
    """Create the database if it doesn't exist"""
    print(f"\n🔨 Creating database '{creds['database']}'...")
    try:
        # Connect to default postgres database
        conn = psycopg2.connect(
            host=creds['host'],
            port=creds['port'],
            user=creds['user'],
            password=creds['password'],
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (creds['database'],)
        )
        exists = cursor.fetchone()
        
        if exists:
            print(f"ℹ️  Database '{creds['database']}' already exists")
        else:
            # Create database
            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(creds['database'])
                )
            )
            print(f"✅ Database '{creds['database']}' created successfully!")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        return False

def generate_env_file(creds):
    """Generate DATABASE_URL for .env file"""
    db_url = f"postgresql://{creds['user']}:{creds['password']}@{creds['host']}:{creds['port']}/{creds['database']}"
    
    print("\n" + "=" * 60)
    print("✅ Setup Complete!")
    print("=" * 60)
    print("\nAdd this to your backend/.env file:")
    print("-" * 60)
    print(f"DATABASE_URL={db_url}")
    print("-" * 60)
    
    # Ask if they want to update .env automatically
    update = input("\nWould you like to update the .env file automatically? (y/n): ").strip().lower()
    if update == 'y':
        try:
            # Read existing .env
            try:
                with open('.env', 'r') as f:
                    lines = f.readlines()
            except FileNotFoundError:
                lines = []
            
            # Update DATABASE_URL line
            updated = False
            for i, line in enumerate(lines):
                if line.startswith('DATABASE_URL='):
                    lines[i] = f"DATABASE_URL={db_url}\n"
                    updated = True
                    break
            
            if not updated:
                lines.append(f"DATABASE_URL={db_url}\n")
            
            # Write back to .env
            with open('.env', 'w') as f:
                f.writelines(lines)
            
            print("✅ .env file updated successfully!")
        except Exception as e:
            print(f"❌ Failed to update .env file: {e}")
            print("Please update it manually.")

def main():
    """Main setup function"""
    print("\nDollarClub Trading Platform - PostgreSQL Setup\n")
    
    creds = get_credentials()
    
    if not test_connection(creds):
        sys.exit(1)
    
    if not create_database(creds):
        sys.exit(1)
    
    generate_env_file(creds)
    
    print("\n📝 Next steps:")
    print("1. Make sure DATABASE_URL is set in your .env file")
    print("2. Run: python -m uvicorn main:app --reload")
    print("3. The tables will be created automatically on first run")
    print("\nHappy trading! 🚀\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user.")
        sys.exit(1)

