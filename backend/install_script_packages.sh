#!/bin/bash
# Install common packages for user trading scripts (Linux/macOS)

echo "======================================================================"
echo "Installing common packages for user trading scripts..."
echo "======================================================================"
echo

# Check if virtual environment exists
if [ -f "venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
    echo
fi

# Run the Python installation script
python3 install_script_packages.py

# Exit with the script's exit code
exit $?

