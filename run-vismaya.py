#!/usr/bin/env python3
"""
Vismaya DemandOps - Production Startup Script
Ensures proper virtual environment and runs the application
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def get_venv_python():
    """Get virtual environment Python executable"""
    if platform.system() == "Windows":
        return Path("venv") / "Scripts" / "python.exe"
    else:
        return Path("venv") / "bin" / "python"

def check_venv_available():
    """Check if virtual environment is available"""
    venv_python = get_venv_python()
    return venv_python.exists()

def setup_venv_if_needed():
    """Setup virtual environment if it doesn't exist"""
    if not check_venv_available():
        print("🔧 Virtual environment not found. Setting up...")
        
        # Try venv-manager first
        if Path("venv-manager.py").exists():
            result = subprocess.run([sys.executable, "venv-manager.py", "setup"])
            return result.returncode == 0
        
        # Fallback to setup-venv.py
        elif Path("setup-venv.py").exists():
            result = subprocess.run([sys.executable, "setup-venv.py"])
            return result.returncode == 0
        
        else:
            print("❌ No setup script found")
            return False
    
    return True

def run_in_venv():
    """Run the application in virtual environment"""
    venv_python = get_venv_python()
    
    if not venv_python.exists():
        print("❌ Virtual environment Python not found")
        return False
    
    print("🚀 Starting Vismaya DemandOps in virtual environment...")
    
    try:
        # Run app.py in virtual environment
        subprocess.run([str(venv_python), "app.py"])
        return True
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
        return True
    except Exception as e:
        print(f"❌ Error running application: {e}")
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("🎯 Vismaya DemandOps - Production Startup")
    print("AI-Powered FinOps Platform for AWS Cost Optimization")
    print("Team MaximAI")
    print("=" * 60)
    
    # Setup virtual environment if needed
    if not setup_venv_if_needed():
        print("❌ Failed to setup virtual environment")
        sys.exit(1)
    
    # Run application in virtual environment
    if not run_in_venv():
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