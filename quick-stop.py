#!/usr/bin/env python3
"""
Quick Stop Script for Vismaya DemandOps
Immediately stops local processes and optionally AWS resources
"""

import os
import sys
import signal
import subprocess
import psutil
from datetime import datetime

def stop_local_processes():
    """Stop local Streamlit and Python processes"""
    print("🛑 Stopping local processes...")
    
    stopped_processes = []
    
    # Find and kill Streamlit processes
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'streamlit' in cmdline.lower() or 'dashboard.py' in cmdline.lower() or 'app.py' in cmdline.lower():
                    print(f"   Stopping process: {proc.info['pid']} - {cmdline[:60]}...")
                    proc.terminate()
                    stopped_processes.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    # Wait for processes to terminate
    if stopped_processes:
        print(f"   Waiting for {len(stopped_processes)} processes to stop...")
        psutil.wait_procs([psutil.Process(pid) for pid in stopped_processes], timeout=10)
        print("✅ Local processes stopped")
    else:
        print("   No Vismaya processes found running")

def stop_docker_containers():
    """Stop Docker containers"""
    print("\n🐳 Stopping Docker containers...")
    
    try:
        # Stop docker-compose services
        result = subprocess.run(['docker-compose', 'down'], 
                              capture_output=True, text=True, cwd='.')
        if result.returncode == 0:
            print("✅ Docker Compose services stopped")
        else:
            print("   No Docker Compose services running")
        
        # Stop individual containers
        result = subprocess.run(['docker', 'ps', '--filter', 'name=vismaya', '--format', '{{.Names}}'], 
                              capture_output=True, text=True)
        
        if result.stdout.strip():
            containers = result.stdout.strip().split('\n')
            for container in containers:
                subprocess.run(['docker', 'stop', container], capture_output=True)
                print(f"✅ Stopped container: {container}")
        else:
            print("   No Vismaya containers running")
            
    except FileNotFoundError:
        print("   Docker not found, skipping container cleanup")
    except Exception as e:
        print(f"   Error stopping containers: {e}")

def cleanup_ports():
    """Clean up used ports"""
    print("\n🔌 Cleaning up ports...")
    
    ports_to_check = [8501, 8502, 8503]
    
    for port in ports_to_check:
        try:
            # Find processes using the port
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    for conn in proc.connections():
                        if conn.laddr.port == port:
                            print(f"   Stopping process on port {port}: {proc.info['pid']}")
                            proc.terminate()
                            break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            print(f"   Error cleaning port {port}: {e}")
    
    print("✅ Port cleanup completed")

def quick_aws_stop():
    """Quick AWS resource stop (EC2 instances only)"""
    print("\n☁️  Quick AWS stop (EC2 instances only)...")
    
    try:
        import boto3
        from config import Config
        
        # Create session
        if Config.use_sso():
            session = boto3.Session(
                profile_name=Config.AWS_PROFILE,
                region_name=Config.AWS_REGION
            )
        else:
            session = boto3.Session(
                aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
                aws_session_token=Config.AWS_SESSION_TOKEN,
                region_name=Config.AWS_REGION
            )
        
        ec2 = session.client('ec2')
        
        # Get running instances
        response = ec2.describe_instances(
            Filters=[
                {'Name': 'instance-state-name', 'Values': ['running']},
                {'Name': 'tag:Project', 'Values': ['VismayaDemandOps', 'vismaya*']}
            ]
        )
        
        instance_ids = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_ids.append(instance['InstanceId'])
        
        if instance_ids:
            ec2.stop_instances(InstanceIds=instance_ids)
            print(f"✅ Stopping {len(instance_ids)} EC2 instances")
            print("   For complete AWS cleanup, run: python shutdown-aws.py")
        else:
            print("   No running Vismaya EC2 instances found")
            
    except Exception as e:
        print(f"   Could not stop AWS resources: {e}")
        print("   Run 'python shutdown-aws.py' for complete AWS cleanup")

def save_stop_log():
    """Save stop log"""
    log_file = f"quick_stop_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(log_file, 'w') as f:
        f.write(f"Quick stop executed at: {datetime.now().isoformat()}\n")
        f.write("Local processes and containers stopped\n")
        f.write("For AWS resources, run: python shutdown-aws.py\n")
    
    print(f"\n📝 Stop log saved to: {log_file}")

def main():
    # Check if called with --silent flag for automated stopping
    silent_mode = len(sys.argv) > 1 and '--silent' in sys.argv
    
    if not silent_mode:
        print("=" * 50)
        print("🛑 Vismaya DemandOps - Quick Stop")
        print("Team MaximAI - AI-Powered FinOps Platform")
        print("=" * 50)
    
    # Stop local processes
    stop_local_processes()
    
    # Stop Docker containers
    stop_docker_containers()
    
    # Clean up ports
    cleanup_ports()
    
    if not silent_mode:
        # Ask about AWS resources
        print("\n" + "=" * 50)
        aws_choice = input("Stop AWS EC2 instances too? (y/n): ").lower().strip()
        
        if aws_choice == 'y':
            quick_aws_stop()
        else:
            print("⚠️  AWS resources not stopped. Run 'python shutdown-aws.py' to stop all AWS resources.")
        
        # Save log
        save_stop_log()
        
        print("\n" + "=" * 50)
        print("✅ Quick stop completed!")
        print("=" * 50)
        print("🚀 To restart:")
        print("   Local: python app.py")
        print("   AWS: python startup-aws.py")
        print("=" * 50)
    else:
        print("✅ Existing processes stopped")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Quick stop cancelled")
    except Exception as e:
        print(f"\n❌ Quick stop failed: {e}")
        sys.exit(1)