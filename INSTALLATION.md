# Installation Guide

## Quick Start

### Option 1: Minimal Installation (Recommended)
```bash
pip install -r requirements-minimal.txt
```

### Option 2: Full Installation
```bash
pip install -r requirements.txt
```

### Option 3: Development Installation
```bash
pip install -r requirements-dev.txt
```

## Package Installation Issues

If you encounter package installation errors, try these solutions:

### 1. Use Minimal Requirements
Some packages in the full requirements may not be available on all systems. Use the minimal requirements first:
```bash
pip install -r requirements-minimal.txt
```

### 2. Install Optional Packages Separately
Install packages separately as needed:
```bash
# For real-time notifications (WebSocket support)
pip install websockets

# For AI features
pip install anthropic openai

# For advanced workflow management
pip install langchain langchain-community

# For email notifications
pip install sendgrid

# For caching
pip install redis cachetools

# For database features
pip install sqlalchemy alembic

# For monitoring
pip install structlog prometheus-client
```

### 3. Virtual Environment Setup
Always use a virtual environment:
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install packages
pip install -r requirements-minimal.txt
```

### 4. Python Version Compatibility
Ensure you're using Python 3.9 or higher:
```bash
python --version
```

### 5. Update pip
Make sure pip is up to date:
```bash
pip install --upgrade pip
```

## Core Dependencies

The system requires these essential packages:
- `streamlit` - Web interface
- `boto3` - AWS integration
- `pandas` - Data processing
- `plotly` - Visualizations
- `requests` - HTTP requests
- `python-dotenv` - Environment variables
- `pydantic` - Data validation
- `aiohttp` - Async HTTP
- `rich` - Terminal formatting

## Real-Time Features

For real-time notifications and WebSocket support:
- `websockets` - WebSocket server/client support

## Optional Dependencies

These packages add advanced features but are not required for basic functionality:
- `anthropic`, `openai` - AI model integration
- `langchain` - Advanced AI workflows
- `redis` - Caching
- `sqlalchemy` - Database ORM
- `sendgrid` - Email notifications
- `prometheus-client` - Metrics

## Troubleshooting

### Common Issues

1. **Package not found**: Use requirements-minimal.txt
2. **Version conflicts**: Create a fresh virtual environment
3. **Permission errors**: Use `--user` flag or virtual environment
4. **Network issues**: Try `--trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org`

### Platform-Specific Notes

**Windows:**
- Use `venv\Scripts\activate` to activate virtual environment
- Some packages may require Visual Studio Build Tools

**Linux/Mac:**
- Use `source venv/bin/activate` to activate virtual environment
- May need to install system dependencies for some packages

## Verification

Test your installation:
```bash
python -c "import streamlit, boto3, pandas, plotly; print('Core packages installed successfully')"
```

## Next Steps

After successful installation:
1. Copy `.env.example` to `.env` and configure your settings
2. Run the simple demo: `python demo_migration_simple.py`
3. Install additional packages as needed: `pip install websockets anthropic openai`
4. Run the full demo: `python demo_migration.py`
5. Start the application: `streamlit run app.py`

## Quick Test

Test the migration system:
```bash
# Simple demo (minimal dependencies)
python demo_migration_simple.py

# Full demo (requires all packages)
python demo_migration.py
```