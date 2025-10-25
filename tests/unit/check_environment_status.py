#!/usr/bin/env python3
"""
Environment Status Checker for Vismaya DemandOps
Comprehensive health check for AWS environment and application components
"""

import boto3
import sys
import requests
import psutil
from datetime import datetime, timedelta
from config import Config

def print_header():
    """Print status check header"""
    print("=" * 60)
    print("🔍 VISMAYA DEMANDOPS - ENVIRONMENT STATUS CHECK")
    print("=" * 60)
    print(f"🕐 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌍 Region: {Config.AWS_REGION}")
    print(f"🏷️  Environment: {Config.ENVIRONMENT}")
    print("-" * 60)

def check_system_resources():
    """Check local system resources"""
    print("💻 SYSTEM RESOURCES:")
    try:
        # Memory usage
        memory = psutil.virtual_memory()
        print(f"   💾 Memory: {memory.percent:.1f}% used ({memory.used // (1024**3):.1f}GB / {memory.total // (1024**3):.1f}GB)")
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"   🖥️  CPU: {cpu_percent:.1f}% used")
        
        # Disk usage
        disk = psutil.disk_usage('.')
        print(f"   💿 Disk: {disk.percent:.1f}% used ({disk.used // (1024**3):.1f}GB / {disk.total // (1024**3):.1f}GB)")
        
        # System health assessment
        health_issues = []
        if memory.percent > 85:
            health_issues.append("High memory usage")
        if cpu_percent > 80:
            health_issues.append("High CPU usage")
        if disk.percent > 90:
            health_issues.append("Low disk space")
        
        if health_issues:
            print(f"   ⚠️  Issues: {', '.join(health_issues)}")
            return False
        else:
            print("   ✅ System resources: OK")
            return True
            
    except Exception as e:
        print(f"   ❌ System check failed: {e}")
        return False

def check_aws_connectivity():
    """Check AWS service connectivity"""
    print("\n☁️  AWS CONNECTIVITY:")
    
    try:
        # Basic AWS identity check
        sts = boto3.client('sts', region_name=Config.AWS_REGION)
        identity = sts.get_caller_identity()
        
        # Get user display name - prefer email if available
        user_display = getattr(Config, 'AWS_USER_EMAIL', None)
        if not user_display:
            user_display = identity['Arn'].split('/')[-1]
        
        print(f"   ✅ AWS Account: {identity['Account']}")
        print(f"   ✅ User: {user_display}")
        print(f"   ✅ Region: {Config.AWS_REGION}")
        
        aws_services_status = True
        
        # Test Cost Explorer
        try:
            ce = boto3.client('ce', region_name=Config.AWS_REGION)
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=1)
            
            response = ce.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['BlendedCost']
            )
            print("   ✅ Cost Explorer: Accessible")
        except Exception as e:
            print(f"   ❌ Cost Explorer: {str(e)[:50]}...")
            aws_services_status = False
        
        # Test EC2
        try:
            ec2 = boto3.client('ec2', region_name=Config.AWS_REGION)
            instances = ec2.describe_instances()
            instance_count = sum(len(r['Instances']) for r in instances['Reservations'])
            print(f"   ✅ EC2: Accessible ({instance_count} instances)")
        except Exception as e:
            print(f"   ❌ EC2: {str(e)[:50]}...")
            aws_services_status = False
        
        # Test Bedrock
        try:
            bedrock = boto3.client('bedrock-runtime', region_name=Config.AWS_REGION)
            # Try a simple operation to test access
            bedrock_models = boto3.client('bedrock', region_name=Config.AWS_REGION)
            bedrock_models.list_foundation_models()
            print("   ✅ Bedrock: Accessible")
        except Exception as e:
            error_str = str(e)
            if 'AccessDenied' in error_str or 'not authorized' in error_str:
                user_email = getattr(Config, 'AWS_USER_EMAIL', 'user')
                print(f"   ❌ Bedrock: Access denied for {user_email}")
            else:
                print(f"   ❌ Bedrock: {str(e)[:50]}...")
            aws_services_status = False
        
        return aws_services_status
        
    except Exception as e:
        print(f"   ❌ AWS connectivity failed: {e}")
        return False

