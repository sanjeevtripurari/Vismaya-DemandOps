#!/usr/bin/env python3
"""
AWS Resource Startup Script for Vismaya DemandOps
Starts up AWS resources that were previously shut down
"""

import boto3
import json
import time
import sys
import glob
from datetime import datetime
from config import Config

class AWSResourceStartup:
    def __init__(self):
        self.session = self._create_session()
        self.region = Config.AWS_REGION
        self.startup_log = []
        
    def _create_session(self):
        """Create AWS session"""
        try:
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
        except Exception as e:
            print(f"❌ Error creating AWS session: {e}")
            sys.exit(1)
    
    def log_action(self, action, resource_id, status):
        """Log startup actions"""
        self.startup_log.append({
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'resource_id': resource_id,
            'status': status
        })
    
    def load_shutdown_log(self):
        """Load the most recent shutdown log"""
        log_files = glob.glob("shutdown_log_*.json")
        
        if not log_files:
            print("⚠️  No shutdown log found. Will attempt to start all Vismaya resources.")
            return None
        
        # Get the most recent log file
        latest_log = max(log_files)
        print(f"📝 Loading shutdown log: {latest_log}")
        
        try:
            with open(latest_log, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Could not load shutdown log: {e}")
            return None
    
    def start_ec2_instances(self, shutdown_log=None):
        """Start EC2 instances"""
        print("🖥️  Starting EC2 instances...")
        
        try:
            ec2 = self.session.client('ec2')
            
            # Get stopped instances
            response = ec2.describe_instances(
                Filters=[
                    {'Name': 'instance-state-name', 'Values': ['stopped']},
                    {'Name': 'tag:Project', 'Values': ['VismayaDemandOps', 'vismaya*']}
                ]
            )
            
            instance_ids = []
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instance_ids.append(instance['InstanceId'])
                    print(f"   Found stopped instance: {instance['InstanceId']}")
            
            if instance_ids:
                # Start instances
                ec2.start_instances(InstanceIds=instance_ids)
                print(f"✅ Starting {len(instance_ids)} EC2 instances")
                
                for instance_id in instance_ids:
                    self.log_action('start_ec2', instance_id, 'initiated')
                
                # Wait for instances to start
                print("   Waiting for instances to start...")
                waiter = ec2.get_waiter('instance_running')
                waiter.wait(InstanceIds=instance_ids, WaiterConfig={'Delay': 15, 'MaxAttempts': 20})
                print("✅ All instances started successfully")
                
                for instance_id in instance_ids:
                    self.log_action('start_ec2', instance_id, 'completed')
                    
                # Get public IPs
                response = ec2.describe_instances(InstanceIds=instance_ids)
                for reservation in response['Reservations']:
                    for instance in reservation['Instances']:
                        public_ip = instance.get('PublicIpAddress', 'No public IP')
                        print(f"   Instance {instance['InstanceId']}: {public_ip}")
            else:
                print("   No stopped Vismaya instances found")
                
        except Exception as e:
            print(f"❌ Error starting EC2 instances: {e}")
            self.log_action('start_ec2', 'all', f'error: {e}')
    
    def start_rds_instances(self, shutdown_log=None):
        """Start RDS instances"""
        print("\n🗄️  Starting RDS instances...")
        
        try:
            rds = self.session.client('rds')
            
            # Get stopped RDS instances
            response = rds.describe_db_instances()
            
            vismaya_instances = []
            for db in response['DBInstances']:
                # Check if it's a Vismaya-related instance
                if ('vismaya' in db['DBInstanceIdentifier'].lower() or 
                    any(tag.get('Key') == 'Project' and 'vismaya' in tag.get('Value', '').lower() 
                        for tag in db.get('TagList', []))):
                    if db['DBInstanceStatus'] == 'stopped':
                        vismaya_instances.append(db['DBInstanceIdentifier'])
                        print(f"   Found stopped RDS instance: {db['DBInstanceIdentifier']}")
            
            for db_id in vismaya_instances:
                try:
                    rds.start_db_instance(DBInstanceIdentifier=db_id)
                    print(f"✅ Starting RDS instance: {db_id}")
                    self.log_action('start_rds', db_id, 'initiated')
                except Exception as e:
                    print(f"⚠️  Could not start RDS instance {db_id}: {e}")
                    self.log_action('start_rds', db_id, f'error: {e}')
            
            if not vismaya_instances:
                print("   No stopped Vismaya RDS instances found")
                
        except Exception as e:
            print(f"❌ Error starting RDS instances: {e}")
            self.log_action('start_rds', 'all', f'error: {e}')
    
    def deploy_cloudformation_stack(self):
        """Deploy CloudFormation stack"""
        print("\n☁️  Deploying CloudFormation stack...")
        
        try:
            cf = self.session.client('cloudformation')
            
            # Check if stack exists
            try:
                cf.describe_stacks(StackName='vismaya-demandops')
                print("   Stack already exists, skipping deployment")
                return
            except cf.exceptions.ClientError:
                pass  # Stack doesn't exist, continue with deployment
            
            # Deploy stack
            print("   Deploying new stack...")
            print("   Run: ./deploy.sh for full CloudFormation deployment")
            self.log_action('deploy_stack', 'vismaya-demandops', 'manual_required')
            
        except Exception as e:
            print(f"❌ Error with CloudFormation: {e}")
            self.log_action('deploy_stack', 'all', f'error: {e}')
    
    def start_ecs_services(self, shutdown_log=None):
        """Start ECS services"""
        print("\n🐳 Starting ECS services...")
        
        try:
            ecs = self.session.client('ecs')
            
            # List clusters
            clusters_response = ecs.list_clusters()
            
            for cluster_arn in clusters_response['clusterArns']:
                cluster_name = cluster_arn.split('/')[-1]
                
                if 'vismaya' in cluster_name.lower():
                    print(f"   Found cluster: {cluster_name}")
                    
                    # List services in cluster
                    services_response = ecs.list_services(cluster=cluster_name)
                    
                    for service_arn in services_response['serviceArns']:
                        service_name = service_arn.split('/')[-1]
                        
                        try:
                            # Scale service to 1
                            ecs.update_service(
                                cluster=cluster_name,
                                service=service_name,
                                desiredCount=1
                            )
                            print(f"✅ Scaling up service: {service_name}")
                            self.log_action('scale_ecs', f"{cluster_name}/{service_name}", 'scaled_to_1')
                        except Exception as e:
                            print(f"⚠️  Could not scale service {service_name}: {e}")
                            self.log_action('scale_ecs', f"{cluster_name}/{service_name}", f'error: {e}')
            
        except Exception as e:
            print(f"❌ Error starting ECS services: {e}")
            self.log_action('start_ecs', 'all', f'error: {e}')
    
    def start_app_runner_services(self, shutdown_log=None):
        """Start App Runner services"""
        print("\n🏃 Starting App Runner services...")
        
        try:
            apprunner = self.session.client('apprunner')
            
            # List services
            response = apprunner.list_services()
            
            vismaya_services = []
            for service in response['ServiceSummaryList']:
                if 'vismaya' in service['ServiceName'].lower():
                    if service['Status'] == 'PAUSED':
                        vismaya_services.append(service['ServiceArn'])
                        print(f"   Found paused App Runner service: {service['ServiceName']}")
            
            for service_arn in vismaya_services:
                try:
                    apprunner.resume_service(ServiceArn=service_arn)
                    print(f"✅ Resuming App Runner service: {service_arn.split('/')[-1]}")
                    self.log_action('resume_apprunner', service_arn, 'resumed')
                except Exception as e:
                    print(f"⚠️  Could not resume service {service_arn}: {e}")
                    self.log_action('resume_apprunner', service_arn, f'error: {e}')
            
            if not vismaya_services:
                print("   No paused Vismaya App Runner services found")
                
        except Exception as e:
            print(f"❌ Error starting App Runner services: {e}")
            self.log_action('start_apprunner', 'all', f'error: {e}')
    
    def quick_deploy_option(self):
        """Provide quick deployment options"""
        print("\n🚀 Quick Deployment Options:")
        print("=" * 40)
        print("1. Local Development:")
        print("   python app.py")
        print("")
        print("2. Docker Deployment:")
        print("   ./deploy/docker-deploy.sh compose")
        print("")
        print("3. AWS CloudFormation:")
        print("   ./deploy.sh")
        print("")
        print("4. Manual EC2 Setup:")
        print("   See DEPLOYMENT.md for detailed instructions")
        print("=" * 40)
    
    def save_startup_log(self):
        """Save startup log"""
        log_file = f"startup_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(log_file, 'w') as f:
            json.dump({
                'startup_time': datetime.now().isoformat(),
                'region': self.region,
                'actions': self.startup_log
            }, f, indent=2)
        
        print(f"\n📝 Startup log saved to: {log_file}")
        return log_file
    
    def estimate_running_costs(self):
        """Estimate running costs"""
        print("\n💰 Estimated running costs:")
        
        # Count started resources
        ec2_count = len([log for log in self.startup_log if log['action'] == 'start_ec2' and log['status'] == 'completed'])
        rds_count = len([log for log in self.startup_log if log['action'] == 'start_rds' and log['status'] == 'initiated'])
        
        # Rough cost estimates (per hour)
        ec2_costs = ec2_count * 0.05  # ~$0.05/hour for t3.medium
        rds_costs = rds_count * 0.08  # ~$0.08/hour for db.t3.medium
        
        hourly_costs = ec2_costs + rds_costs
        daily_costs = hourly_costs * 24
        monthly_costs = daily_costs * 30
        
        print(f"   EC2 instances running: {ec2_count}")
        print(f"   RDS instances running: {rds_count}")
        print(f"   Estimated hourly cost: ${hourly_costs:.2f}")
        print(f"   Estimated daily cost: ${daily_costs:.2f}")
        print(f"   Estimated monthly cost: ${monthly_costs:.2f}")
        
        if hourly_costs > 0:
            print(f"\n⚠️  Remember to run 'python shutdown-aws.py' when done testing!")
    
    def run_startup(self):
        """Run complete startup process"""
        print("=" * 60)
        print("🚀 Vismaya DemandOps - AWS Resource Startup")
        print("Team MaximAI - AI-Powered FinOps Platform")
        print("=" * 60)
        
        # Load shutdown log
        shutdown_log = self.load_shutdown_log()
        
        print("\nStartup options:")
        print("1. Start existing stopped resources")
        print("2. Deploy new infrastructure")
        print("3. Show deployment options only")
        
        choice = input("\nSelect option (1-3): ").strip()
        
        if choice == '1':
            print("\n🚀 Starting existing resources...")
            self.start_ec2_instances(shutdown_log)
            self.start_rds_instances(shutdown_log)
            self.start_ecs_services(shutdown_log)
            self.start_app_runner_services(shutdown_log)
            
        elif choice == '2':
            print("\n🚀 Deploying new infrastructure...")
            self.deploy_cloudformation_stack()
            
        elif choice == '3':
            self.quick_deploy_option()
            return
        
        else:
            print("❌ Invalid option")
            return
        
        # Save log and show costs
        log_file = self.save_startup_log()
        self.estimate_running_costs()
        self.quick_deploy_option()
        
        print("\n" + "=" * 60)
        print("✅ Startup process completed!")
        print("=" * 60)
        print(f"📝 Log file: {log_file}")
        print("🛑 To stop resources, run: python shutdown-aws.py")
        print("=" * 60)

def main():
    try:
        startup = AWSResourceStartup()
        startup.run_startup()
    except KeyboardInterrupt:
        print("\n❌ Startup cancelled by user")
    except Exception as e:
        print(f"\n❌ Startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()