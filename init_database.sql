-- DollarClub Trading Platform Database Initialization
-- Run this script to create the database schema

-- Set timezone
SET timezone = 'UTC';

-- Create database (uncomment if needed)
-- CREATE DATABASE dollarclub;

-- Connect to database (uncomment if needed)
-- \c dollarclub;

-- Drop existing tables if they exist (for clean setup)
DROP TABLE IF EXISTS scripts CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TYPE IF EXISTS scriptstatus CASCADE;
DROP TYPE IF EXISTS authprovider CASCADE;
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

-- Create custom enum types
CREATE TYPE authprovider AS ENUM ('email', 'google');
CREATE TYPE scriptstatus AS ENUM ('uploaded', 'running', 'completed', 'failed', 'cancelled');

-- Create users table with all fields
CREATE TABLE users (
    -- Primary key
    id SERIAL PRIMARY KEY,
    
    -- Authentication fields
    email VARCHAR(255) NOT NULL,
    username VARCHAR(100) NOT NULL,
    hashed_password VARCHAR(255),
    auth_provider authprovider DEFAULT 'email',
    google_id VARCHAR(100),
    
    -- Account status
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    
    -- IBKR Integration
    ibkr_user_id VARCHAR(100),
    ibkr_access_token TEXT,
    ibkr_refresh_token TEXT,
    ibkr_token_expires_at TIMESTAMP,
    ibkr_connected_at TIMESTAMP
);

