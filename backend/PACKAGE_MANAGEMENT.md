# Package Management for User Scripts

## Overview

The DollarClub platform automatically validates package dependencies for user-uploaded scripts and provides clear error messages when packages are missing.

## Quick Start

### For Administrators

**Install common trading packages:**

```bash
# Windows
cd backend
install_script_packages.bat

# Linux/macOS
cd backend
chmod +x install_script_packages.sh
./install_script_packages.sh

# Or directly with Python
cd backend
python install_script_packages.py
```

This will install commonly used packages for trading scripts including:
- Data manipulation: pandas, numpy, scipy
- Financial data: yfinance, alpaca-trade-api, python-binance, ccxt
- Technical analysis: pandas-ta, stockstats
- Machine learning: scikit-learn, tensorflow, pytorch
- Visualization: matplotlib, plotly, seaborn
- And more...

### For Users

When you upload a script that requires packages not installed on the server:

1. **Clear Error Message**: You'll see exactly which packages are missing
2. **Installation Command**: The error message includes the exact `pip install` command
3. **Contact Admin**: Share the error message with your administrator

## How It Works

### Automatic Package Detection

The platform automatically:
1. ✅ Analyzes your script before execution
2. ✅ Detects all `import` statements
3. ✅ Checks if required packages are installed
4. ✅ Provides clear error messages with package names
5. ✅ Shows the exact pip command to install missing packages

### Example Error Message

```
Missing Python packages detected!

Your script requires the following packages that are not installed:
alpaca-trade-api, pandas-ta

To install these packages, run:
pip install alpaca-trade-api pandas-ta

Or ask your administrator to install them in the backend environment.
```

## Package Categories

### Pre-installed Essentials
Standard library packages (no installation needed):
- `os`, `sys`, `time`, `datetime`, `json`, `csv`, `math`, etc.

### Common Trading Packages
Recommended to pre-install (see `requirements_scripts.txt`):
- **Data**: pandas, numpy, scipy
- **Finance**: yfinance, alpaca-trade-api, ccxt
- **Analysis**: pandas-ta, stockstats
- **ML**: scikit-learn
- **Plotting**: matplotlib, plotly

### User-Specific Packages
Installed on-demand when users need them:
- Less common trading APIs
- Specialized analysis libraries
- Custom internal packages

## Configuration Options

### Enable Auto-Install (Optional)

⚠️ **Security Warning**: Auto-installing packages can be risky. Only enable in trusted environments.

To enable automatic package installation, modify `backend/app/core/config.py`:

```python
# Package management
AUTO_INSTALL_PACKAGES: bool = False  # Set to True to enable
```

When enabled, the system will automatically install missing packages before script execution.

### Custom Package Mappings

Some packages have different import names than their pip names. These are handled automatically:

```python
cv2 → opencv-python
PIL → Pillow
sklearn → scikit-learn
yaml → PyYAML
bs4 → beautifulsoup4
```

## Troubleshooting

### TA-Lib Installation Issues

TA-Lib requires a C library. Install it before running pip:

**Windows:**
```bash
# Download from https://github.com/mrjbq7/ta-lib
# Then: pip install ta-lib
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install ta-lib
pip install ta-lib
```

**macOS:**
```bash
brew install ta-lib
pip install ta-lib
```

### TensorFlow/PyTorch GPU Support

For GPU support, install CUDA first, then use specific package versions:
```bash
# TensorFlow with GPU
pip install tensorflow[and-cuda]

# PyTorch with GPU (check pytorch.org for your CUDA version)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Package Not Found

If a package is not in PyPI:
1. Check the correct package name on [pypi.org](https://pypi.org)
2. Install from GitHub: `pip install git+https://github.com/user/repo.git`
3. Add to `requirements_scripts.txt` for future use

## Best Practices

### For Administrators

1. **Pre-install Common Packages**: Run the installation script regularly
2. **Monitor Usage**: Check logs for frequently requested packages
3. **Update Regularly**: Keep packages up-to-date for security
4. **Document Custom Packages**: Maintain a list of user-requested packages

### For Users

1. **Use Common Packages**: Stick to pandas, numpy, yfinance, etc.
2. **Test Locally First**: Test your script with required packages locally
3. **Document Dependencies**: Add comments listing required packages
4. **Report Issues**: Contact admin if packages are missing

### For Developers

1. **Add Package Detection**: The validator automatically detects most packages
2. **Custom Mappings**: Add special cases to `IMPORT_TO_PACKAGE` in `package_validator.py`
3. **Whitelist Packages**: Add trusted packages to auto-install whitelist
4. **Version Pinning**: Pin critical package versions in requirements

## Security Considerations

### Package Validation
- ✅ Only analyzes import statements (safe)
- ✅ Does not execute user code during validation
- ✅ Checks against installed packages list

### Auto-Installation
- ⚠️ **Disabled by default** for security
- ⚠️ Can install arbitrary packages if enabled
- ⚠️ Only enable in trusted environments
- ✅ Logs all installation attempts

### Sandboxing
Future enhancements:
- Virtual environments per user
- Container isolation per script
- Package whitelisting
- Resource limits

## API Reference

### PackageValidator Class

```python
from app.services.package_validator import validator

# Validate a script
all_ok, missing, available = validator.validate_packages("path/to/script.py")

# Generate error message
error_msg = validator.create_error_message(missing)

# Auto-install (if enabled)
success, message = validator.auto_install_packages(missing)
```

## Examples

### Example 1: Simple Trading Script

```python
# my_trading_bot.py
import pandas as pd
import yfinance as yf
import numpy as np

# Script will work if pandas, yfinance, numpy are installed
```

### Example 2: Advanced ML Script

```python
# ml_strategy.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import matplotlib.pyplot as plt

# Requires: pandas, numpy, scikit-learn, matplotlib
```

### Example 3: Custom Packages

```python
# custom_indicators.py
import pandas as pd
import pandas_ta as ta
from alpaca_trade_api import REST

# Requires: pandas, pandas-ta, alpaca-trade-api
# If missing, user will see clear error with install command
```

## Support

For questions or issues:
1. Check the error message - it tells you exactly what's needed
2. Review this documentation
3. Contact your system administrator
4. Check logs: `backend/logs/` for detailed information

