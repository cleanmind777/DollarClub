-- DollarClub Trading Platform Database Schema
-- SQL queries to create tables directly

-- Create custom types (enums)
CREATE TYPE authprovider AS ENUM ('email', 'google');
CREATE TYPE scriptstatus AS ENUM ('uploaded', 'running', 'completed', 'failed', 'cancelled');

-- Create users table
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
    
    -- IBKR Integration (optional, after main auth)
    ibkr_user_id VARCHAR(100),
    ibkr_access_token TEXT,
    ibkr_refresh_token TEXT,
    ibkr_token_expires_at TIMESTAMP,
    ibkr_connected_at TIMESTAMP
);

-- Create indexes for users table
CREATE UNIQUE INDEX ix_users_email ON users (email);
CREATE UNIQUE INDEX ix_users_google_id ON users (google_id);
CREATE INDEX ix_users_id ON users (id);
CREATE UNIQUE INDEX ix_users_ibkr_user_id ON users (ibkr_user_id);
CREATE INDEX ix_users_email_provider ON users (email, auth_provider);
CREATE INDEX ix_users_created_at ON users (created_at);
CREATE INDEX ix_users_last_login ON users (last_login_at);

-- Create check constraints for users table
ALTER TABLE users ADD CONSTRAINT ck_email_password_required 
    CHECK (CASE WHEN auth_provider = 'email' THEN hashed_password IS NOT NULL ELSE TRUE END);

ALTER TABLE users ADD CONSTRAINT ck_google_id_required 
    CHECK (CASE WHEN auth_provider = 'google' THEN google_id IS NOT NULL ELSE TRUE END);

-- Create scripts table
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
    
    -- Foreign key constraint
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes for scripts table
CREATE INDEX ix_scripts_id ON scripts (id);
CREATE INDEX ix_scripts_user_status ON scripts (user_id, status);
CREATE INDEX ix_scripts_created_at ON scripts (created_at);
CREATE INDEX ix_scripts_filename ON scripts (filename);
CREATE INDEX ix_scripts_status ON scripts (status);

-- Create check constraints for scripts table
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

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scripts_updated_at BEFORE UPDATE ON scripts 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data (optional)
-- Sample user with email/password authentication
INSERT INTO users (email, username, hashed_password, auth_provider, is_verified) 
VALUES ('admin@dollarclub.com', 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J8.9QKxS6', 'email', true);

-- Sample user with Google authentication
INSERT INTO users (email, username, auth_provider, google_id, is_verified) 
VALUES ('user@gmail.com', 'google_user', 'google', '123456789', true);

-- Sample script
INSERT INTO scripts (user_id, filename, original_filename, file_path, file_size, file_extension, status) 
VALUES (1, 'trading_strategy_001.py', 'my_trading_strategy.py', '/scripts/trading_strategy_001.py', 2048, 'py', 'uploaded');

-- Create views for common queries (optional)
CREATE VIEW user_stats AS
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
    COUNT(s.id) as script_count,
    COALESCE(SUM(CASE WHEN s.status = 'completed' THEN 1 ELSE 0 END), 0) as completed_scripts,
    COALESCE(SUM(CASE WHEN s.status = 'running' THEN 1 ELSE 0 END), 0) as running_scripts,
    COALESCE(SUM(CASE WHEN s.status = 'failed' THEN 1 ELSE 0 END), 0) as failed_scripts
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
    u.email as owner_email
FROM scripts s
JOIN users u ON s.user_id = u.id
WHERE s.status IN ('completed', 'failed', 'cancelled');

-- Create indexes on views (if your PostgreSQL version supports it)
-- CREATE INDEX idx_user_stats_script_count ON user_stats (script_count);
-- CREATE INDEX idx_script_performance_execution_time ON script_performance (execution_time_seconds);

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON users TO dollarclub_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON scripts TO dollarclub_user;
-- GRANT USAGE, SELECT ON SEQUENCE users_id_seq TO dollarclub_user;
-- GRANT USAGE, SELECT ON SEQUENCE scripts_id_seq TO dollarclub_user;

-- Display table information
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('users', 'scripts')
ORDER BY tablename;

-- Display column information
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_schema = 'public' 
AND table_name IN ('users', 'scripts')
ORDER BY table_name, ordinal_position;
