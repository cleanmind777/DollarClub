# Package Management - Quick Start Guide

## 🚀 Setup (5 minutes)

### Step 1: Install Common Packages

**Windows:**
```bash
cd backend
install_script_packages.bat
```

**Linux/macOS:**
```bash
cd backend
chmod +x install_script_packages.sh
./install_script_packages.sh
```

This installs ~40 common packages for trading scripts (pandas, numpy, yfinance, etc.)

### Step 2: Verify Installation

Upload and run the test script:
- File: `backend/scripts/test_missing_package.py`
- This tests pandas and numpy

### Step 3: Test Error Handling

Upload and run:
- File: `backend/scripts/test_alpaca_required.py`  
- If alpaca-trade-api is not installed, you'll see a clear error with installation instructions

## ✨ Features

### Automatic Package Detection
✅ Scripts are analyzed before execution  
✅ All `import` statements are detected  
✅ Missing packages are identified instantly  
✅ Clear error messages with exact pip commands  

### User Experience
✅ No configuration needed  
✅ Works immediately after package installation  
✅ Clear, actionable error messages  
✅ Auto-scroll logs in real-time  

### Example Error Message
```
Missing Python packages detected!

Your script requires the following packages that are not installed:
alpaca-trade-api, pandas-ta

To install these packages, run:
pip install alpaca-trade-api pandas-ta

Or ask your administrator to install them in the backend environment.
```

## 📦 Included Packages

After running the installation script, you'll have:

**Data & Analysis:**
- pandas, numpy, scipy
- matplotlib, plotly, seaborn

**Financial APIs:**
- yfinance (Yahoo Finance)
- alpaca-trade-api (Alpaca)
- python-binance (Binance)
- ccxt (Multi-exchange)

**Technical Analysis:**
- pandas-ta
- stockstats

**Machine Learning:**
- scikit-learn
- tensorflow (optional)
- pytorch (optional)

**Utilities:**
- requests, aiohttp
- python-dateutil, pytz
- beautifulsoup4, lxml

## 🔧 Configuration (Optional)

### Enable Auto-Install

⚠️ **Security Warning**: Only enable in trusted environments!

Edit `backend/app/core/config.py`:
```python
AUTO_INSTALL_PACKAGES: bool = True  # Changed from False
```

When enabled, missing packages are automatically installed before script execution.

## 🧪 Testing

### Test 1: Basic Packages (Should Work)
```bash
# Upload: backend/scripts/test_missing_package.py
# Expected: Success (uses pandas, numpy)
```

### Test 2: Missing Package (Should Show Error)
```bash
# Upload: backend/scripts/test_alpaca_required.py
# Expected: Clear error if alpaca-trade-api not installed
# Shows: pip install alpaca-trade-api
```

### Test 3: Your Own Script
```python
# my_script.py
import pandas as pd
import yfinance as yf

data = yf.download("AAPL", start="2024-01-01")
print(data.head())
```

## 🆘 Troubleshooting

### "TA-Lib failed to install"
TA-Lib requires a C library. See [PACKAGE_MANAGEMENT.md](PACKAGE_MANAGEMENT.md) for installation instructions.

**Quick fix**: Comment out TA-Lib in `requirements_scripts.txt` and re-run installation.

### "TensorFlow/PyTorch failed"
These are optional. Scripts work without them unless specifically required.

**Solution**: Install separately with GPU support if needed, or skip them.

### "Script says package missing but it's installed"
1. Check you're in the right environment (venv)
2. Restart Celery worker: `celery -A app.tasks.celery_app worker --loglevel=info --pool=threads --concurrency=1`
3. Check package name matches import name

## 📚 Documentation

- **Full Guide**: [PACKAGE_MANAGEMENT.md](PACKAGE_MANAGEMENT.md)
- **Logging Improvements**: [LOGGING_IMPROVEMENTS.md](LOGGING_IMPROVEMENTS.md)
- **Main README**: [../README.md](../README.md)

## 🎯 Best Practices

### For Administrators
1. ✅ Run `install_script_packages.bat/.sh` on first setup
2. ✅ Keep packages updated monthly
3. ✅ Monitor logs for frequently requested packages
4. ✅ Keep AUTO_INSTALL_PACKAGES disabled (security)

### For Users
1. ✅ Use common packages (pandas, numpy, yfinance)
2. ✅ Test scripts locally first
3. ✅ Report missing packages to admin with error message
4. ✅ Check error logs - they tell you exactly what to install

## 💡 Tips

- **Error messages are your friend**: They show the exact pip command needed
- **Test incremental**: Start with simple imports, add complexity
- **Document dependencies**: Add a comment at the top of your script listing required packages
- **Share error messages**: Copy the full error message when asking admin for help

## ⚡ Quick Commands

```bash
# Install all common packages
cd backend && install_script_packages.bat  # Windows
cd backend && ./install_script_packages.sh  # Linux/Mac

# Install specific package
pip install package-name

# List installed packages
pip list

# Check if package is installed
pip show package-name

# Restart Celery after installing packages
# Press Ctrl+C to stop, then:
celery -A app.tasks.celery_app worker --loglevel=info --pool=threads --concurrency=1
```

## ✅ Success Checklist

- [ ] Ran `install_script_packages` script
- [ ] Tested with `test_missing_package.py` (should succeed)
- [ ] Tested with `test_alpaca_required.py` (may fail with clear error)
- [ ] Uploaded own script and checked for package errors
- [ ] Restarted Celery worker after installing new packages
- [ ] Reviewed [PACKAGE_MANAGEMENT.md](PACKAGE_MANAGEMENT.md) for advanced options

---

**Need Help?** Check the full documentation in [PACKAGE_MANAGEMENT.md](PACKAGE_MANAGEMENT.md)