def check_application_status():
    """Check application status"""
    print("\n🚀 APPLICATION STATUS:")
    
    try:
        # Test if application is running
        ports_to_check = [8501, 8502]  # Common Streamlit ports
        app_running = False
        
        for port in ports_to_check:
            try:
                response = requests.get(f'http://localhost:{port}/_stcore/health', timeout=5)
                if response.status_code == 200:
                    print(f"   ✅ Dashboard: Running on port {port}")
                    app_running = True
                    
                    # Test response time
                    import time
                    start = time.time()
                    requests.get(f'http://localhost:{port}', timeout=10)
                    response_time = (time.time() - start) * 1000
                    
                    if response_time < 3000:
                        print(f"   ✅ Response Time: {response_time:.0f}ms (Good)")
                    else:
                        print(f"   ⚠️  Response Time: {response_time:.0f}ms (Slow)")
                    
                    break
            except:
                continue
        
        if not app_running:
            print("   ❌ Dashboard: Not running")
            return False
        
        # Test application components
        try:
            import sys
            sys.path.append('.')
            from src.application.dependency_injection import DependencyContainer
            
            container = DependencyContainer(Config)
            container.initialize()
            print("   ✅ Dependency Container: Initialized")
            
            # Test use cases
            chat_use_case = container.get_use_case('handle_chat')
            print("   ✅ Chat Use Case: Available")
            
            cost_service = container.get('cost_service')
            print("   ✅ Cost Service: Available")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Application components: {str(e)[:50]}...")
            return False
            
    except Exception as e:
        print(f"   ❌ Application status check failed: {e}")
        return False

def check_configuration():
    """Check configuration status"""
    print("\n⚙️  CONFIGURATION:")
    
    config_issues = []
    
    # Check required environment variables
    required_vars = ['AWS_REGION']
    for var in required_vars:
        value = getattr(Config, var, None)
        if value:
            print(f"   ✅ {var}: {value}")
        else:
            print(f"   ❌ {var}: Not set")
            config_issues.append(var)
    
    # Check optional but important variables
    optional_vars = ['AWS_PROFILE', 'DEFAULT_BUDGET', 'BEDROCK_MODEL_ID']
    for var in optional_vars:
        value = getattr(Config, var, None)
        if value:
            print(f"   ✅ {var}: {value}")
        else:
            print(f"   ⚠️  {var}: Using default")
    
    # Check file existence
    important_files = ['.env', 'requirements.txt', 'dashboard.py']
    for file in important_files:
        try:
            with open(file, 'r'):
                print(f"   ✅ {file}: Exists")
        except FileNotFoundError:
            print(f"   ❌ {file}: Missing")
            config_issues.append(file)
    
    return len(config_issues) == 0

def generate_summary(system_ok, aws_ok, app_ok, config_ok):
    """Generate overall status summary"""
    print("\n" + "=" * 60)
    print("📊 OVERALL STATUS SUMMARY")
    print("=" * 60)
    
    components = [
        ("System Resources", system_ok),
        ("AWS Connectivity", aws_ok),
        ("Application", app_ok),
        ("Configuration", config_ok)
    ]
    
    all_ok = True
    for component, status in components:
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {component}: {'OK' if status else 'ISSUES'}")
        if not status:
            all_ok = False
    
    print("-" * 60)
    if all_ok:
        print("🎉 ENVIRONMENT STATUS: ALL SYSTEMS OPERATIONAL")
        print("🚀 Ready for deployment and operation!")
    else:
        print("⚠️  ENVIRONMENT STATUS: ISSUES DETECTED")
        print("🔧 Please resolve the issues above before proceeding.")
    
    print("=" * 60)
    return all_ok

def main():
    """Main status check function"""
    print_header()
    
    # Run all checks
    system_ok = check_system_resources()
    aws_ok = check_aws_connectivity()
    app_ok = check_application_status()
    config_ok = check_configuration()
    
    # Generate summary
    all_ok = generate_summary(system_ok, aws_ok, app_ok, config_ok)
    
    # Exit with appropriate code
    sys.exit(0 if all_ok else 1)

if __name__ == "__main__":
    main()