#!/usr/bin/env python3
"""
Vismaya - DemandOps
AI-Powered FinOps Platform for AWS Cost Optimization
Team MaximAI

Main application entry point
"""

import subprocess
import sys
import os
import logging
import asyncio
import socket
from config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def install_requirements():
    """Install required packages with better error handling"""
    try:
        # First try to install setuptools if missing
        try:
            import setuptools
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "setuptools>=65.0.0"])
        
        # Install requirements
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "--upgrade", "--no-cache-dir", "-r", "requirements.txt"
        ])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        print("🔧 Please run: python setup.py")
        return False

def setup_environment():
    """Setup environment variables"""
    os.environ['AWS_REGION'] = Config.AWS_REGION
    
    if not Config.use_sso():
        # Only set explicit credentials if they exist
        if Config.AWS_ACCESS_KEY_ID:
            os.environ['AWS_ACCESS_KEY_ID'] = Config.AWS_ACCESS_KEY_ID
        if Config.AWS_SECRET_ACCESS_KEY:
            os.environ['AWS_SECRET_ACCESS_KEY'] = Config.AWS_SECRET_ACCESS_KEY
        if Config.AWS_SESSION_TOKEN:
            os.environ['AWS_SESSION_TOKEN'] = Config.AWS_SESSION_TOKEN
        print("✅ AWS explicit credentials configured")
    else:
        print(f"✅ AWS SSO/Profile authentication configured (Profile: {Config.AWS_PROFILE})")

def check_aws_auth():
    """Check AWS authentication"""
    try:
        from src.application.dependency_injection import DependencyContainer
        
        # Test the dependency container
        container = DependencyContainer(Config)
        health_status = asyncio.run(container.health_check())
        
        if health_status.get('authentication', False):
            print("✅ AWS Authentication successful")
            return True
        else:
            print("⚠️  AWS Authentication warning")
            print("📝 The app will use mock data for demonstration")
            return False
            
    except Exception as e:
        print(f"⚠️  AWS Authentication warning: {e}")
        print("📝 The app will use mock data for demonstration")
        return False

def stop_existing_processes():
    """Stop any existing Vismaya processes"""
    try:
        import psutil
        stopped_processes = []
        
        print("🔍 Checking for existing Vismaya processes...")
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if ('streamlit' in cmdline.lower() and 'dashboard.py' in cmdline.lower()) or \
                       ('vismaya' in cmdline.lower() and 'dashboard.py' in cmdline.lower()):
                        print(f"   🛑 Stopping existing process: PID {proc.info['pid']}")
                        proc.terminate()
                        stopped_processes.append(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        if stopped_processes:
            print(f"   ⏳ Waiting for {len(stopped_processes)} processes to stop...")
            # Wait for processes to terminate
            import time
            time.sleep(2)
            
            # Force kill if still running
            for pid in stopped_processes:
                try:
                    proc = psutil.Process(pid)
                    if proc.is_running():
                        proc.kill()
                        print(f"   💀 Force killed process: PID {pid}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            print("✅ Existing processes stopped")
        else:
            print("   ℹ️  No existing Vismaya processes found")
            
    except ImportError:
        print("⚠️  psutil not available, trying alternative method...")
        try:
            # Try to kill processes using port
            if os.name == 'nt':  # Windows
                subprocess.run([
                    'netstat', '-ano', '|', 'findstr', f':{Config.PORT}', '|', 
                    'for', '/f', 'tokens=5', '%a', 'in', "('more')", 'do', 'taskkill', '/PID', '%a', '/F'
                ], shell=True, capture_output=True)
            else:  # Unix/Linux/Mac
                subprocess.run([
                    'lsof', '-ti', f':{Config.PORT}', '|', 'xargs', 'kill', '-9'
                ], shell=True, capture_output=True)
        except Exception:
            pass
    except Exception as e:
        print(f"⚠️  Error stopping existing processes: {e}")

def check_port_availability():
    """Check if the port is available"""
    import socket
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', Config.PORT))
            return True
    except OSError:
        return False

def run_dashboard():
    """Run the Streamlit dashboard"""
    try:
        # Stop existing processes first
        stop_existing_processes()
        
        # Check port availability
        if not check_port_availability():
            print(f"⚠️  Port {Config.PORT} is still in use, trying to free it...")
            import time
            time.sleep(3)
            
            if not check_port_availability():
                print(f"❌ Port {Config.PORT} is still occupied. Trying alternative port...")
                # Try next available port
                for port in range(Config.PORT + 1, Config.PORT + 10):
                    try:
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                            s.bind(('localhost', port))
                            Config.PORT = port
                            print(f"✅ Using alternative port: {port}")
                            break
                    except OSError:
                        continue
                else:
                    print("❌ No available ports found")
                    return
        
        print("🚀 Starting Vismaya DemandOps Dashboard...")
        print(f"📊 Dashboard will be available at: http://localhost:{Config.PORT}")
        print("💡 Press Ctrl+C to stop the application")
        
        # Add a small delay to ensure port is free
        import time
        time.sleep(1)
        
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "dashboard.py",
            "--server.port", str(Config.PORT),
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Vismaya DemandOps stopped")
    except Exception as e:
        print(f"❌ Error running dashboard: {e}")

def check_virtual_environment():
    """Check if virtual environment is activated"""
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if not in_venv:
        print("⚠️  Virtual environment not detected!")
        print("🔧 Please activate the virtual environment first:")
        
        if os.name == 'nt':  # Windows
            print("   venv\\Scripts\\activate")
        else:  # Unix/Linux/Mac
            print("   source venv/bin/activate")
        
        print("\nOr use the startup script:")
        print("   python vismaya-control.py start")
        
        return False
    
    print(f"✅ Virtual environment active: {sys.prefix}")
    return True

def ensure_dependencies():
    """Ensure all dependencies are installed in the virtual environment"""
    try:
        import streamlit
        import boto3
        import plotly
        import psutil
        print("✅ All core dependencies available")
        return True
    except ImportError as e:
        print(f"📦 Missing dependency: {e}")
        print("🔧 Installing missing dependencies...")
        
        if not install_requirements():
            print("❌ Dependency installation failed")
            print("🔧 Please run: python setup.py")
            return False
        
        return True

def main():
    """Main application entry point"""
    print("=" * 50)
    print("🎯 Vismaya - DemandOps")
    print("AI-Powered FinOps Platform for AWS Cost Optimization")
    print("Team MaximAI")
    print(f"🌍 Environment: {Config.ENVIRONMENT}")
    print(f"🔧 AWS Region: {Config.AWS_REGION}")
    print("=" * 50)
    
    # Check virtual environment first
    if not check_virtual_environment():
        sys.exit(1)
    
    # Setup environment
    setup_environment()
    
    # Ensure dependencies are available
    if not ensure_dependencies():
        sys.exit(1)
    
    # Check AWS authentication
    check_aws_auth()
    
    # Run dashboard
    run_dashboard()

if __name__ == "__main__":
    main()