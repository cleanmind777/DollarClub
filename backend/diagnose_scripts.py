#!/usr/bin/env python3
"""
Diagnose script execution issues
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.script import Script
from app.tasks.script_execution import running_processes

db = SessionLocal()

print("=" * 60)
print("Script Execution Diagnostic")
print("=" * 60)
print()

# Check scripts in database
scripts = db.query(Script).all()
print(f"1. Scripts in Database: {len(scripts)}")
print("-" * 60)

for script in scripts:
    print(f"ID: {script.id}")
    print(f"  File: {script.original_filename}")
    print(f"  Status: {script.status.value}")
    print(f"  Path: {script.file_path}")
    print(f"  Exists: {os.path.exists(script.file_path)}")
    print()

# Check running processes
print()
print(f"2. Running Processes in Memory: {len(running_processes)}")
print("-" * 60)

if running_processes:
    for script_id, process in running_processes.items():
        print(f"Script ID: {script_id}")
        print(f"  Process: {process}")
        print(f"  Running: {process.poll() is None}")
        print()
else:
    print("No processes in memory")
    print()

# Recommendations
print()
print("3. Recommendations:")
print("-" * 60)

stuck_scripts = [s for s in scripts if s.status.value == 'RUNNING']
if stuck_scripts:
    print(f"[WARNING] {len(stuck_scripts)} script(s) stuck in RUNNING status:")
    for s in stuck_scripts:
        print(f"  - Script {s.id} ({s.original_filename})")
    print()
    print("To fix, run:")
    print('  python -c "from app.core.database import SessionLocal; from app.models.script import Script, ScriptStatus; from datetime import datetime; db = SessionLocal(); db.query(Script).filter(Script.status == ScriptStatus.RUNNING).update({Script.status: ScriptStatus.FAILED, Script.error_message: \'Reset\', Script.completed_at: datetime.utcnow()}); db.commit()"')
else:
    print("[OK] No stuck scripts")

print()
print("=" * 60)

db.close()

