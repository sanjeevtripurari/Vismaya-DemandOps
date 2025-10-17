#!/usr/bin/env python3
"""
Setup script for Vismaya DemandOps
Handles Python version compatibility and dependency installation
"""

import sys
import subprocess
import os

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        sys.exit(1)
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return version

def install_setuptools():
    """Install setuptools if missing"""
    try:
        import setuptools
        print("✅ setuptools already installed")
    except ImportError:
        print("📦 Installing setuptools...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "setuptools>=65.0.0"])
        print("✅ setuptools installed")

def install_pip_tools():
    """Install pip-tools for better dependency management"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        print("✅ pip upgraded")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Warning: Could not upgrade pip: {e}")

def install_requirements():
    """Install project requirements"""
    print("📦 Installing project dependencies...")
    try:
        # Install requirements with better error handling
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "--upgrade",
            "--no-cache-dir",
            "-r", "requirements.txt"
        ])
        print("✅ All dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        print("\n🔧 Trying alternative installation method...")
        
        # Try installing packages one by one
        with open('requirements.txt', 'r') as f:
            packages = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        failed_packages = []
        for package in packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✅ Installed: {package}")
            except subprocess.CalledProcessError:
                print(f"❌ Failed: {package}")
                failed_packages.append(package)
        
        if failed_packages:
            print(f"\n⚠️  Some packages failed to install: {failed_packages}")
            print("The application may still work with mock data")
            return False
        
        return True

def create_virtual_env():
    """Create virtual environment if not exists"""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment detected")
        return True
    
    print("⚠️  No virtual environment detected")
    response = input("Create virtual environment? (y/n): ").lower().strip()
    
    if response == 'y':
        try:
            subprocess.check_call([sys.executable, "-m", "venv", "venv"])
            print("✅ Virtual environment created")
            print("🔄 Please activate it and run setup again:")
            if os.name == 'nt':  # Windows
                print("   venv\\Scripts\\activate")
            else:  # Unix/Linux/Mac
                print("   source venv/bin/activate")
            print("   python setup.py")
            return False
        except subprocess.CalledProcessError as e:
            print(f"❌ Error creating virtual environment: {e}")
            return False
    
    return True

def main():
    """Main setup function"""
    print("=" * 50)
    print("🛠️  Vismaya DemandOps - Setup")
    print("=" * 50)
    
    # Check Python version
    version = check_python_version()
    
    # Handle Python 3.12+ distutils issue
    if version.major == 3 and version.minor >= 12:
        print("🔧 Python 3.12+ detected - installing compatibility packages...")
        install_setuptools()
    
    # Check virtual environment
    if not create_virtual_env():
        return
    
    # Upgrade pip and install tools
    install_pip_tools()
    
    # Install setuptools first
    install_setuptools()
    
    # Install requirements
    success = install_requirements()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Setup completed successfully!")
        print("\n🚀 Next steps:")
        print("   1. Configure AWS: python aws-setup.py")
        print("   2. Test locally: python local-test.py")
        print("   3. Run app: python app.py")
    else:
        print("⚠️  Setup completed with warnings")
        print("   The app may work with limited functionality")
        print("\n🚀 Try running: python app.py")
    print("=" * 50)

if __name__ == "__main__":
    main()