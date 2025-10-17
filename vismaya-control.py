#!/usr/bin/env python3
"""
Vismaya DemandOps - Master Control Script
Central control for all Vismaya operations
"""

import sys
import subprocess
import os
from datetime import datetime

def show_banner():
    """Show Vismaya banner"""
    print("=" * 60)
    print("🎯 Vismaya DemandOps - Master Control")
    print("AI-Powered FinOps Platform for AWS Cost Optimization")
    print("Team MaximAI")
    print("=" * 60)

def show_help():
    """Show help information"""
    print("""
Available Commands:

🚀 STARTUP & DEPLOYMENT:
  start           - Start the application locally
  deploy          - Deploy to AWS (CloudFormation)
  docker          - Run with Docker
  startup-aws     - Start AWS resources
  
🛑 SHUTDOWN & CLEANUP:
  stop            - Quick stop (local processes)
  shutdown        - Full AWS resource shutdown
  cleanup         - Clean up all resources
  
📊 MONITORING & TESTING:
  test            - Test AWS connectivity
  monitor         - Monitor AWS costs
  status          - Show system status
  logs            - Show application logs
  
🔧 SETUP & CONFIGURATION:
  setup           - Setup virtual environment
  setup-aws       - Setup AWS credentials
  config          - Show current configuration
  
📋 INFORMATION:
  help            - Show this help
  version         - Show version information
  
Examples:
  python vismaya-control.py start
  python vismaya-control.py deploy
  python vismaya-control.py shutdown
  python vismaya-control.py monitor
""")

def get_venv_python():
    """Get the Python executable from virtual environment"""
    import platform
    from pathlib import Path
    
    if platform.system() == "Windows":
        venv_python = Path("venv") / "Scripts" / "python.exe"
    else:
        venv_python = Path("venv") / "bin" / "python"
    
    if venv_python.exists():
        return str(venv_python)
    else:
        print("⚠️  Virtual environment not found, using system Python")
        return "python"

def run_command(script_name, args=None):
    """Run a Python script with optional arguments using venv Python"""
    python_exe = get_venv_python()
    cmd = [python_exe, script_name]
    if args:
        cmd.extend(args)
    
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ Script not found: {script_name}")
        return False

def ensure_venv():
    """Ensure virtual environment is set up"""
    from pathlib import Path
    
    venv_path = Path('venv')
    if not venv_path.exists():
        print("📦 Virtual environment not found, creating...")
        try:
            subprocess.check_call([sys.executable, "-m", "venv", "venv"])
            print("✅ Virtual environment created")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create virtual environment: {e}")
            return False
    
    return True

def check_prerequisites():
    """Check if prerequisites are met"""
    issues = []
    
    # Check Python version
    if sys.version_info < (3, 8):
        issues.append("Python 3.8+ required")
    
    # Check if virtual environment exists
    if not os.path.exists('venv'):
        issues.append("Virtual environment not found (run: setup)")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        issues.append("Configuration file .env not found")
    
    return issues

def show_status():
    """Show system status"""
    print("📊 System Status:")
    print("=" * 30)
    
    # Check prerequisites
    issues = check_prerequisites()
    if issues:
        print("⚠️  Issues found:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("✅ Prerequisites met")
    
    # Check if processes are running
    try:
        import psutil
        vismaya_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'vismaya' in cmdline.lower() or 'dashboard.py' in cmdline.lower():
                    vismaya_processes.append(f"PID {proc.info['pid']}: {cmdline[:50]}...")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if vismaya_processes:
            print("🟢 Running processes:")
            for proc in vismaya_processes:
                print(f"   {proc}")
        else:
            print("🔴 No Vismaya processes running")
            
    except ImportError:
        print("⚠️  psutil not available for process checking")
    
    # Check Docker
    try:
        result = subprocess.run(['docker', 'ps', '--filter', 'name=vismaya'], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            print("🐳 Docker containers running")
        else:
            print("🔴 No Docker containers running")
    except FileNotFoundError:
        print("⚠️  Docker not available")
    
    print("=" * 30)

def main():
    show_banner()
    
    if len(sys.argv) < 2:
        print("Use 'python vismaya-control.py help' for available commands")
        return
    
    command = sys.argv[1].lower()
    args = sys.argv[2:] if len(sys.argv) > 2 else []
    
    # Handle commands
    if command == 'help':
        show_help()
        
    elif command == 'start':
        print("🚀 Starting Vismaya DemandOps locally...")
        if not ensure_venv():
            print("❌ Virtual environment setup failed")
            return
        print("   Using smart startup script...")
        run_command('start-vismaya.py')
        
    elif command == 'deploy':
        print("☁️  Deploying to AWS...")
        if os.name == 'nt':  # Windows
            subprocess.run(['deploy.sh'], shell=True)
        else:
            subprocess.run(['./deploy.sh'])
            
    elif command == 'docker':
        print("🐳 Starting with Docker...")
        if os.name == 'nt':  # Windows
            subprocess.run(['deploy\\docker-deploy.sh', 'compose'], shell=True)
        else:
            subprocess.run(['./deploy/docker-deploy.sh', 'compose'])
            
    elif command == 'startup-aws':
        print("☁️  Starting AWS resources...")
        run_command('startup-aws.py')
        
    elif command == 'stop':
        print("🛑 Quick stop...")
        run_command('quick-stop.py')
        
    elif command == 'shutdown':
        print("🛑 Full AWS shutdown...")
        run_command('shutdown-aws.py')
        
    elif command == 'cleanup':
        print("🧹 Cleaning up...")
        run_command('quick-stop.py')
        run_command('shutdown-aws.py')
        
    elif command == 'test':
        print("🧪 Testing AWS connectivity...")
        run_command('test-aws-connection.py')
        
    elif command == 'monitor':
        print("📊 Monitoring costs...")
        monitor_args = ['report'] if not args else args
        run_command('cost-monitor.py', monitor_args)
        
    elif command == 'status':
        show_status()
        
    elif command == 'logs':
        print("📋 Showing logs...")
        # Try to show Docker logs
        try:
            subprocess.run(['docker-compose', 'logs', '--tail', '50'])
        except:
            print("No Docker logs available")
            
    elif command == 'setup':
        print("🔧 Setting up virtual environment...")
        run_command('setup-venv.py')
        
    elif command == 'setup-aws':
        print("🔐 Setting up AWS credentials...")
        run_command('setup-aws-local.py')
        
    elif command == 'config':
        print("⚙️  Current configuration:")
        try:
            from config import Config
            print(f"   AWS Region: {Config.AWS_REGION}")
            print(f"   Environment: {Config.ENVIRONMENT}")
            print(f"   Port: {Config.PORT}")
            print(f"   Budget: ${Config.DEFAULT_BUDGET}")
            print(f"   Using SSO: {Config.use_sso()}")
        except Exception as e:
            print(f"   Error loading config: {e}")
            
    elif command == 'version':
        print("📋 Version Information:")
        print("   Vismaya DemandOps v1.0.0")
        print("   AI-Powered FinOps Platform for AWS Cost Optimization")
        print("   Team MaximAI")
        print(f"   Python: {sys.version}")
        
    else:
        print(f"❌ Unknown command: {command}")
        print("Use 'python vismaya-control.py help' for available commands")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)