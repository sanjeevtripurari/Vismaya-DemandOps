#!/usr/bin/env python3
"""
Virtual Environment Setup for Vismaya DemandOps
Creates and configures a virtual environment for the project
"""

import os
import sys
import subprocess
import platform

def create_venv():
    """Create virtual environment"""
    venv_name = "venv"
    
    if os.path.exists(venv_name):
        print(f"✅ Virtual environment '{venv_name}' already exists")
        return True
    
    print(f"📦 Creating virtual environment '{venv_name}'...")
    try:
        subprocess.check_call([sys.executable, "-m", "venv", venv_name])
        print(f"✅ Virtual environment '{venv_name}' created successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating virtual environment: {e}")
        return False

def get_activation_command():
    """Get the activation command for the current OS"""
    if platform.system() == "Windows":
        return "venv\\Scripts\\activate"
    else:
        return "source venv/bin/activate"

def get_python_executable():
    """Get the Python executable path in venv"""
    if platform.system() == "Windows":
        return "venv\\Scripts\\python.exe"
    else:
        return "venv/bin/python"

def install_dependencies():
    """Install dependencies in virtual environment"""
    python_exe = get_python_executable()
    
    if not os.path.exists(python_exe):
        print("❌ Virtual environment Python not found")
        return False
    
    print("📦 Installing dependencies in virtual environment...")
    try:
        # Upgrade pip first
        subprocess.check_call([python_exe, "-m", "pip", "install", "--upgrade", "pip"])
        
        # Install setuptools for Python 3.12+ compatibility
        subprocess.check_call([python_exe, "-m", "pip", "install", "--upgrade", "setuptools>=65.0.0"])
        
        # Install project dependencies
        subprocess.check_call([python_exe, "-m", "pip", "install", "-r", "requirements.txt"])
        
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def test_installation():
    """Test if all packages are installed correctly"""
    python_exe = get_python_executable()
    
    print("🧪 Testing installation...")
    test_script = """
import sys
try:
    import streamlit
    import boto3
    import plotly
    import pandas
    import numpy
    print("✅ All packages imported successfully")
    print(f"Python version: {sys.version}")
    sys.exit(0)
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
"""
    
    try:
        result = subprocess.run([python_exe, "-c", test_script], 
                              capture_output=True, text=True, check=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Test failed: {e}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def main():
    """Main setup function"""
    print("=" * 60)
    print("🐍 Vismaya DemandOps - Virtual Environment Setup")
    print("=" * 60)
    
    # Create virtual environment
    if not create_venv():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Test installation
    if not test_installation():
        print("⚠️  Installation test failed, but you can still try running the app")
    
    # Show next steps
    activation_cmd = get_activation_command()
    print("\n" + "=" * 60)
    print("🎉 Virtual Environment Setup Complete!")
    print("=" * 60)
    print("\n🚀 Next Steps:")
    print(f"1. Activate virtual environment:")
    print(f"   {activation_cmd}")
    print("\n2. Configure AWS (if needed):")
    print("   python aws-setup.py")
    print("\n3. Test the application:")
    print("   python local-test.py")
    print("\n4. Run the application:")
    print("   python app.py")
    print("\n📊 Dashboard will be available at: http://localhost:8501")
    print("=" * 60)

if __name__ == "__main__":
    main()