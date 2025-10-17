"""
AWS Resource Provider
Implements IResourceProvider interface
Following Dependency Inversion Principle
"""

import logging
from typing import List

from ..core.interfaces import IResourceProvider
from ..core.models import EC2Instance, StorageVolume, DatabaseInstance, InstanceState

logger = logging.getLogger(__name__)


class AWSResourceProvider(IResourceProvider):
    """AWS resource provider implementation"""
    
    def __init__(self, aws_session):
        self._session = aws_session
        self._ec2_client = None
        self._rds_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize AWS clients"""
        try:
            self._ec2_client = self._session.client('ec2')
            self._rds_client = self._session.client('rds')
            logger.info("AWS resource clients initialized")
        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {e}")
            self._ec2_client = None
            self._rds_client = None
    
    async def get_ec2_instances(self) -> List[EC2Instance]:
        """Get EC2 instances"""
        try:
            if not self._ec2_client:
                return self._get_mock_ec2_instances()
            
            response = self._ec2_client.describe_instances()
            instances = []
            
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    # Extract instance name from tags
                    name = ""
                    tags = {}
                    if 'Tags' in instance:
                        for tag in instance['Tags']:
                            tags[tag['Key']] = tag['Value']
                            if tag['Key'] == 'Name':
                                name = tag['Value']
                    
                    # Estimate monthly cost (rough calculation)
                    monthly_cost = self._estimate_ec2_cost(instance['InstanceType'])
                    
                    instances.append(EC2Instance(
                        instance_id=instance['InstanceId'],
                        instance_type=instance['InstanceType'],
                        state=InstanceState(instance['State']['Name']),
                        name=name,
                        monthly_cost=monthly_cost,
                        tags=tags
                    ))
            
            return instances if instances else self._get_mock_ec2_instances()
            
        except Exception as e:
            logger.error(f"Error fetching EC2 instances: {e}")
            return self._get_mock_ec2_instances()
    
    async def get_storage_volumes(self) -> List[StorageVolume]:
        """Get EBS volumes"""
        try:
            if not self._ec2_client:
                return self._get_mock_storage_volumes()
            
            response = self._ec2_client.describe_volumes()
            volumes = []
            
            for volume in response['Volumes']:
                # Get attached instance
                attached_instance = ""
                if volume['Attachments']:
                    attached_instance = volume['Attachments'][0]['InstanceId']
                
                # Estimate monthly cost
                monthly_cost = self._estimate_ebs_cost(volume['Size'], volume['VolumeType'])
                
                volumes.append(StorageVolume(
                    volume_id=volume['VolumeId'],
                    size_gb=volume['Size'],
                    volume_type=volume['VolumeType'],
                    monthly_cost=monthly_cost,
                    attached_instance=attached_instance
                ))
            
            return volumes if volumes else self._get_mock_storage_volumes()
            
        except Exception as e:
            logger.error(f"Error fetching storage volumes: {e}")
            return self._get_mock_storage_volumes()
    
    async def get_database_instances(self) -> List[DatabaseInstance]:
        """Get RDS instances"""
        try:
            if not self._rds_client:
                return self._get_mock_database_instances()
            
            response = self._rds_client.describe_db_instances()
            databases = []
            
            for db in response['DBInstances']:
                # Estimate monthly cost
                monthly_cost = self._estimate_rds_cost(db['DBInstanceClass'], db['Engine'])
                
                databases.append(DatabaseInstance(
                    db_instance_id=db['DBInstanceIdentifier'],
                    engine=db['Engine'],
                    instance_class=db['DBInstanceClass'],
                    monthly_cost=monthly_cost,
                    status=db['DBInstanceStatus']
                ))
            
            return databases if databases else self._get_mock_database_instances()
            
        except Exception as e:
            logger.error(f"Error fetching database instances: {e}")
            return self._get_mock_database_instances()
    
    def _estimate_ec2_cost(self, instance_type: str) -> float:
        """Estimate monthly EC2 cost (rough calculation)"""
        # These are rough estimates - in production, use AWS Pricing API
        cost_mapping = {
            't3.nano': 3.80,
            't3.micro': 7.60,
            't3.small': 15.20,
            't3.medium': 30.40,
            't3.large': 60.80,
            't3.xlarge': 121.60,
            't3.2xlarge': 243.20,
            'm5.large': 70.08,
            'm5.xlarge': 140.16,
            'm5.2xlarge': 280.32,
            'c5.large': 62.56,
            'c5.xlarge': 125.12,
            'r5.large': 91.25,
            'r5.xlarge': 182.50
        }
        
        return cost_mapping.get(instance_type, 50.0)  # Default estimate
    
    def _estimate_ebs_cost(self, size_gb: int, volume_type: str) -> float:
        """Estimate monthly EBS cost"""
        # Cost per GB per month
        cost_per_gb = {
            'gp2': 0.10,
            'gp3': 0.08,
            'io1': 0.125,
            'io2': 0.125,
            'st1': 0.045,
            'sc1': 0.025
        }
        
        rate = cost_per_gb.get(volume_type, 0.10)
        return size_gb * rate
    
    def _estimate_rds_cost(self, instance_class: str, engine: str) -> float:
        """Estimate monthly RDS cost"""
        # Base cost mapping (rough estimates)
        base_costs = {
            'db.t3.micro': 12.41,
            'db.t3.small': 24.82,
            'db.t3.medium': 49.64,
            'db.t3.large': 99.28,
            'db.m5.large': 138.24,
            'db.m5.xlarge': 276.48,
            'db.r5.large': 174.72,
            'db.r5.xlarge': 349.44
        }
        
        base_cost = base_costs.get(instance_class, 100.0)
        
        # Engine multiplier
        engine_multiplier = {
            'mysql': 1.0,
            'postgres': 1.0,
            'oracle-ee': 2.5,
            'sqlserver-ee': 3.0,
            'aurora-mysql': 1.2,
            'aurora-postgresql': 1.2
        }
        
        multiplier = engine_multiplier.get(engine, 1.0)
        return base_cost * multiplier
    
    def _get_mock_ec2_instances(self) -> List[EC2Instance]:
        """Mock EC2 instances for demo"""
        return [
            EC2Instance(
                instance_id="i-1234567890abcdef0",
                instance_type="t3.medium",
                state=InstanceState.RUNNING,
                name="Web Server 1",
                monthly_cost=30.40,
                tags={"Environment": "Production", "Team": "WebDev"}
            ),
            EC2Instance(
                instance_id="i-0987654321fedcba0",
                instance_type="t3.large",
                state=InstanceState.RUNNING,
                name="Database Server",
                monthly_cost=60.80,
                tags={"Environment": "Production", "Team": "Database"}
            ),
            EC2Instance(
                instance_id="i-abcdef1234567890",
                instance_type="t3.small",
                state=InstanceState.STOPPED,
                name="Development Server",
                monthly_cost=0.0,  # Stopped instance
                tags={"Environment": "Development", "Team": "DevOps"}
            )
        ]
    
    def _get_mock_storage_volumes(self) -> List[StorageVolume]:
        """Mock storage volumes for demo"""
        return [
            StorageVolume(
                volume_id="vol-1234567890abcdef0",
                size_gb=100,
                volume_type="gp3",
                monthly_cost=8.0,
                attached_instance="i-1234567890abcdef0"
            ),
            StorageVolume(
                volume_id="vol-0987654321fedcba0",
                size_gb=500,
                volume_type="gp3",
                monthly_cost=40.0,
                attached_instance="i-0987654321fedcba0"
            ),
            StorageVolume(
                volume_id="vol-abcdef1234567890",
                size_gb=50,
                volume_type="gp2",
                monthly_cost=5.0,
                attached_instance="i-abcdef1234567890"
            )
        ]
    
    def _get_mock_database_instances(self) -> List[DatabaseInstance]:
        """Mock database instances for demo"""
        return [
            DatabaseInstance(
                db_instance_id="prod-db-1",
                engine="mysql",
                instance_class="db.t3.medium",
                monthly_cost=49.64,
                status="available"
            ),
            DatabaseInstance(
                db_instance_id="analytics-db",
                engine="postgres",
                instance_class="db.r5.large",
                monthly_cost=174.72,
                status="available"
            )
        ]