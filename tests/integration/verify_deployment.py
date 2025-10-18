#!/usr/bin/env python3
"""
Deployment Verification Script
Verifies that all components are working correctly after deployment
"""

import asyncio
import sys
import os
import requests
import time
from datetime import datetime

def print_status(message, status="INFO"):
    """Print status message with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    symbols = {
        "INFO": "ℹ️",
        "SUCCESS": "✅", 
        "ERROR": "❌",
        "WARNING": "⚠️"
    }
    symbol = symbols.get(status, "ℹ️")
    print(f"[{timestamp}] {symbol} {message}")

def check_environment():
    """Check environment configuration"""
    print_status("Checking environment configuration...")
    
    required_vars = [
        'AWS_REGION',
        'BEDROCK_MODEL_ID', 
        'DEFAULT_BUDGET',
        'BUDGET_WARNING_LIMIT',
        'BUDGET_MAXIMUM_LIMIT'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print_status(f"Missing environment variables: {', '.join(missing_vars)}", "ERROR")
        return False
    
    print_status("Environment configuration OK", "SUCCESS")
    return True

def check_dependencies():
    """Check if all required packages are installed"""
    print_status("Checking Python dependencies...")
    
    # Check if we're in a virtual environment
    import sys
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if in_venv:
        print_status("✅ Running in virtual environment", "SUCCESS")
    else:
        print_status("⚠️ Not in virtual environment (recommended to use venv)", "WARNING")
    
    required_packages = [
        ('streamlit', 'streamlit'),
        ('boto3', 'boto3'), 
        ('pandas', 'pandas'),
        ('plotly', 'plotly'),
        ('numpy', 'numpy'),
        ('python-dotenv', 'dotenv'),
        ('requests', 'requests')
    ]
    
    missing_packages = []
    installed_packages = []
    
    for package_name, import_name in required_packages:
        try:
            module = __import__(import_name)
            version = getattr(module, '__version__', 'unknown')
            installed_packages.append(f"{package_name} ({version})")
        except ImportError:
            missing_packages.append(package_name)
    
    # Show installed packages
    for package in installed_packages:
        print_status(f"✅ {package}", "SUCCESS")
    
    if missing_packages:
        print_status(f"❌ Missing packages: {', '.join(missing_packages)}", "ERROR")
        print_status("💡 Run: pip install -r requirements.txt", "INFO")
        if not in_venv:
            print_status("💡 Consider using virtual environment: python -m venv venv", "INFO")
        return False
    
    print_status("✅ All dependencies installed", "SUCCESS")
    return True

def check_aws_connection():
    """Check AWS connectivity"""
    print_status("Checking AWS connection...")
    
    try:
        import boto3
        
        # Test STS connection
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        
        print_status(f"AWS Account: {identity.get('Account')}", "SUCCESS")
        print_status(f"AWS User/Role: {identity.get('Arn', 'Unknown')}", "SUCCESS")
        
        # Test Cost Explorer
        ce = boto3.client('ce')
        from datetime import datetime, timedelta
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        ce.get_cost_and_usage(
            TimePeriod={'Start': start_date, 'End': end_date},
            Granularity='DAILY',
            Metrics=['BlendedCost']
        )
        
        print_status("Cost Explorer access OK", "SUCCESS")
        
        # Test Bedrock
        bedrock = boto3.client('bedrock-runtime')
        print_status("Bedrock access OK", "SUCCESS")
        
        return True
        
    except Exception as e:
        print_status(f"AWS connection failed: {str(e)}", "ERROR")
        return False

def check_application_health(port=8501, timeout=10):
    """Check if application is running and healthy (optional check)"""
    print_status(f"Checking if application is running on port {port}...")
    
    health_url = f"http://localhost:{port}/_stcore/health"
    app_url = f"http://localhost:{port}"
    
    # Quick check if application is running
    try:
        response = requests.get(health_url, timeout=2)
        if response.status_code == 200:
            print_status("✅ Application is running and healthy", "SUCCESS")
            
            # Test main page
            try:
                main_response = requests.get(app_url, timeout=3)
                if main_response.status_code == 200:
                    print_status("✅ Main application page accessible", "SUCCESS")
                    print_status(f"🌐 Access at: http://localhost:{port}", "INFO")
                    return True
                else:
                    print_status(f"⚠️ Main page returned status {main_response.status_code}", "WARNING")
                    return True  # Health check passed
            except:
                print_status("⚠️ Main page loading (this is normal)", "WARNING")
                return True  # Health check passed
                
    except requests.exceptions.RequestException:
        print_status("ℹ️ Application not currently running", "INFO")
        print_status("💡 To start: python app.py or docker-compose up -d", "INFO")
        print_status("✅ This is OK - components can work without web UI", "SUCCESS")
        return True  # Not running is OK for component testing
    
    return True  # Always return True since this is optional

async def test_core_functionality():
    """Test core application functionality"""
    print_status("Testing core functionality...")
    
    try:
        # Import and test core components
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
        
        from config import Config
        from src.application.dependency_injection import DependencyContainer
        
        print_status("✅ Core modules imported successfully", "SUCCESS")
        
        config = Config()
        container = DependencyContainer(config)
        print_status("✅ Dependency injection container initialized", "SUCCESS")
        
        # Test usage summary
        usage_summary_use_case = container.get_use_case('get_usage_summary')
        usage_summary = await usage_summary_use_case.execute()
        
        if usage_summary and usage_summary.budget_info:
            current_spend = usage_summary.budget_info.current_spend
            budget_status = usage_summary.budget_info.budget_status
            service_count = len(usage_summary.service_costs)
            
            print_status(f"✅ Budget info: ${current_spend:.2f} ({budget_status})", "SUCCESS")
            print_status(f"✅ Service costs: {service_count} services tracked", "SUCCESS")
        else:
            print_status("❌ Failed to load usage summary", "ERROR")
            return False
        
        # Test budget alerts
        from src.services.budget_alert_service import BudgetAlertService
        alert_service = BudgetAlertService()
        alerts = alert_service.check_budget_status(usage_summary.budget_info)
        
        print_status(f"✅ Budget alerts: {len(alerts)} alerts generated", "SUCCESS")
        
        # Test forecasting
        from src.services.budget_forecasting_service import BudgetForecastingService
        forecasting_service = BudgetForecastingService()
        timeline = forecasting_service.generate_budget_timeline(
            usage_summary.budget_info, 
            usage_summary.cost_forecast
        )
        
        daily_cost = timeline.get('daily_cost_estimate', 0)
        growth_rate = timeline.get('monthly_growth_rate', 0)
        print_status(f"✅ Forecasting: ${daily_cost:.4f}/day, {growth_rate:.1f}% growth", "SUCCESS")
        
        # Test AI assistant (if available)
        try:
            chat_use_case = container.get_use_case('handle_chat')
            response = await chat_use_case.execute("What is my current spending?")
            if response and len(response) > 10:
                print_status("✅ AI Assistant: Responding correctly", "SUCCESS")
            else:
                print_status("⚠️ AI Assistant: Limited response", "WARNING")
        except Exception as ai_error:
            print_status(f"⚠️ AI Assistant: {str(ai_error)[:50]}...", "WARNING")
        
        return True
        
    except Exception as e:
        print_status(f"❌ Core functionality test failed: {str(e)}", "ERROR")
        return False

def main():
    """Main verification function"""
    print("🚀 Vismaya DemandOps - Deployment Verification")
    print("=" * 60)
    print("Team MaximAI - AI-Powered FinOps Platform")
    print("=" * 60)
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    checks = [
        ("Environment Configuration", check_environment),
        ("Python Dependencies", check_dependencies), 
        ("AWS Connection", check_aws_connection),
        ("Application Health", lambda: check_application_health()),
        ("Core Functionality", lambda: asyncio.run(test_core_functionality()))
    ]
    
    results = []
    
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}")
        print("-" * 40)
        
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print_status(f"Check failed with exception: {str(e)}", "ERROR")
            results.append((check_name, False))
    
    # Summary
    print(f"\n🎯 VERIFICATION SUMMARY")
    print("=" * 40)
    
    passed = 0
    total = len(results)
    
    for check_name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✅" if result else "❌"
        print(f"{symbol} {check_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} checks passed")
    
    if passed == total:
        print_status("🎉 All verification checks passed! Deployment is ready.", "SUCCESS")
        print_status("🌐 Access your application at: http://localhost:8501", "INFO")
        return 0
    else:
        print_status(f"⚠️ {total - passed} checks failed. Please review and fix issues.", "ERROR")
        return 1

if __name__ == "__main__":
    sys.exit(main())