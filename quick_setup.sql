-- Quick Setup SQL for DollarClub Trading Platform
-- Simplified version for immediate table creation

-- Create custom types (enums)
CREATE TYPE authprovider AS ENUM ('email', 'google');
CREATE TYPE scriptstatus AS ENUM ('uploaded', 'running', 'completed', 'failed', 'cancelled');

-- Create users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) NOT NULL,
    hashed_password VARCHAR(255),
    auth_provider authprovider DEFAULT 'email',
    google_id VARCHAR(100) UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    ibkr_user_id VARCHAR(100) UNIQUE,
    ibkr_access_token TEXT,
    ibkr_refresh_token TEXT,
    ibkr_token_expires_at TIMESTAMP,
    ibkr_connected_at TIMESTAMP
);

-- Create scripts table
CREATE TABLE scripts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    file_extension VARCHAR(10),
    status scriptstatus DEFAULT 'uploaded',
    execution_logs TEXT,
    error_message TEXT,
    execution_time_seconds NUMERIC(10, 3),
    memory_usage_mb NUMERIC(10, 2),
    exit_code INTEGER,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create essential indexes
CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_users_google_id ON users (google_id);
CREATE INDEX idx_users_ibkr_user_id ON users (ibkr_user_id);
CREATE INDEX idx_scripts_user_id ON scripts (user_id);
CREATE INDEX idx_scripts_status ON scripts (status);
CREATE INDEX idx_scripts_created_at ON scripts (created_at);

-- Create trigger function for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scripts_updated_at 
    BEFORE UPDATE ON scripts 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data
INSERT INTO users (email, username, hashed_password, auth_provider, is_verified) 
VALUES ('admin@dollarclub.com', 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J8.9QKxS6', 'email', true);

INSERT INTO users (email, username, auth_provider, google_id, is_verified) 
VALUES ('user@gmail.com', 'google_user', 'google', '123456789', true);

INSERT INTO scripts (user_id, filename, original_filename, file_path, file_size, file_extension, status) 
VALUES (1, 'trading_strategy_001.py', 'my_trading_strategy.py', '/scripts/trading_strategy_001.py', 2048, 'py', 'uploaded');

-- Verify tables were created
SELECT 'Tables created successfully!' as status;
SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename IN ('users', 'scripts');
