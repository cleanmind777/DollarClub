"""Enhanced user and script schema with SQLAlchemy features

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create auth_provider enum
    auth_provider_enum = postgresql.ENUM('email', 'google', name='authprovider')
    auth_provider_enum.create(op.get_bind())
    
    # Create users table with enhanced features
    op.create_table('users',
        # Primary key
        sa.Column('id', sa.Integer(), nullable=False),
        
        # Authentication fields
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=True),
        sa.Column('auth_provider', auth_provider_enum, nullable=True),
        sa.Column('google_id', sa.String(length=100), nullable=True),
        
        # Account status
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True, default=False),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        
        # IBKR Integration
        sa.Column('ibkr_user_id', sa.String(length=100), nullable=True),
        sa.Column('ibkr_access_token', sa.Text(), nullable=True),
        sa.Column('ibkr_refresh_token', sa.Text(), nullable=True),
        sa.Column('ibkr_token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('ibkr_connected_at', sa.DateTime(), nullable=True),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for users table
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_google_id', 'users', ['google_id'], unique=True)
    op.create_index('ix_users_id', 'users', ['id'], unique=False)
    op.create_index('ix_users_ibkr_user_id', 'users', ['ibkr_user_id'], unique=True)
    op.create_index('ix_users_email_provider', 'users', ['email', 'auth_provider'])
    op.create_index('ix_users_created_at', 'users', ['created_at'])
    op.create_index('ix_users_last_login', 'users', ['last_login_at'])
    
    # Create check constraints for users table
    op.create_check_constraint(
        'ck_email_password_required',
        'users',
        "CASE WHEN auth_provider = 'email' THEN hashed_password IS NOT NULL ELSE TRUE END"
    )
    op.create_check_constraint(
        'ck_google_id_required',
        'users',
        "CASE WHEN auth_provider = 'google' THEN google_id IS NOT NULL ELSE TRUE END"
    )
    
    # Create script_status enum
    script_status_enum = postgresql.ENUM('uploaded', 'running', 'completed', 'failed', 'cancelled', name='scriptstatus')
    script_status_enum.create(op.get_bind())
    
    # Create scripts table with enhanced features
    op.create_table('scripts',
        # Primary key
        sa.Column('id', sa.Integer(), nullable=False),
        
        # Foreign key relationship
        sa.Column('user_id', sa.Integer(), nullable=False),
        
        # File information
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_extension', sa.String(length=10), nullable=True),
        
        # Execution information
        sa.Column('status', script_status_enum, nullable=False, default='uploaded'),
        sa.Column('execution_logs', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        
        # Execution metrics
        sa.Column('execution_time_seconds', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('memory_usage_mb', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('exit_code', sa.Integer(), nullable=True),
        
        # Timestamps
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for scripts table
    op.create_index('ix_scripts_id', 'scripts', ['id'], unique=False)
    op.create_index('ix_scripts_user_status', 'scripts', ['user_id', 'status'])
    op.create_index('ix_scripts_created_at', 'scripts', ['created_at'])
    op.create_index('ix_scripts_filename', 'scripts', ['filename'])
    op.create_index('ix_scripts_status', 'scripts', ['status'])
    
    # Create check constraints for scripts table
    op.create_check_constraint(
        'ck_positive_file_size',
        'scripts',
        'file_size > 0'
    )
    op.create_check_constraint(
        'ck_non_negative_execution_time',
        'scripts',
        'execution_time_seconds >= 0'
    )
    op.create_check_constraint(
        'ck_non_negative_memory',
        'scripts',
        'memory_usage_mb >= 0'
    )
    op.create_check_constraint(
        'ck_completed_has_completion_time',
        'scripts',
        "CASE WHEN status IN ('completed', 'failed', 'cancelled') THEN completed_at IS NOT NULL ELSE TRUE END"
    )
    op.create_check_constraint(
        'ck_running_has_start_time',
        'scripts',
        "CASE WHEN status = 'running' THEN started_at IS NOT NULL ELSE TRUE END"
    )


def downgrade() -> None:
    # Drop check constraints for scripts
    op.drop_constraint('ck_running_has_start_time', 'scripts', type_='check')
    op.drop_constraint('ck_completed_has_completion_time', 'scripts', type_='check')
    op.drop_constraint('ck_non_negative_memory', 'scripts', type_='check')
    op.drop_constraint('ck_non_negative_execution_time', 'scripts', type_='check')
    op.drop_constraint('ck_positive_file_size', 'scripts', type_='check')
    
    # Drop indexes for scripts
    op.drop_index('ix_scripts_status', table_name='scripts')
    op.drop_index('ix_scripts_filename', table_name='scripts')
    op.drop_index('ix_scripts_created_at', table_name='scripts')
    op.drop_index('ix_scripts_user_status', table_name='scripts')
    op.drop_index('ix_scripts_id', table_name='scripts')
    
    # Drop scripts table
    op.drop_table('scripts')
    
    # Drop check constraints for users
    op.drop_constraint('ck_google_id_required', 'users', type_='check')
    op.drop_constraint('ck_email_password_required', 'users', type_='check')
    
    # Drop indexes for users
    op.drop_index('ix_users_last_login', table_name='users')
    op.drop_index('ix_users_created_at', table_name='users')
    op.drop_index('ix_users_email_provider', table_name='users')
    op.drop_index('ix_users_ibkr_user_id', table_name='users')
    op.drop_index('ix_users_id', table_name='users')
    op.drop_index('ix_users_google_id', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    
    # Drop users table
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS scriptstatus')
    op.execute('DROP TYPE IF EXISTS authprovider')
