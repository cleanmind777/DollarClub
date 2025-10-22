"""
Package validation service for user scripts
Detects and validates package dependencies before execution
"""
import ast
import re
import subprocess
import sys
import logging
from typing import List, Set, Tuple, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Mapping of common import names to package names
IMPORT_TO_PACKAGE = {
    'cv2': 'opencv-python',
    'PIL': 'Pillow',
    'sklearn': 'scikit-learn',
    'yaml': 'PyYAML',
    'dateutil': 'python-dateutil',
    'bs4': 'beautifulsoup4',
    'dotenv': 'python-dotenv',
}

# Packages that are part of standard library (don't need installation)
STDLIB_MODULES = {
    'abc', 'argparse', 'asyncio', 'base64', 'collections', 'concurrent',
    'copy', 'csv', 'datetime', 'decimal', 'email', 'enum', 'functools',
    'glob', 'hashlib', 'hmac', 'http', 'io', 'itertools', 'json', 'logging',
    'math', 'multiprocessing', 'operator', 'os', 'pathlib', 'pickle', 'queue',
    're', 'random', 'shutil', 'signal', 'socket', 'sqlite3', 'statistics',
    'string', 'subprocess', 'sys', 'tempfile', 'threading', 'time', 'typing',
    'unittest', 'urllib', 'uuid', 'warnings', 'weakref', 'xml', 'zipfile',
}


class PackageValidator:
    """Validate and manage package dependencies for scripts"""
    
    def __init__(self):
        self.installed_packages = self._get_installed_packages()
    
    def _get_installed_packages(self) -> Set[str]:
        """Get list of installed packages"""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--format=freeze'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            packages = set()
            for line in result.stdout.split('\n'):
                if line and '==' in line:
                    pkg_name = line.split('==')[0].lower()
                    packages.add(pkg_name)
            
            logger.info(f"Found {len(packages)} installed packages")
            return packages
            
        except Exception as e:
            logger.error(f"Error getting installed packages: {e}")
            return set()
    
    def extract_imports(self, script_path: str) -> Set[str]:
        """Extract all import statements from a Python script"""
        imports = set()
        
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=script_path)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        # Get top-level package name
                        package = alias.name.split('.')[0]
                        imports.add(package)
                        
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        # Get top-level package name
                        package = node.module.split('.')[0]
                        imports.add(package)
            
            logger.info(f"Extracted {len(imports)} imports from {script_path}")
            return imports
            
        except Exception as e:
            logger.error(f"Error extracting imports from {script_path}: {e}")
            return set()
    
    def validate_packages(self, script_path: str) -> Tuple[bool, List[str], List[str]]:
        """
        Validate if all required packages are installed
        
        Returns:
            (all_installed, missing_packages, available_packages)
        """
        imports = self.extract_imports(script_path)
        
        # Filter out stdlib modules
        external_imports = {imp for imp in imports if imp not in STDLIB_MODULES}
        
        missing = []
        available = []
        
        for import_name in external_imports:
            # Map import name to package name
            package_name = IMPORT_TO_PACKAGE.get(import_name, import_name)
            package_name_lower = package_name.lower()
            
            if package_name_lower in self.installed_packages:
                available.append(package_name)
            else:
                missing.append(package_name)
        
        all_installed = len(missing) == 0
        
        if missing:
            logger.warning(f"Missing packages: {missing}")
        
        return all_installed, missing, available
    
    def get_install_command(self, packages: List[str]) -> str:
        """Generate pip install command for missing packages"""
        if not packages:
            return ""
        
        return f"pip install {' '.join(packages)}"
    
    def create_error_message(self, missing_packages: List[str]) -> str:
        """Create user-friendly error message for missing packages"""
        if not missing_packages:
            return ""
        
        install_cmd = self.get_install_command(missing_packages)
        
        message = f"""
Missing Python packages detected!

Your script requires the following packages that are not installed:
{', '.join(missing_packages)}

To install these packages, run:
{install_cmd}

Or ask your administrator to install them in the backend environment.
""".strip()
        
        return message
    
    def auto_install_packages(self, packages: List[str]) -> Tuple[bool, str]:
        """
        Automatically install missing packages (use with caution!)
        
        Returns:
            (success, message)
        """
        if not packages:
            return True, "No packages to install"
        
        try:
            logger.info(f"Auto-installing packages: {packages}")
            
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install'] + packages,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                # Refresh installed packages cache
                self.installed_packages = self._get_installed_packages()
                message = f"Successfully installed: {', '.join(packages)}"
                logger.info(message)
                return True, message
            else:
                message = f"Failed to install packages: {result.stderr}"
                logger.error(message)
                return False, message
                
        except subprocess.TimeoutExpired:
            message = "Package installation timed out"
            logger.error(message)
            return False, message
        except Exception as e:
            message = f"Error installing packages: {str(e)}"
            logger.error(message)
            return False, message


# Global validator instance
validator = PackageValidator()

