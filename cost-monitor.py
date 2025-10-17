#!/usr/bin/env python3
"""
Cost Monitor for Vismaya DemandOps
Monitors AWS costs and provides alerts
"""

import boto3
import json
import time
from datetime import datetime, timedelta
from config import Config

class CostMonitor:
    def __init__(self):
        self.session = self._create_session()
        self.ce = self.session.client('ce')
        self.cloudwatch = self.session.client('cloudwatch')
        
    def _create_session(self):
        """Create AWS session"""
        if Config.use_sso():
            return boto3.Session(
                profile_name=Config.AWS_PROFILE,
                region_name=Config.AWS_REGION
            )
        else:
            return boto3.Session(
                aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
                aws_session_token=Config.AWS_SESSION_TOKEN,
                region_name=Config.AWS_REGION
            )
    
    def get_current_costs(self):
        """Get current month costs"""
        try:
            now = datetime.now()
            start_date = now.replace(day=1).strftime('%Y-%m-%d')
            end_date = now.strftime('%Y-%m-%d')
            
            response = self.ce.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost']
            )
            
            if response['ResultsByTime']:
                amount = float(response['ResultsByTime'][0]['Total']['BlendedCost']['Amount'])
                return amount
            return 0.0
            
        except Exception as e:
            print(f"Error getting costs: {e}")
            return 0.0
    
    def get_daily_costs(self, days=7):
        """Get daily costs for the past N days"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            response = self.ce.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['BlendedCost']
            )
            
            daily_costs = []
            for result in response['ResultsByTime']:
                date = result['TimePeriod']['Start']
                amount = float(result['Total']['BlendedCost']['Amount'])
                daily_costs.append({'date': date, 'amount': amount})
            
            return daily_costs
            
        except Exception as e:
            print(f"Error getting daily costs: {e}")
            return []
    
    def get_service_costs(self):
        """Get costs by service"""
        try:
            now = datetime.now()
            start_date = now.replace(day=1).strftime('%Y-%m-%d')
            end_date = now.strftime('%Y-%m-%d')
            
            response = self.ce.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ]
            )
            
            service_costs = []
            if response['ResultsByTime'] and response['ResultsByTime'][0]['Groups']:
                for group in response['ResultsByTime'][0]['Groups']:
                    service = group['Keys'][0]
                    amount = float(group['Metrics']['BlendedCost']['Amount'])
                    if amount > 0:
                        service_costs.append({'service': service, 'amount': amount})
            
            return sorted(service_costs, key=lambda x: x['amount'], reverse=True)
            
        except Exception as e:
            print(f"Error getting service costs: {e}")
            return []
    
    def check_budget_alerts(self, budget_limit=50.0):
        """Check if costs exceed budget thresholds"""
        current_cost = self.get_current_costs()
        
        alerts = []
        
        # Check various thresholds
        thresholds = [
            (0.5, "50% of budget"),
            (0.8, "80% of budget"),
            (0.9, "90% of budget"),
            (1.0, "100% of budget - EXCEEDED!")
        ]
        
        for threshold, message in thresholds:
            if current_cost >= budget_limit * threshold:
                alerts.append({
                    'level': 'WARNING' if threshold < 1.0 else 'CRITICAL',
                    'message': f"Cost alert: ${current_cost:.2f} - {message}",
                    'threshold': threshold,
                    'current_cost': current_cost,
                    'budget_limit': budget_limit
                })
        
        return alerts
    
    def estimate_monthly_cost(self):
        """Estimate end-of-month cost based on current trend"""
        daily_costs = self.get_daily_costs(7)
        
        if not daily_costs:
            return 0.0
        
        # Calculate average daily cost
        total_cost = sum(day['amount'] for day in daily_costs)
        avg_daily_cost = total_cost / len(daily_costs)
        
        # Estimate monthly cost
        now = datetime.now()
        days_in_month = (now.replace(month=now.month+1, day=1) - timedelta(days=1)).day
        estimated_monthly = avg_daily_cost * days_in_month
        
        return estimated_monthly
    
    def generate_cost_report(self):
        """Generate comprehensive cost report"""
        print("=" * 60)
        print("💰 Vismaya DemandOps - Cost Report")
    print("Team MaximAI - AI-Powered FinOps Platform")
        print("=" * 60)
        print(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Current costs
        current_cost = self.get_current_costs()
        print(f"\n📊 Current Month Cost: ${current_cost:.2f}")
        
        # Estimated monthly cost
        estimated_cost = self.estimate_monthly_cost()
        print(f"📈 Estimated Monthly Cost: ${estimated_cost:.2f}")
        
        # Service breakdown
        service_costs = self.get_service_costs()
        if service_costs:
            print(f"\n🔧 Top Services by Cost:")
            for i, service in enumerate(service_costs[:5]):
                print(f"   {i+1}. {service['service']}: ${service['amount']:.2f}")
        
        # Budget alerts
        budget_alerts = self.check_budget_alerts(Config.DEFAULT_BUDGET)
        if budget_alerts:
            print(f"\n⚠️  Budget Alerts:")
            for alert in budget_alerts:
                print(f"   {alert['level']}: {alert['message']}")
        else:
            print(f"\n✅ No budget alerts (Budget: ${Config.DEFAULT_BUDGET})")
        
        # Daily trend
        daily_costs = self.get_daily_costs(7)
        if daily_costs:
            print(f"\n📅 Daily Costs (Last 7 days):")
            for day in daily_costs[-7:]:
                print(f"   {day['date']}: ${day['amount']:.2f}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if current_cost > Config.DEFAULT_BUDGET * 0.8:
            print("   🛑 Consider running 'python shutdown-aws.py' to stop resources")
        if estimated_cost > Config.DEFAULT_BUDGET:
            print("   ⚠️  Projected to exceed monthly budget")
        if current_cost < 1.0:
            print("   ✅ Costs are minimal - good for testing")
        
        print("=" * 60)
        
        return {
            'current_cost': current_cost,
            'estimated_cost': estimated_cost,
            'service_costs': service_costs,
            'budget_alerts': budget_alerts,
            'daily_costs': daily_costs
        }
    
    def continuous_monitor(self, check_interval=300):  # 5 minutes
        """Continuously monitor costs"""
        print("🔄 Starting continuous cost monitoring...")
        print(f"   Check interval: {check_interval} seconds")
        print("   Press Ctrl+C to stop")
        
        try:
            while True:
                current_cost = self.get_current_costs()
                alerts = self.check_budget_alerts(Config.DEFAULT_BUDGET)
                
                timestamp = datetime.now().strftime('%H:%M:%S')
                print(f"[{timestamp}] Current cost: ${current_cost:.2f}")
                
                for alert in alerts:
                    if alert['level'] == 'CRITICAL':
                        print(f"🚨 CRITICAL: {alert['message']}")
                    elif alert['level'] == 'WARNING':
                        print(f"⚠️  WARNING: {alert['message']}")
                
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Cost monitoring stopped")

def main():
    import sys
    
    monitor = CostMonitor()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'report':
            monitor.generate_cost_report()
        elif command == 'monitor':
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 300
            monitor.continuous_monitor(interval)
        elif command == 'current':
            cost = monitor.get_current_costs()
            print(f"Current month cost: ${cost:.2f}")
        elif command == 'alerts':
            alerts = monitor.check_budget_alerts(Config.DEFAULT_BUDGET)
            if alerts:
                for alert in alerts:
                    print(f"{alert['level']}: {alert['message']}")
            else:
                print("No budget alerts")
        else:
            print("Usage: python cost-monitor.py [report|monitor|current|alerts]")
    else:
        # Default: generate report
        monitor.generate_cost_report()

if __name__ == "__main__":
    main()