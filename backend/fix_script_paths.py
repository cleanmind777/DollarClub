#!/usr/bin/env python3
"""
Fix script file paths in database
Converts relative paths to absolute paths
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.script import Script
from app.core.config import settings

def fix_script_paths():
    """Fix script paths from relative to absolute"""
    db = SessionLocal()
    
    try:
        # Get all scripts
        scripts = db.query(Script).all()
        
        print(f"Found {len(scripts)} scripts in database")
        print("=" * 60)
        
        fixed_count = 0
        
        for script in scripts:
            old_path = script.file_path
            
            # Check if path is relative
            if not os.path.isabs(old_path):
                # Convert to absolute path
                new_path = os.path.abspath(old_path)
                
                print(f"Script ID {script.id}:")
                print(f"  Old: {old_path}")
                print(f"  New: {new_path}")
                
                # Check if file exists at new path
                if os.path.exists(new_path):
                    script.file_path = new_path
                    fixed_count += 1
                    print(f"  Status: FIXED (file exists)")
                else:
                    # Try to find the file in scripts directory
                    filename = os.path.basename(old_path)
                    scripts_path = os.path.abspath(os.path.join(settings.SCRIPTS_DIR, filename))
                    
                    if os.path.exists(scripts_path):
                        script.file_path = scripts_path
                        fixed_count += 1
                        print(f"  Status: FIXED (found in scripts dir)")
                    else:
                        print(f"  Status: FILE NOT FOUND (skipped)")
                
                print()
            elif "scripts\\scripts\\" in old_path or "scripts/scripts/" in old_path:
                # Fix duplicate scripts directory
                new_path = old_path.replace("scripts\\scripts\\", "scripts\\").replace("scripts/scripts/", "scripts/")
                
                print(f"Script ID {script.id}:")
                print(f"  Old: {old_path}")
                print(f"  New: {new_path}")
                
                if os.path.exists(new_path):
                    script.file_path = new_path
                    fixed_count += 1
                    print(f"  Status: FIXED (removed duplicate)")
                else:
                    print(f"  Status: FILE NOT FOUND (skipped)")
                
                print()
        
        # Commit changes
        if fixed_count > 0:
            db.commit()
            print("=" * 60)
            print(f"[OK] Fixed {fixed_count} script paths")
            print("=" * 60)
        else:
            print("=" * 60)
            print("[OK] No scripts needed fixing")
            print("=" * 60)
    
    except Exception as e:
        print(f"[ERROR] Failed to fix paths: {e}")
        db.rollback()
    
    finally:
        db.close()

if __name__ == '__main__':
    fix_script_paths()

