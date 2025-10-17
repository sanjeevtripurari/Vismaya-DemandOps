#!/usr/bin/env python3
"""
Vismaya DemandOps - Smart Startup Script
Ensures proper virtual environment activation and dependency management
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def check_venv_exists():
    """Check if virtual environment exists"""
    venv_path = Path('venv')
    
    if not venv_path.exists():
        print("❌ Virtual environment not found")
        print("🔧 Creating virtual environment...")
        
        try:
            subprocess.check_call([sys.executable, "-m", "venv", "venv"])
            print("✅ Virtual environment created")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create virtual environment: {e}")
            return False
    
    print("✅ Virtual environment found")
    return True

def get_venv_python():
    """Get the Python executable path in virtual environment"""
    if platform.system() == "Windows":
        return Path("venv") / "Scripts" / "python.exe"
    else:
        return Path("venv") / "bin" / "python"

def get_venv_activate():
    """Get the activation script path"""
    if platform.system() == "Windows":
        return Path("venv") / "Scripts" / "activate.bat"
    else:
        return Path("venv") / "bin" / "activate"

def install_dependencies():
    """Install dependencies in virtual environment"""
    venv_python = get_venv_python()
    
    if not venv_python.exists():
        print("❌ Virtual environment Python not found")
        return False
    
    print("📦 Installing/updating dependencies...")
    
    try:
        # Upgrade pip first
        subprocess.check_call([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"])
        
        # Install setuptools for Python 3.12+ compatibility
        subprocess.check_call([str(venv_python), "-m", "pip", "install", "--upgrade", "setuptools>=65.0.0"])
        
        # Install psutil for process management
        subprocess.check_call([str(venv_python), "-m", "pip", "install", "psutil"])
        
        # Install project dependencies
        subprocess.check_call([str(venv_python), "-m", "pip", "install", "-r", "requirements.txt"])
        
        print("✅ Dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def stop_existing_processes():
    """Stop any existing Vismaya processes"""
    try:
        venv_python = get_venv_python()
        subprocess.run([str(venv_python), "quick-stop.py", "--silent"], 
                      capture_output=True, timeout=30)
        print("✅ Existing processes stopped")
    except Exception as e:
        print(f"⚠️  Could not stop existing processes: {e}")

def start_application():
    """Start the application in virtual environment"""
    venv_python = get_venv_python()
    
    if not venv_python.exists():
        print("❌ Virtual environment Python not found")
        return False
    
    print("🚀 Starting Vismaya DemandOps...")
    
    try:
        # Run the application
        subprocess.run([str(venv_python), "app.py"])
        return True
        
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
        return True
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        return False

def show_startup_info():
    """Show startup information"""
    print("=" * 60)
    print("🎯 Vismaya DemandOps - Smart Startup")
    print("AI-Powered FinOps Platform for AWS Cost Optimization")
    print("Team MaximAI")
    print("=" * 60)

def main():
    """Main startup function"""
    show_startup_info()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check/create virtual environment
    if not check_venv_exists():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("⚠️  Dependency installation failed, but continuing...")
    
    # Stop existing processes
    stop_existing_processes()
    
    # Start application
    if not start_application():
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ Vismaya DemandOps session completed")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Startup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Startup failed: {e}")
        sys.exit(1)