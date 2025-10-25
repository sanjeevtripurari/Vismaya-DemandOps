"""
Natural Language Query Parser
Extracts structured resource specifications from natural language queries
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from ..core.interfaces import IQueryParser
from ..core.models import (
    ResourceSpecification, ResourceType, TimePeriod,
    InvalidResourceSpecificationError
)

logger = logging.getLogger(__name__)


class NaturalLanguageQueryParser(IQueryParser):
    """Parser for natural language cost estimation queries"""
    
    def __init__(self):
        # Resource type patterns
        self.resource_patterns = {
            ResourceType.EC2: [
                r'\bec2\b', r'\binstance[s]?\b', r'\bserver[s]?\b', r'\bcompute\b',
                r'\bvm[s]?\b', r'\bvirtual machine[s]?\b'
            ],
            ResourceType.RDS: [
                r'\brds\b', r'\bdatabase[s]?\b', r'\bdb\b', r'\bmysql\b', r'\bpostgres\b',
                r'\bmariadb\b', r'\boracle\b', r'\bsql server\b'
            ],
            ResourceType.S3: [
                r'\bs3\b', r'\bstorage\b', r'\bbucket[s]?\b', r'\bobject storage\b'
            ],
            ResourceType.EBS: [
                r'\bebs\b', r'\bvolume[s]?\b', r'\bdisk[s]?\b', r'\bblock storage\b'
            ],
            ResourceType.LAMBDA: [
                r'\blambda\b', r'\bfunction[s]?\b', r'\bserverless\b'
            ]
        }
        
        # EC2 instance type patterns
        self.ec2_instance_patterns = [
            # General Purpose
            r'\bt[2-4]\.(nano|micro|small|medium|large|xlarge|2xlarge)\b',
            r'\bm[4-6]\.(large|xlarge|2xlarge|4xlarge|8xlarge|12xlarge|16xlarge|24xlarge)\b',
            r'\ba1\.(medium|large|xlarge|2xlarge|4xlarge)\b',
            
            # Compute Optimized
            r'\bc[4-6]\.(large|xlarge|2xlarge|4xlarge|8xlarge|9xlarge|12xlarge|18xlarge|24xlarge)\b',
            
            # Memory Optimized
            r'\br[4-6]\.(large|xlarge|2xlarge|4xlarge|8xlarge|12xlarge|16xlarge|24xlarge)\b',
            r'\bx1[e]?\.(xlarge|2xlarge|4xlarge|8xlarge|16xlarge|32xlarge)\b',
            r'\bz1d\.(large|xlarge|2xlarge|3xlarge|6xlarge|12xlarge)\b',
            
            # Storage Optimized
            r'\bi[3-4]\.(large|xlarge|2xlarge|4xlarge|8xlarge|16xlarge|24xlarge)\b',
            r'\bd[2-3]\.(xlarge|2xlarge|4xlarge|8xlarge)\b',
            r'\bh1\.(2xlarge|4xlarge|8xlarge|16xlarge)\b'
        ]
        
        # RDS instance type patterns
        self.rds_instance_patterns = [
            r'\bdb\.t[2-4]\.(nano|micro|small|medium|large|xlarge|2xlarge)\b',
            r'\bdb\.m[4-6]\.(large|xlarge|2xlarge|4xlarge|8xlarge|12xlarge|16xlarge|24xlarge)\b',
            r'\bdb\.r[4-6]\.(large|xlarge|2xlarge|4xlarge|8xlarge|12xlarge|16xlarge|24xlarge)\b'
        ]
        
        # Time period patterns
        self.time_patterns = [
            (r'(\d+)\s*month[s]?', 'months'),
            (r'(\d+)\s*week[s]?', 'weeks'),
            (r'(\d+)\s*day[s]?', 'days'),
            (r'(\d+)\s*year[s]?', 'years'),
            (r'(\d+)\s*hr[s]?', 'hours'),
            (r'(\d+)\s*hour[s]?', 'hours')
        ]
        
        # Quantity patterns
        self.quantity_patterns = [
            r'(\d+)\s*(?:instance[s]?|server[s]?|vm[s]?|machine[s]?)',
            r'(\d+)\s*(?:database[s]?|db[s]?)',
            r'(\d+)\s*(?:volume[s]?|disk[s]?)',
            r'(\d+)\s*(?:gb|gigabyte[s]?|tb|terabyte[s]?)',
            r'(\d+)\s*(?:unit[s]?|resource[s]?)'
        ]
        
        # Region patterns
        self.region_patterns = {
            'us-east-1': [r'\bus-east-1\b', r'\bvirginia\b', r'\bn\.?\s*virginia\b'],
            'us-east-2': [r'\bus-east-2\b', r'\bohio\b'],
            'us-west-1': [r'\bus-west-1\b', r'\bcalifornia\b', r'\bn\.?\s*california\b'],
            'us-west-2': [r'\bus-west-2\b', r'\boregon\b'],
            'eu-west-1': [r'\beu-west-1\b', r'\bireland\b'],
            'eu-central-1': [r'\beu-central-1\b', r'\bfrankfurt\b', r'\bgermany\b'],
            'ap-southeast-1': [r'\bap-southeast-1\b', r'\bsingapore\b'],
            'ap-southeast-2': [r'\bap-southeast-2\b', r'\bsydney\b', r'\baustralia\b'],
            'ap-northeast-1': [r'\bap-northeast-1\b', r'\btokyo\b', r'\bjapan\b']
        }
        
        # Operating system patterns
        self.os_patterns = {
            'Linux': [r'\blinux\b', r'\bubuntu\b', r'\bamazon linux\b', r'\bcentos\b', r'\brhel\b'],
            'Windows': [r'\bwindows\b', r'\bwin\b', r'\bmicrosoft\b'],
            'SUSE': [r'\bsuse\b'],
            'RHEL': [r'\brhel\b', r'\bred hat\b']
        }
    
    def parse_resource_query(self, query: str) -> ResourceSpecification:
        """Parse natural language query into structured resource specification"""
        try:
            query_lower = query.lower()
            logger.info(f"Parsing query: {query}")
            
            # Extract resource type
            resource_type = self._extract_resource_type(query_lower)
            if not resource_type:
                raise InvalidResourceSpecificationError("Could not identify resource type from query")
            
            # Extract instance type
            instance_type = self._extract_instance_type(query_lower, resource_type)
            
            # Extract region
            region = self._extract_region(query_lower)
            
            # Extract operating system
            operating_system = self._extract_operating_system(query_lower)
            
            # Extract quantity
            quantity = self._extract_quantity(query_lower)
            
            # Extract additional specifications
            additional_specs = self._extract_additional_specs(query_lower, resource_type)
            
            resource_spec = ResourceSpecification(
                resource_type=resource_type,
                instance_type=instance_type,
                region=region,
                operating_system=operating_system,
                quantity=quantity,
                additional_specs=additional_specs
            )
            
            logger.info(f"Parsed resource specification: {resource_spec}")
            return resource_spec
            
        except Exception as e:
            logger.error(f"Failed to parse query '{query}': {e}")
            raise InvalidResourceSpecificationError(f"Could not parse query: {str(e)}")
    
    def extract_time_period(self, query: str) -> TimePeriod:
        """Extract time period from query (e.g., '2 months', '6 weeks')"""
        try:
            query_lower = query.lower()
            
            for pattern, unit in self.time_patterns:
                match = re.search(pattern, query_lower)
                if match:
                    value = int(match.group(1))
                    
                    if unit == 'months':
                        return TimePeriod.from_months(value)
                    elif unit == 'weeks':
                        return TimePeriod.from_weeks(value)
                    elif unit == 'days':
                        return TimePeriod.from_days(value)
                    elif unit == 'years':
                        return TimePeriod.from_months(value * 12)
                    elif unit == 'hours':
                        return TimePeriod.from_days(max(1, value // 24))
            
            # Default to 1 month if no time period specified
            logger.info("No time period found in query, defaulting to 1 month")
            return TimePeriod.from_months(1)
            
        except Exception as e:
            logger.warning(f"Failed to extract time period from '{query}': {e}")
            return TimePeriod.from_months(1)
    
    def needs_clarification(self, resource_spec: ResourceSpecification) -> bool:
        """Check if resource specification needs clarification"""
        if not resource_spec.is_complete:
            return True
        
        # Check for ambiguous specifications
        if resource_spec.resource_type == ResourceType.EC2:
            if not resource_spec.instance_type:
                return True
        elif resource_spec.resource_type == ResourceType.RDS:
            if not resource_spec.instance_type:
                return True
        elif resource_spec.resource_type == ResourceType.EBS:
            if not resource_spec.additional_specs.get('size_gb'):
                return True
        
        return False
    
    def _extract_resource_type(self, query: str) -> Optional[ResourceType]:
        """Extract resource type from query"""
        for resource_type, patterns in self.resource_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    return resource_type
        return None
    
    def _extract_instance_type(self, query: str, resource_type: ResourceType) -> Optional[str]:
        """Extract instance type from query"""
        if resource_type == ResourceType.EC2:
            for pattern in self.ec2_instance_patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    return match.group(0).lower()
        
        elif resource_type == ResourceType.RDS:
            for pattern in self.rds_instance_patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    return match.group(0).lower()
        
        return None
    
    def _extract_region(self, query: str) -> str:
        """Extract AWS region from query"""
        for region, patterns in self.region_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    return region
        
        # Default to us-east-1
        return "us-east-1"
    
    def _extract_operating_system(self, query: str) -> str:
        """Extract operating system from query"""
        for os_name, patterns in self.os_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    return os_name
        
        # Default to Linux
        return "Linux"
    
    def _extract_quantity(self, query: str) -> int:
        """Extract quantity from query"""
        for pattern in self.quantity_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        # Look for standalone numbers
        number_match = re.search(r'\b(\d+)\b', query)
        if number_match:
            num = int(number_match.group(1))
            # Reasonable bounds for quantity
            if 1 <= num <= 1000:
                return num
        
        # Default to 1
        return 1
    
    def _extract_additional_specs(self, query: str, resource_type: ResourceType) -> Dict[str, any]:
        """Extract additional specifications based on resource type"""
        specs = {}
        
        if resource_type == ResourceType.EBS:
            # Extract storage size
            size_patterns = [
                r'(\d+)\s*gb',
                r'(\d+)\s*gigabyte[s]?',
                r'(\d+)\s*tb',
                r'(\d+)\s*terabyte[s]?'
            ]
            
            for pattern in size_patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    size = int(match.group(1))
                    if 'tb' in pattern or 'terabyte' in pattern:
                        size *= 1024  # Convert TB to GB
                    specs['size_gb'] = size
                    break
            
            # Extract volume type
            if re.search(r'\bgp3\b', query, re.IGNORECASE):
                specs['volume_type'] = 'gp3'
            elif re.search(r'\bgp2\b', query, re.IGNORECASE):
                specs['volume_type'] = 'gp2'
            elif re.search(r'\bio[12]\b', query, re.IGNORECASE):
                specs['volume_type'] = 'io1'
            else:
                specs['volume_type'] = 'gp3'  # Default
        
        elif resource_type == ResourceType.RDS:
            # Extract database engine
            if re.search(r'\bmysql\b', query, re.IGNORECASE):
                specs['engine'] = 'mysql'
            elif re.search(r'\bpostgres\b', query, re.IGNORECASE):
                specs['engine'] = 'postgres'
            elif re.search(r'\bmariadb\b', query, re.IGNORECASE):
                specs['engine'] = 'mariadb'
            elif re.search(r'\boracle\b', query, re.IGNORECASE):
                specs['engine'] = 'oracle-ee'
            elif re.search(r'\bsql server\b', query, re.IGNORECASE):
                specs['engine'] = 'sqlserver-ex'
            else:
                specs['engine'] = 'mysql'  # Default
            
            # Extract storage size
            storage_match = re.search(r'(\d+)\s*gb.*storage', query, re.IGNORECASE)
            if storage_match:
                specs['allocated_storage'] = int(storage_match.group(1))
        
        return specs
    
    def generate_clarification_questions(self, resource_spec: ResourceSpecification) -> List[str]:
        """Generate clarification questions for incomplete specifications"""
        questions = []
        
        if resource_spec.resource_type == ResourceType.EC2 and not resource_spec.instance_type:
            questions.append("What EC2 instance type would you like? (e.g., t3.micro, t3.small, m5.large)")
        
        if resource_spec.resource_type == ResourceType.RDS and not resource_spec.instance_type:
            questions.append("What RDS instance class would you like? (e.g., db.t3.micro, db.t3.small)")
        
        if resource_spec.resource_type == ResourceType.EBS and not resource_spec.additional_specs.get('size_gb'):
            questions.append("How much EBS storage do you need? (e.g., 100 GB, 1 TB)")
        
        if not questions:
            questions.append("Could you provide more details about the resource configuration you need?")
        
        return questions