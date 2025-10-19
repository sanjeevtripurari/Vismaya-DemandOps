#!/usr/bin/env python3
"""
Vismaya DemandOps - Virtual Environment Manager
Comprehensive virtual environment management for all Python operations
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

class VenvManager:
    def __init__(self):
        self.venv_path = Path('venv')
        self.is_windows = platform.system() == "Windows"
        self.python_exe = self._get_python_exe()
        self.pip_exe = self._get_pip_exe()
        self.activate_script = self._get_activate_script()
    
    def _get_python_exe(self):
        """Get Python executable path in venv"""
        if self.is_windows:
            return self.venv_path / "Scripts" / "python.exe"
        else:
            return self.venv_path / "bin" / "python"
    
    def _get_pip_exe(self):
        """Get pip executable path in venv"""
        if self.is_windows:
            return self.venv_path / "Scripts" / "pip.exe"
        else:
            return self.venv_path / "bin" / "pip"
    
    def _get_activate_script(self):
        """Get activation script path"""
        if self.is_windows:
            return self.venv_path / "Scripts" / "activate.bat"
        else:
            return self.venv_path / "bin" / "activate"
    
    def check_venv_exists(self):
        """Check if virtual environment exists and is valid"""
        if not self.venv_path.exists():
            return False
        
        if not self.python_exe.exists():
            return False
        
        # Test if venv is functional
        try:
            result = subprocess.run([str(self.python_exe), "--version"], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except Exception:
            return False
    
    def create_venv(self):
        """Create virtual environment"""
        print("📦 Creating virtual environment...")
        
        # Remove existing broken venv
        if self.venv_path.exists():
            print("🗑️  Removing existing virtual environment...")
            shutil.rmtree(self.venv_path)
        
        try:
            subprocess.check_call([sys.executable, "-m", "venv", str(self.venv_path)])
            print("✅ Virtual environment created successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error creating virtual environment: {e}")
            return False
    
    def upgrade_pip(self):
        """Upgrade pip in virtual environment"""
        print("⬆️  Upgrading pip...")
        try:
            subprocess.check_call([str(self.python_exe), "-m", "pip", "install", "--upgrade", "pip"])
            print("✅ Pip upgraded successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error upgrading pip: {e}")
            return False
    
    def install_setuptools(self):
        """Install/upgrade setuptools for Python 3.12+ compatibility"""
        print("📦 Installing setuptools...")
        try:
            subprocess.check_call([str(self.python_exe), "-m", "pip", "install", "--upgrade", "setuptools>=65.0.0"])
            print("✅ Setuptools installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error installing setuptools: {e}")
            return False
    
    def install_requirements(self):
        """Install project requirements"""
        requirements_file = Path("requirements.txt")
        
        if not requirements_file.exists():
            print("⚠️  requirements.txt not found, creating basic requirements...")
            self.create_basic_requirements()
        
        print("📦 Installing project requirements...")
        try:
            subprocess.check_call([str(self.python_exe), "-m", "pip", "install", "-r", "requirements.txt"])
            print("✅ Requirements installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error installing requirements: {e}")
            return False
    
    def create_basic_requirements(self):
        """Create basic requirements.txt if it doesn't exist"""
        basic_requirements = """streamlit>=1.28.0
boto3>=1.26.0
pandas>=1.5.0
plotly>=5.0.0
python-dotenv>=0.19.0
requests>=2.28.0
numpy>=1.21.0
altair>=4.0.0
psutil>=5.8.0
"""
        with open("requirements.txt", "w") as f:
            f.write(basic_requirements)
        print("✅ Basic requirements.txt created")
    
    def test_installation(self):
        """Test if all packages are installed correctly"""
        print("🧪 Testing installation...")
        
        test_script = """
import sys
try:
    import streamlit
    import boto3
    import plotly
    import pandas
    import numpy
    import psutil
    print("✅ All core packages imported successfully")
    print(f"Python: {sys.version}")
    print(f"Streamlit: {streamlit.__version__}")
    print(f"Boto3: {boto3.__version__}")
    sys.exit(0)
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
"""
        
        try:
            result = subprocess.run([str(self.python_exe), "-c", test_script], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(result.stdout)
                return True
            else:
                print(f"❌ Test failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            return False
    
    def run_in_venv(self, script_name, args=None):
        """Run a Python script in the virtual environment"""
        if not self.check_venv_exists():
            print("❌ Virtual environment not available")
            return False
        
        cmd = [str(self.python_exe), script_name]
        if args:
            cmd.extend(args)
        
        try:
            subprocess.run(cmd)
            return True
        except Exception as e:
            print(f"❌ Error running {script_name}: {e}")
            return False
    
    def get_activation_command(self):
        """Get the command to activate virtual environment"""
        if self.is_windows:
            return f"venv\\Scripts\\activate"
        else:
            return f"source venv/bin/activate"
    
    def setup_complete_environment(self):
        """Complete environment setup"""
        print("=" * 60)
        print("🐍 Vismaya DemandOps - Virtual Environment Setup")
        print("=" * 60)
        
        # Check/create virtual environment
        if not self.check_venv_exists():
            if not self.create_venv():
                return False
        else:
            print("✅ Virtual environment already exists")
        
        # Upgrade pip
        if not self.upgrade_pip():
            print("⚠️  Pip upgrade failed, continuing...")
        
        # Install setuptools
        if not self.install_setuptools():
            print("⚠️  Setuptools installation failed, continuing...")
        
        # Install requirements
        if not self.install_requirements():
            print("⚠️  Requirements installation failed")
            return False
        
        # Test installation
        if not self.test_installation():
            print("⚠️  Installation test failed, but environment may still work")
        
        print("\n" + "=" * 60)
        print("🎉 Virtual Environment Setup Complete!")
        print("=" * 60)
        print(f"\n🔧 To activate manually: {self.get_activation_command()}")
        print("🚀 To start application: python start-vismaya.py")
        print("📊 Dashboard URL: http://localhost:8503")
        print("=" * 60)
        
        return True

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Vismaya Virtual Environment Manager")
    parser.add_argument("action", choices=["setup", "test", "run"], 
                       help="Action to perform")
    parser.add_argument("--script", help="Script to run (for 'run' action)")
    parser.add_argument("--args", nargs="*", help="Arguments for script")
    
    args = parser.parse_args()
    
    manager = VenvManager()
    
    if args.action == "setup":
        success = manager.setup_complete_environment()
        sys.exit(0 if success else 1)
    
    elif args.action == "test":
        if manager.check_venv_exists():
            success = manager.test_installation()
            sys.exit(0 if success else 1)
        else:
            print("❌ Virtual environment not found. Run 'python venv-manager.py setup' first.")
            sys.exit(1)
    
    elif args.action == "run":
        if not args.script:
            print("❌ --script argument required for 'run' action")
            sys.exit(1)
        
        success = manager.run_in_venv(args.script, args.args)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()