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
                logger.error("EC2 client not available")
                return []
            
            # Track API cost
            from ..services.api_cost_tracker import api_cost_tracker
            
            response = self._ec2_client.describe_instances()
            
            # Track the API call
            instance_count = sum(len(r['Instances']) for r in response['Reservations'])
            api_cost_tracker.track_ec2_call('DescribeInstances', instance_count)
            
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
            
            logger.info(f"âœ… Retrieved {len(instances)} real EC2 instances")
            return instances
            
        except Exception as e:
            logger.error(f"âŒ Error fetching EC2 instances: {e}")
            # NO MOCK DATA - return empty list for real data
            return []
    
    async def get_storage_volumes(self) -> List[StorageVolume]:
        """Get EBS volumes"""
        try:
            if not self._ec2_client:
                logger.error("EC2 client not available for storage volumes")
                return []
            
            # Track API cost
            from ..services.api_cost_tracker import api_cost_tracker
            
            response = self._ec2_client.describe_volumes()
            
            # Track the API call
            volume_count = len(response['Volumes'])
            api_cost_tracker.track_ec2_call('DescribeVolumes', volume_count)
            
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
            
            logger.info(f"âœ… Retrieved {len(volumes)} real storage volumes")
            return volumes
            
        except Exception as e:
            logger.error(f"âŒ Error fetching storage volumes: {e}")
            # NO MOCK DATA - return empty list for real data
            return []
    
    async def get_database_instances(self) -> List[DatabaseInstance]:
        """Get RDS instances"""
        try:
            if not self._rds_client:
                logger.error("RDS client not available")
                return []
            
            # Track API cost
            from ..services.api_cost_tracker import api_cost_tracker
            
            response = self._rds_client.describe_db_instances()
            
            # Track the API call
            db_count = len(response['DBInstances'])
            api_cost_tracker.track_rds_call('DescribeDBInstances', db_count)
            
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
            
            logger.info(f"âœ… Retrieved {len(databases)} real database instances")
            return databases
            
        except Exception as e:
            logger.error(f"âŒ Error fetching database instances: {e}")
            # NO MOCK DATA - return empty list for real data
            return []
    
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
    
