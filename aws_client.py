import boto3
from datetime import datetime, timedelta
import pandas as pd
from config import Config
import logging

logger = logging.getLogger(__name__)

class AWSClient:
    def __init__(self):
        self.session = self._create_session()
        
        try:
            self.cost_explorer = self.session.client('ce')
            self.ec2 = self.session.client('ec2')
            self.cloudwatch = self.session.client('cloudwatch')
            self.bedrock = self.session.client('bedrock-runtime')
            logger.info("AWS clients initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing AWS clients: {e}")
            raise
    
    def _create_session(self):
        """Create AWS session with appropriate authentication method"""
        try:
            if Config.use_sso():
                # Use SSO or default profile
                logger.info("Using AWS SSO/Profile authentication")
                return boto3.Session(
                    profile_name=Config.AWS_PROFILE,
                    region_name=Config.AWS_REGION
                )
            else:
                # Use explicit credentials (for AWS deployment)
                logger.info("Using explicit AWS credentials")
                return boto3.Session(
                    aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
                    aws_session_token=Config.AWS_SESSION_TOKEN,
                    region_name=Config.AWS_REGION
                )
        except Exception as e:
            logger.warning(f"Error creating AWS session: {e}. Using default session.")
            return boto3.Session(region_name=Config.AWS_REGION)
    
    def get_current_month_costs(self):
        """Get current month's AWS costs"""
        try:
            now = datetime.now()
            start_date = now.replace(day=1).strftime('%Y-%m-%d')
            end_date = now.strftime('%Y-%m-%d')
            
            response = self.cost_explorer.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='DAILY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ]
            )
            
            return response
        except Exception as e:
            print(f"Error fetching costs: {e}")
            return self._get_mock_cost_data()
    
    def get_monthly_trend(self):
        """Get monthly cost trend for the past 6 months"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=180)
            
            response = self.cost_explorer.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost']
            )
            
            return response
        except Exception as e:
            print(f"Error fetching monthly trend: {e}")
            return self._get_mock_trend_data()
    
    def get_service_costs(self):
        """Get costs by AWS service"""
        try:
            now = datetime.now()
            start_date = now.replace(day=1).strftime('%Y-%m-%d')
            end_date = now.strftime('%Y-%m-%d')
            
            response = self.cost_explorer.get_cost_and_usage(
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
            
            return response
        except Exception as e:
            print(f"Error fetching service costs: {e}")
            return self._get_mock_service_data()
    
    def get_ec2_instances(self):
        """Get current EC2 instances"""
        try:
            response = self.ec2.describe_instances()
            return response
        except Exception as e:
            print(f"Error fetching EC2 instances: {e}")
            return self._get_mock_ec2_data()
    
    def _get_mock_cost_data(self):
        """Mock cost data for demo purposes"""
        return {
            'ResultsByTime': [
                {
                    'TimePeriod': {
                        'Start': '2024-01-01',
                        'End': '2024-01-31'
                    },
                    'Total': {
                        'BlendedCost': {
                            'Amount': '12500.00',
                            'Unit': 'USD'
                        }
                    }
                }
            ]
        }
    
    def _get_mock_trend_data(self):
        """Mock trend data for demo purposes"""
        return {
            'ResultsByTime': [
                {'TimePeriod': {'Start': '2024-01-01'}, 'Total': {'BlendedCost': {'Amount': '5000'}}},
                {'TimePeriod': {'Start': '2024-02-01'}, 'Total': {'BlendedCost': {'Amount': '8000'}}},
                {'TimePeriod': {'Start': '2024-03-01'}, 'Total': {'BlendedCost': {'Amount': '12000'}}},
                {'TimePeriod': {'Start': '2024-04-01'}, 'Total': {'BlendedCost': {'Amount': '18000'}}},
                {'TimePeriod': {'Start': '2024-05-01'}, 'Total': {'BlendedCost': {'Amount': '23000'}}},
            ]
        }
    
    def _get_mock_service_data(self):
        """Mock service cost data for demo purposes"""
        return {
            'ResultsByTime': [
                {
                    'Groups': [
                        {'Keys': ['Amazon Elastic Compute Cloud - Compute'], 'Metrics': {'BlendedCost': {'Amount': '5500'}}},
                        {'Keys': ['Amazon Relational Database Service'], 'Metrics': {'BlendedCost': {'Amount': '8000'}}},
                        {'Keys': ['Amazon Simple Storage Service'], 'Metrics': {'BlendedCost': {'Amount': '3500'}}},
                        {'Keys': ['Amazon Elastic Block Store'], 'Metrics': {'BlendedCost': {'Amount': '7500'}}},
                    ]
                }
            ]
        }
    
    def _get_mock_ec2_data(self):
        """Mock EC2 data for demo purposes"""
        return {
            'Reservations': [
                {
                    'Instances': [
                        {
                            'InstanceId': 'i-1234567890abcdef0',
                            'InstanceType': 't3.medium',
                            'State': {'Name': 'running'},
                            'Tags': [{'Key': 'Name', 'Value': 'Web Server 1'}]
                        },
                        {
                            'InstanceId': 'i-0987654321fedcba0',
                            'InstanceType': 't3.large',
                            'State': {'Name': 'running'},
                            'Tags': [{'Key': 'Name', 'Value': 'Database Server'}]
                        }
                    ]
                }
            ]
        }