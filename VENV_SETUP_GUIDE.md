# Virtual Environment Setup Guide for Vismaya DemandOps

## 🐍 Virtual Environment Management

This project now includes comprehensive virtual environment management to ensure consistent Python execution across all environments.

## 📁 New Files Created

### Core Virtual Environment Files
- **`venv-manager.py`** - Comprehensive virtual environment management
- **`run-vismaya.py`** - Production startup script with venv
- **`start.py`** - Universal startup script
- **`VENV_SETUP_GUIDE.md`** - This guide

### Updated Files
- **`app.py`** - Enhanced venv detection and auto-restart
- **`setup-ec2.sh`** - Docker with virtual environment
- **`DEPLOYMENT_SUMMARY.md`** - Updated deployment instructions

## 🚀 Quick Start Options

### Option 1: Universal Startup (Recommended)
```bash
python start.py
```
This script will:
- Check Python version compatibility
- Create virtual environment if needed
- Install all dependencies
- Start the application

### Option 2: Comprehensive Setup
```bash
# Setup virtual environment with full management
python venv-manager.py setup

# Run application in virtual environment
python run-vismaya.py
```

### Option 3: Manual Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install --upgrade pip setuptools>=65.0.0
pip install -r requirements.txt

# Run application
python app.py
```

## 🔧 Virtual Environment Manager Features

The `venv-manager.py` script provides:

### Setup Command
```bash
python venv-manager.py setup
```
- Creates virtual environment if needed
- Upgrades pip and setuptools
- Installs all project requirements
- Tests installation
- Shows activation instructions

### Test Command
```bash
python venv-manager.py test
```
- Tests if all packages are installed correctly
- Shows version information
- Validates virtual environment

### Run Command
```bash
python venv-manager.py run --script app.py
```
- Runs any Python script in the virtual environment
- Passes arguments to the script

## 🐳 Docker Integration

The Docker setup now uses virtual environments internally:

```dockerfile
# Create virtual environment in container
RUN python -m venv /app/venv

# Install dependencies in venv
RUN /app/venv/bin/pip install --upgrade pip setuptools>=65.0.0
RUN /app/venv/bin/pip install --no-cache-dir -r requirements.txt

# Use venv Python
CMD ["/app/venv/bin/python", "-m", "streamlit", "run", "app.py"]
```

## 📋 Requirements Management

The `requirements.txt` file includes:
```
streamlit>=1.28.0,<2.0.0
boto3>=1.34.0,<2.0.0
pandas>=2.0.0,<3.0.0
plotly>=5.17.0,<6.0.0
numpy>=1.24.0,<2.0.0
python-dotenv>=1.0.0,<2.0.0
requests>=2.31.0,<3.0.0
setuptools>=65.0.0
psutil>=5.9.0,<6.0.0
```

## 🔍 Troubleshooting

### Virtual Environment Not Found
```bash
# Create new virtual environment
python venv-manager.py setup
```

### Import Errors
```bash
# Test installation
python venv-manager.py test

# Reinstall dependencies
python venv-manager.py setup
```

### Permission Issues (Linux/Mac)
```bash
# Make scripts executable
chmod +x venv-manager.py
chmod +x run-vismaya.py
chmod +x start.py
```

### Python Version Issues
- Ensure Python 3.8+ is installed
- Use `python3` instead of `python` if needed
- Check with `python --version`

## 🌐 Deployment Environments

### Local Development
```bash
python start.py
```

### EC2 Deployment
The setup scripts automatically handle virtual environment:
```bash
curl -sSL https://raw.githubusercontent.com/sanjeevtripurari/Vismaya-DemandOps/v2-dev/setup-ec2.sh | bash
```

### Docker Deployment
```bash
docker-compose up -d
```

## ✅ Verification

After setup, verify everything works:

1. **Check Virtual Environment**
   ```bash
   python venv-manager.py test
   ```

2. **Test Application**
   ```bash
   python start.py
   ```

3. **Check Dependencies**
   ```bash
   # In activated venv
   pip list
   ```

## 🎯 Benefits

- **Isolation**: Dependencies don't conflict with system Python
- **Consistency**: Same environment across development and production
- **Reliability**: Automatic setup and error handling
- **Flexibility**: Multiple startup options for different scenarios
- **Compatibility**: Works on Windows, Linux, and macOS

## 📞 Support

If you encounter issues:
1. Check Python version: `python --version`
2. Run setup: `python venv-manager.py setup`
3. Test installation: `python venv-manager.py test`
4. Check the troubleshooting section above

Your Vismaya DemandOps application now has robust virtual environment management! 🎉