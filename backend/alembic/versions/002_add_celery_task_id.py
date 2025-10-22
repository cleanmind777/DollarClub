"""add celery_task_id to scripts table

Revision ID: 002
Revises: 001
Create Date: 2025-10-20

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Add celery_task_id column to scripts table
    op.add_column('scripts', sa.Column('celery_task_id', sa.String(255), nullable=True))
    op.create_index('ix_scripts_celery_task_id', 'scripts', ['celery_task_id'])


def downgrade():
    # Remove celery_task_id column
    op.drop_index('ix_scripts_celery_task_id', 'scripts')
    op.drop_column('scripts', 'celery_task_id')

