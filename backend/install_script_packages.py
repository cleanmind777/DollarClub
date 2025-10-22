#!/usr/bin/env python3
"""
Install common packages for user trading scripts
Run this script to prepare the environment for user-uploaded scripts
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    print("=" * 70)
    print("Installing common packages for user trading scripts...")
    print("=" * 70)
    print()
    
    # Get the requirements file path
    script_dir = Path(__file__).parent
    requirements_file = script_dir / "requirements_scripts.txt"
    
    if not requirements_file.exists():
        print(f"ERROR: Requirements file not found: {requirements_file}")
        return 1
    
    print(f"Using requirements file: {requirements_file}")
    print()
    
    # Check Python version
    python_version = sys.version_info
    print(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    print(f"Python executable: {sys.executable}")
    print()
    
    # Upgrade pip first
    print("Step 1: Upgrading pip...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
            check=True
        )
        print("✓ pip upgraded successfully")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to upgrade pip: {e}")
        print("Continuing anyway...")
    print()
    
    # Install packages
    print("Step 2: Installing packages from requirements_scripts.txt...")
    print("This may take several minutes...")
    print()
    
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
            check=True
        )
        print()
        print("=" * 70)
        print("✓ All packages installed successfully!")
        print("=" * 70)
        return 0
        
    except subprocess.CalledProcessError as e:
        print()
        print("=" * 70)
        print("✗ Some packages failed to install")
        print("=" * 70)
        print()
        print("Common issues:")
        print("1. TA-Lib requires the TA-Lib C library to be installed first")
        print("   - Windows: Download from https://github.com/mrjbq7/ta-lib")
        print("   - Linux: sudo apt-get install ta-lib")
        print("   - macOS: brew install ta-lib")
        print()
        print("2. TensorFlow/PyTorch may require specific CUDA versions for GPU support")
        print()
        print("3. Some packages may not be available for your Python version")
        print()
        print("You can continue without these packages.")
        print("Users will see clear error messages if their scripts need them.")
        return 1

if __name__ == "__main__":
    exit(main())

