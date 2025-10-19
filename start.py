#!/usr/bin/env python3
"""
Vismaya DemandOps - Universal Startup Script
Works in any environment with proper virtual environment management
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_header():
    """Print application header"""
    print("=" * 60)
    print("🎯 Vismaya DemandOps")
    print("AI-Powered FinOps Platform for AWS Cost Optimization")
    print("Team MaximAI")
    print("=" * 60)

def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required. Current: {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def get_venv_paths():
    """Get virtual environment paths"""
    is_windows = platform.system() == "Windows"
    venv_dir = Path("venv")
    
    if is_windows:
        python_exe = venv_dir / "Scripts" / "python.exe"
        activate_script = venv_dir / "Scripts" / "activate.bat"
    else:
        python_exe = venv_dir / "bin" / "python"
        activate_script = venv_dir / "bin" / "activate"
    
    return python_exe, activate_script

def is_in_venv():
    """Check if currently in virtual environment"""
    return (hasattr(sys, 'real_prefix') or 
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))

def setup_venv():
    """Setup virtual environment if needed"""
    python_exe, _ = get_venv_paths()
    
    if python_exe.exists():
        print("✅ Virtual environment found")
        return True
    
    print("📦 Creating virtual environment...")
    try:
        subprocess.check_call([sys.executable, "-m", "venv", "venv"])
        print("✅ Virtual environment created")
        
        # Install dependencies
        print("📦 Installing dependencies...")
        subprocess.check_call([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([str(python_exe), "-m", "pip", "install", "--upgrade", "setuptools>=65.0.0"])
        subprocess.check_call([str(python_exe), "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error setting up virtual environment: {e}")
        return False

def run_application():
    """Run the application"""
    python_exe, activate_script = get_venv_paths()
    
    if is_in_venv():
        # Already in venv, run directly
        print("🚀 Starting application in current virtual environment...")
        try:
            subprocess.run([sys.executable, "app.py"])
        except KeyboardInterrupt:
            print("\n👋 Application stopped")
    
    elif python_exe.exists():
        # Use venv python
        print("🚀 Starting application in virtual environment...")
        try:
            subprocess.run([str(python_exe), "app.py"])
        except KeyboardInterrupt:
            print("\n👋 Application stopped")
    
    else:
        print("❌ Virtual environment not available")
        return False
    
    return True

def main():
    """Main function"""
    print_header()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Setup virtual environment
    if not setup_venv():
        sys.exit(1)
    
    # Run application
    if not run_application():
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ Session completed")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)