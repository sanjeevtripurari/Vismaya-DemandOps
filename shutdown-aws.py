#!/usr/bin/env python3
"""
AWS Resource Shutdown Script for Vismaya DemandOps
Safely shuts down AWS resources to prevent billing
"""

import boto3
import json
import time
import sys
from datetime import datetime
from config import Config

class AWSResourceShutdown:
    def __init__(self):
        self.session = self._create_session()
        self.region = Config.AWS_REGION
        self.shutdown_log = []
        
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
        """Log shutdown actions"""
        self.shutdown_log.append({
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'resource_id': resource_id,
            'status': status
        })
    
    def stop_ec2_instances(self):
        """Stop all running EC2 instances"""
        print("🖥️  Stopping EC2 instances...")
        
        try:
            ec2 = self.session.client('ec2')
            
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
                    print(f"   Found running instance: {instance['InstanceId']}")
            
            if instance_ids:
                # Stop instances
                ec2.stop_instances(InstanceIds=instance_ids)
                print(f"✅ Stopping {len(instance_ids)} EC2 instances")
                
                for instance_id in instance_ids:
                    self.log_action('stop_ec2', instance_id, 'initiated')
                
                # Wait for instances to stop
                print("   Waiting for instances to stop...")
                waiter = ec2.get_waiter('instance_stopped')
                waiter.wait(InstanceIds=instance_ids, WaiterConfig={'Delay': 15, 'MaxAttempts': 20})
                print("✅ All instances stopped successfully")
                
                for instance_id in instance_ids:
                    self.log_action('stop_ec2', instance_id, 'completed')
            else:
                print("   No running Vismaya instances found")
                
        except Exception as e:
            print(f"❌ Error stopping EC2 instances: {e}")
            self.log_action('stop_ec2', 'all', f'error: {e}')
    
    def stop_rds_instances(self):
        """Stop RDS instances"""
        print("\n🗄️  Stopping RDS instances...")
        
        try:
            rds = self.session.client('rds')
            
            # Get running RDS instances
            response = rds.describe_db_instances()
            
            vismaya_instances = []
            for db in response['DBInstances']:
                # Check if it's a Vismaya-related instance
                if ('vismaya' in db['DBInstanceIdentifier'].lower() or 
                    any(tag.get('Key') == 'Project' and 'vismaya' in tag.get('Value', '').lower() 
                        for tag in db.get('TagList', []))):
                    if db['DBInstanceStatus'] == 'available':
                        vismaya_instances.append(db['DBInstanceIdentifier'])
                        print(f"   Found RDS instance: {db['DBInstanceIdentifier']}")
            
            for db_id in vismaya_instances:
                try:
                    rds.stop_db_instance(DBInstanceIdentifier=db_id)
                    print(f"✅ Stopping RDS instance: {db_id}")
                    self.log_action('stop_rds', db_id, 'initiated')
                except Exception as e:
                    print(f"⚠️  Could not stop RDS instance {db_id}: {e}")
                    self.log_action('stop_rds', db_id, f'error: {e}')
            
            if not vismaya_instances:
                print("   No Vismaya RDS instances found")
                
        except Exception as e:
            print(f"❌ Error stopping RDS instances: {e}")
            self.log_action('stop_rds', 'all', f'error: {e}')
    
    def delete_cloudformation_stacks(self):
        """Delete CloudFormation stacks"""
        print("\n☁️  Deleting CloudFormation stacks...")
        
        try:
            cf = self.session.client('cloudformation')
            
            # List stacks
            response = cf.list_stacks(
                StackStatusFilter=[
                    'CREATE_COMPLETE', 'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_COMPLETE'
                ]
            )
            
            vismaya_stacks = []
            for stack in response['StackSummaries']:
                if 'vismaya' in stack['StackName'].lower():
                    vismaya_stacks.append(stack['StackName'])
                    print(f"   Found stack: {stack['StackName']}")
            
            for stack_name in vismaya_stacks:
                try:
                    cf.delete_stack(StackName=stack_name)
                    print(f"✅ Deleting stack: {stack_name}")
                    self.log_action('delete_stack', stack_name, 'initiated')
                except Exception as e:
                    print(f"⚠️  Could not delete stack {stack_name}: {e}")
                    self.log_action('delete_stack', stack_name, f'error: {e}')
            
            if not vismaya_stacks:
                print("   No Vismaya CloudFormation stacks found")
                
        except Exception as e:
            print(f"❌ Error deleting CloudFormation stacks: {e}")
            self.log_action('delete_stack', 'all', f'error: {e}')
    
    def stop_ecs_services(self):
        """Stop ECS services"""
        print("\n🐳 Stopping ECS services...")
        
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
                            # Scale service to 0
                            ecs.update_service(
                                cluster=cluster_name,
                                service=service_name,
                                desiredCount=0
                            )
                            print(f"✅ Scaling down service: {service_name}")
                            self.log_action('scale_ecs', f"{cluster_name}/{service_name}", 'scaled_to_0')
                        except Exception as e:
                            print(f"⚠️  Could not scale service {service_name}: {e}")
                            self.log_action('scale_ecs', f"{cluster_name}/{service_name}", f'error: {e}')
            
        except Exception as e:
            print(f"❌ Error stopping ECS services: {e}")
            self.log_action('stop_ecs', 'all', f'error: {e}')
    
    def stop_app_runner_services(self):
        """Stop App Runner services"""
        print("\n🏃 Stopping App Runner services...")
        
        try:
            apprunner = self.session.client('apprunner')
            
            # List services
            response = apprunner.list_services()
            
            vismaya_services = []
            for service in response['ServiceSummaryList']:
                if 'vismaya' in service['ServiceName'].lower():
                    vismaya_services.append(service['ServiceArn'])
                    print(f"   Found App Runner service: {service['ServiceName']}")
            
            for service_arn in vismaya_services:
                try:
                    apprunner.pause_service(ServiceArn=service_arn)
                    print(f"✅ Pausing App Runner service: {service_arn.split('/')[-1]}")
                    self.log_action('pause_apprunner', service_arn, 'paused')
                except Exception as e:
                    print(f"⚠️  Could not pause service {service_arn}: {e}")
                    self.log_action('pause_apprunner', service_arn, f'error: {e}')
            
            if not vismaya_services:
                print("   No Vismaya App Runner services found")
                
        except Exception as e:
            print(f"❌ Error stopping App Runner services: {e}")
            self.log_action('stop_apprunner', 'all', f'error: {e}')
    
    def cleanup_unused_resources(self):
        """Clean up unused resources that might incur costs"""
        print("\n🧹 Cleaning up unused resources...")
        
        try:
            ec2 = self.session.client('ec2')
            
            # Delete unattached EBS volumes
            volumes_response = ec2.describe_volumes(
                Filters=[
                    {'Name': 'status', 'Values': ['available']},
                    {'Name': 'tag:Project', 'Values': ['VismayaDemandOps', 'vismaya*']}
                ]
            )
            
            for volume in volumes_response['Volumes']:
                volume_id = volume['VolumeId']
                try:
                    ec2.delete_volume(VolumeId=volume_id)
                    print(f"✅ Deleted unattached volume: {volume_id}")
                    self.log_action('delete_volume', volume_id, 'deleted')
                except Exception as e:
                    print(f"⚠️  Could not delete volume {volume_id}: {e}")
                    self.log_action('delete_volume', volume_id, f'error: {e}')
            
            # Delete unused Elastic IPs
            eips_response = ec2.describe_addresses()
            
            for eip in eips_response['Addresses']:
                if 'InstanceId' not in eip and 'NetworkInterfaceId' not in eip:
                    allocation_id = eip['AllocationId']
                    try:
                        ec2.release_address(AllocationId=allocation_id)
                        print(f"✅ Released unused Elastic IP: {eip['PublicIp']}")
                        self.log_action('release_eip', allocation_id, 'released')
                    except Exception as e:
                        print(f"⚠️  Could not release EIP {allocation_id}: {e}")
                        self.log_action('release_eip', allocation_id, f'error: {e}')
                        
        except Exception as e:
            print(f"❌ Error cleaning up resources: {e}")
            self.log_action('cleanup', 'all', f'error: {e}')
    
    def save_shutdown_log(self):
        """Save shutdown log for startup reference"""
        log_file = f"shutdown_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(log_file, 'w') as f:
            json.dump({
                'shutdown_time': datetime.now().isoformat(),
                'region': self.region,
                'actions': self.shutdown_log
            }, f, indent=2)
        
        print(f"\n📝 Shutdown log saved to: {log_file}")
        return log_file
    
    def estimate_cost_savings(self):
        """Estimate cost savings from shutdown"""
        print("\n💰 Estimated cost savings:")
        
        # Count stopped resources
        ec2_count = len([log for log in self.shutdown_log if log['action'] == 'stop_ec2' and log['status'] == 'completed'])
        rds_count = len([log for log in self.shutdown_log if log['action'] == 'stop_rds' and log['status'] == 'initiated'])
        
        # Rough cost estimates (per hour)
        ec2_savings = ec2_count * 0.05  # ~$0.05/hour for t3.medium
        rds_savings = rds_count * 0.08  # ~$0.08/hour for db.t3.medium
        
        daily_savings = (ec2_savings + rds_savings) * 24
        monthly_savings = daily_savings * 30
        
        print(f"   EC2 instances stopped: {ec2_count}")
        print(f"   RDS instances stopped: {rds_count}")
        print(f"   Estimated daily savings: ${daily_savings:.2f}")
        print(f"   Estimated monthly savings: ${monthly_savings:.2f}")
    
    def run_shutdown(self):
        """Run complete shutdown process"""
        print("=" * 60)
        print("🛑 Vismaya DemandOps - AWS Resource Shutdown")
        print("Team MaximAI - AI-Powered FinOps Platform")
        print("=" * 60)
        print("This will stop/delete AWS resources to prevent billing.")
        print("Make sure you have saved any important data!")
        
        confirm = input("\nDo you want to continue? (yes/no): ").lower().strip()
        if confirm != 'yes':
            print("❌ Shutdown cancelled")
            return
        
        print("\n🚀 Starting shutdown process...")
        
        # Stop resources
        self.stop_ec2_instances()
        self.stop_rds_instances()
        self.stop_ecs_services()
        self.stop_app_runner_services()
        self.cleanup_unused_resources()
        self.delete_cloudformation_stacks()
        
        # Save log and show savings
        log_file = self.save_shutdown_log()
        self.estimate_cost_savings()
        
        print("\n" + "=" * 60)
        print("✅ Shutdown process completed!")
        print("=" * 60)
        print(f"📝 Log file: {log_file}")
        print("🚀 To restart resources, run: python startup-aws.py")
        print("=" * 60)

def main():
    try:
        shutdown = AWSResourceShutdown()
        shutdown.run_shutdown()
    except KeyboardInterrupt:
        print("\n❌ Shutdown cancelled by user")
    except Exception as e:
        print(f"\n❌ Shutdown failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()