-- Create scripts table with all fields
CREATE TABLE scripts (
    -- Primary key
    id SERIAL PRIMARY KEY,
    
    -- Foreign key relationship
    user_id INTEGER NOT NULL,
    
    -- File information
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    file_extension VARCHAR(10),
    
    -- Execution information
    status scriptstatus DEFAULT 'uploaded' NOT NULL,
    execution_logs TEXT,
    error_message TEXT,
    
    -- Execution metrics
    execution_time_seconds NUMERIC(10, 3),
    memory_usage_mb NUMERIC(10, 2),
    exit_code INTEGER,
    
    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE,
    
    -- Foreign key constraint with cascade delete
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE UNIQUE INDEX ix_users_email ON users (email);
CREATE UNIQUE INDEX ix_users_google_id ON users (google_id);
CREATE INDEX ix_users_id ON users (id);
CREATE UNIQUE INDEX ix_users_ibkr_user_id ON users (ibkr_user_id);
CREATE INDEX ix_users_email_provider ON users (email, auth_provider);
CREATE INDEX ix_users_created_at ON users (created_at);
CREATE INDEX ix_users_last_login ON users (last_login_at);

CREATE INDEX ix_scripts_id ON scripts (id);
CREATE INDEX ix_scripts_user_status ON scripts (user_id, status);
CREATE INDEX ix_scripts_created_at ON scripts (created_at);
CREATE INDEX ix_scripts_filename ON scripts (filename);
CREATE INDEX ix_scripts_status ON scripts (status);

-- Create check constraints for data integrity
ALTER TABLE users ADD CONSTRAINT ck_email_password_required 
    CHECK (CASE WHEN auth_provider = 'email' THEN hashed_password IS NOT NULL ELSE TRUE END);

ALTER TABLE users ADD CONSTRAINT ck_google_id_required 
    CHECK (CASE WHEN auth_provider = 'google' THEN google_id IS NOT NULL ELSE TRUE END);

ALTER TABLE scripts ADD CONSTRAINT ck_positive_file_size 
    CHECK (file_size > 0);

ALTER TABLE scripts ADD CONSTRAINT ck_non_negative_execution_time 
    CHECK (execution_time_seconds >= 0);

ALTER TABLE scripts ADD CONSTRAINT ck_non_negative_memory 
    CHECK (memory_usage_mb >= 0);

ALTER TABLE scripts ADD CONSTRAINT ck_completed_has_completion_time 
    CHECK (CASE WHEN status IN ('completed', 'failed', 'cancelled') THEN completed_at IS NOT NULL ELSE TRUE END);

ALTER TABLE scripts ADD CONSTRAINT ck_running_has_start_time 
    CHECK (CASE WHEN status = 'running' THEN started_at IS NOT NULL ELSE TRUE END);

-- Create trigger function for automatic updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic timestamp updates
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scripts_updated_at 
    BEFORE UPDATE ON scripts 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for testing
INSERT INTO users (email, username, hashed_password, auth_provider, is_verified) VALUES 
('admin@dollarclub.com', 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J8.9QKxS6', 'email', true),
('demo@gmail.com', 'demo_user', NULL, 'google', true);

-- Update the Google user with a Google ID
UPDATE users SET google_id = '123456789' WHERE email = 'demo@gmail.com';

-- Insert sample scripts
INSERT INTO scripts (user_id, filename, original_filename, file_path, file_size, file_extension, status) VALUES 
(1, 'trading_strategy_001.py', 'my_trading_strategy.py', '/scripts/trading_strategy_001.py', 2048, 'py', 'uploaded'),
(1, 'market_analysis_002.py', 'market_analysis.py', '/scripts/market_analysis_002.py', 1536, 'py', 'completed'),
(2, 'portfolio_optimizer_003.py', 'portfolio_optimizer.py', '/scripts/portfolio_optimizer_003.py', 3072, 'py', 'running');

-- Update script with execution details
UPDATE scripts SET 
    started_at = NOW() - INTERVAL '5 minutes',
    execution_time_seconds = 45.5,
    memory_usage_mb = 128.5,
    exit_code = 0,
    execution_logs = 'Script started successfully...\nProcessing market data...\nExecution completed.',
    completed_at = NOW() - INTERVAL '2 minutes'
WHERE id = 2;

-- Create useful views
CREATE VIEW user_summary AS
SELECT 
    u.id,
    u.email,
    u.username,
    u.auth_provider,
    u.is_active,
    u.is_verified,
    u.created_at,
    u.last_login_at,
    CASE WHEN u.ibkr_user_id IS NOT NULL THEN true ELSE false END as is_ibkr_connected,
    u.ibkr_connected_at,
    COUNT(s.id) as total_scripts,
    COUNT(CASE WHEN s.status = 'completed' THEN 1 END) as completed_scripts,
    COUNT(CASE WHEN s.status = 'running' THEN 1 END) as running_scripts,
    COUNT(CASE WHEN s.status = 'failed' THEN 1 END) as failed_scripts,
    COALESCE(SUM(s.file_size), 0) as total_file_size_bytes,
    ROUND(COALESCE(SUM(s.file_size), 0) / 1024.0 / 1024.0, 2) as total_file_size_mb
FROM users u
LEFT JOIN scripts s ON u.id = s.user_id
GROUP BY u.id, u.email, u.username, u.auth_provider, u.is_active, u.is_verified, 
         u.created_at, u.last_login_at, u.ibkr_user_id, u.ibkr_connected_at;

CREATE VIEW script_performance AS
SELECT 
    s.id,
    s.filename,
    s.original_filename,
    s.status,
    s.execution_time_seconds,
    s.memory_usage_mb,
    s.exit_code,
    s.file_size,
    ROUND(s.file_size / 1024.0 / 1024.0, 2) as file_size_mb,
    s.started_at,
    s.completed_at,
    s.created_at,
    u.username as owner_username,
    u.email as owner_email,
    EXTRACT(EPOCH FROM (s.completed_at - s.started_at)) as actual_duration_seconds
FROM scripts s
JOIN users u ON s.user_id = u.id
WHERE s.status IN ('completed', 'failed', 'cancelled')
ORDER BY s.completed_at DESC;

-- Display creation summary
SELECT 'Database schema created successfully!' as status;

SELECT 'Tables created:' as info;
SELECT tablename as table_name FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('users', 'scripts')
ORDER BY tablename;

SELECT 'Indexes created:' as info;
SELECT indexname as index_name FROM pg_indexes 
WHERE schemaname = 'public' 
AND tablename IN ('users', 'scripts')
ORDER BY tablename, indexname;

SELECT 'Views created:' as info;
SELECT viewname as view_name FROM pg_views 
WHERE schemaname = 'public' 
AND viewname IN ('user_summary', 'script_performance')
ORDER BY viewname;

SELECT 'Sample data inserted:' as info;
SELECT COUNT(*) as user_count FROM users;
SELECT COUNT(*) as script_count FROM scripts;

-- Display sample data
SELECT 'Sample users:' as info;
SELECT id, email, username, auth_provider, is_active, is_verified FROM users;

SELECT 'Sample scripts:' as info;
SELECT id, user_id, filename, status, file_size, created_at FROM scripts;
