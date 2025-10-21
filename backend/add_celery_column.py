#!/usr/bin/env python3
"""
Add celery_task_id column to scripts table
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine

print("Adding celery_task_id column to scripts table...")

try:
    with engine.begin() as conn:
        # Add column if it doesn't exist
        conn.execute(text("""
            ALTER TABLE scripts 
            ADD COLUMN IF NOT EXISTS celery_task_id VARCHAR(255)
        """))
        
        # Add index if it doesn't exist
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_scripts_celery_task_id 
            ON scripts(celery_task_id)
        """))
    
    print("✅ Successfully added celery_task_id column and index!")
    print("")
    print("Next steps:")
    print("1. Restart Celery worker")
    print("2. Restart backend")
    print("3. Test cancel → execute workflow")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

