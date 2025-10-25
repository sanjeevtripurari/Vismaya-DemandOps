"""
Smart Defaults Processor for Forecasting AI Assistant
Handles incomplete queries by applying intelligent defaults
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import re
from config import Config

@dataclass
class AppliedDefault:
    """Represents a default that was applied to a query"""
    field: str
    value: Any
    reason: str

class SmartDefaultsProcessor:
    """Processes incomplete queries and applies intelligent defaults"""
    
    def __init__(self):
        self.default_specs = {
            'ec2': {
                'instance_type': 't3.micro',
                'quantity': 1,
                'region': Config.AWS_REGION,
                'duration_months': 1,
                'pricing_model': 'on-demand'
            },
            'rds': {
                'instance_type': 'db.t3.micro',
                'engine': 'mysql',
                'storage_gb': 20,
                'quantity': 1,
                'duration_months': 1
            },
            'ebs': {
                'volume_type': 'gp3',
                'size_gb': 20,
                'quantity': 1,
                'duration_months': 1
            },
            's3': {
                'storage_class': 'standard',
                'size_gb': 10,
                'duration_months': 1
            },
            'lambda': {
                'memory_mb': 128,
                'duration_months': 1,
                'executions_per_month': 1000
            }
        }
        
        # Common patterns for extracting information from queries
        self.patterns = {
            'quantity': r'(\d+)\s*(?:x\s*)?(?:\w+\.\w+\s+)?(?:instances?|servers?|databases?|volumes?|ec2|rds)',
            'instance_type': r'(t3\.\w+|m5\.\w+|c5\.\w+|r5\.\w+|db\.t3\.\w+|db\.m5\.\w+)',
            'storage_size': r'(\d+)\s*(?:gb|tb|gib|tib)',
            'duration': r'(?:for\s+)?(\d+)\s*(?:months?|month|mo|years?|year|yr|days?|day)',
            'region': r'(?:in\s+|region\s+)?(us-east-\d|us-west-\d|eu-west-\d|eu-central-\d|ap-southeast-\d)'
        }
    
    def apply_defaults(self, query: str, parsed_query: Optional[Dict] = None) -> Dict[str, Any]:
        """Apply smart defaults to incomplete query - handle multiple resources"""
        
        # Check for multiple resource types in the query
        query_lower = query.lower()
        
        # Detect all resource types mentioned
        detected_resources = self._detect_all_resource_types(query)
        
        # For complex queries with multiple resources, prioritize the first mentioned
        if len(detected_resources) > 1:
            # Multi-resource query - process primary resource and add notes about others
            primary_resource = detected_resources[0]  # First detected resource
            result = self.default_specs.get(primary_resource, self.default_specs['ec2']).copy()
            result['resource_type'] = primary_resource
            result['applied_defaults'] = []
            
            # Add multi-resource handling
            result['is_multi_resource'] = True
            result['detected_resources'] = detected_resources
            result['multi_resource_notes'] = self._generate_multi_resource_notes(query, detected_resources)
            
        else:
            # Single resource query - original logic
            resource_type = self._detect_resource_type(query)
            result = self.default_specs.get(resource_type, self.default_specs['ec2']).copy()
            result['resource_type'] = resource_type
            result['applied_defaults'] = []
        
        # Extract any explicit specifications from the query
        extracted = self._extract_specifications(query)
        
        # Apply extracted specifications, keeping track of what we defaulted
        for key, value in extracted.items():
            if value is not None:
                result[key] = value
            else:
                # Track that we used a default for this field
                default_value = result.get(key)
                if default_value is not None:
                    result['applied_defaults'].append(AppliedDefault(
                        field=key,
                        value=default_value,
                        reason=f"Not specified in query, using minimum viable option"
                    ))
        
        # Add defaults for any missing critical fields
        self._ensure_critical_fields(result, result['resource_type'])
        
        # Add storage and database cost notes for multi-resource queries
        if result.get('is_multi_resource'):
            self._add_multi_resource_cost_notes(result, query)
        
        return result
    
    def _detect_resource_type(self, query: str) -> str:
        """Detect the primary resource type from the query"""
        query_lower = query.lower()
        
        try:
            # Check for specific resource mentions
            if any(term in query_lower for term in ['ec2', 'instance', 'server', 'compute', 'vm']):
                return 'ec2'
            elif any(term in query_lower for term in ['rds', 'database', 'db', 'mysql', 'postgres']):
                return 'rds'
            elif any(term in query_lower for term in ['storage', 'ebs', 'volume', 'disk']):
                return 'ebs'
            elif any(term in query_lower for term in ['s3', 'bucket', 'object storage']):
                return 's3'
            elif any(term in query_lower for term in ['lambda', 'function', 'serverless']):
                return 'lambda'
            else:
                # Default to EC2 if unclear - most common and safe default
                return 'ec2'
        except Exception:
            # Fallback to EC2 for any parsing errors
            return 'ec2'
    
    def _extract_specifications(self, query: str) -> Dict[str, Any]:
        """Extract explicit specifications from the query"""
        extracted = {}
        
        try:
            # Extract quantity
            quantity_match = re.search(self.patterns['quantity'], query, re.IGNORECASE)
            if quantity_match:
                quantity = int(quantity_match.group(1))
                # Reasonable limits to prevent abuse
                extracted['quantity'] = min(max(quantity, 1), 100)
            
            # Extract instance type
            instance_match = re.search(self.patterns['instance_type'], query, re.IGNORECASE)
            if instance_match:
                extracted['instance_type'] = instance_match.group(1).lower()
            
            # Extract storage size
            storage_match = re.search(self.patterns['storage_size'], query, re.IGNORECASE)
            if storage_match:
                size = int(storage_match.group(1))
                # Convert TB to GB if needed
                if 'tb' in query.lower() or 'tib' in query.lower():
                    size *= 1024
                # Reasonable limits
                size = min(max(size, 1), 16384)  # 1 GB to 16 TB max
                extracted['size_gb'] = size
                extracted['storage_gb'] = size  # For RDS
            
            # Extract duration
            duration_match = re.search(self.patterns['duration'], query, re.IGNORECASE)
            if duration_match:
                duration_num = int(duration_match.group(1))
                duration_text = query[duration_match.end()-10:duration_match.end()].lower()
                
                if 'year' in duration_text or 'yr' in duration_text:
                    extracted['duration_months'] = min(duration_num * 12, 60)  # Max 5 years
                elif 'day' in duration_text:
                    extracted['duration_months'] = max(1, min(duration_num // 30, 60))  # Convert days to months
                else:
                    extracted['duration_months'] = min(max(duration_num, 1), 60)  # 1-60 months
            
            # Extract region
            region_match = re.search(self.patterns['region'], query, re.IGNORECASE)
            if region_match:
                extracted['region'] = region_match.group(1)
            
        except (ValueError, AttributeError) as e:
            # If any parsing fails, continue with empty extracted dict
            # The defaults will be applied later
            pass
        
        return extracted
    
    def _ensure_critical_fields(self, result: Dict[str, Any], resource_type: str):
        """Ensure all critical fields have values, adding defaults if needed"""
        
        critical_fields = {
            'ec2': ['instance_type', 'quantity', 'duration_months', 'region'],
            'rds': ['instance_type', 'engine', 'storage_gb', 'duration_months'],
            'ebs': ['volume_type', 'size_gb', 'duration_months'],
            's3': ['storage_class', 'size_gb', 'duration_months'],
            'lambda': ['memory_mb', 'duration_months', 'executions_per_month']
        }
        
        required_fields = critical_fields.get(resource_type, critical_fields['ec2'])
        defaults = self.default_specs.get(resource_type, self.default_specs['ec2'])
        
        for field in required_fields:
            if field not in result or result[field] is None:
                default_value = defaults.get(field)
                if default_value is not None:
                    result[field] = default_value
                    result['applied_defaults'].append(AppliedDefault(
                        field=field,
                        value=default_value,
                        reason=f"Required field not specified, using minimum viable option"
                    ))
    
    def format_defaults_explanation(self, applied_defaults: List[AppliedDefault], resource_type: str) -> str:
        """Generate user-friendly explanation of applied defaults"""
        
        if not applied_defaults:
            return "✅ All specifications were provided in your query."
        
        explanation = "🔧 **Smart Defaults Applied:**\n\n"
        
        for default in applied_defaults:
            if default.field == 'instance_type':
                explanation += f"• **Instance Type:** {default.value} (smallest available option)\n"
            elif default.field == 'quantity':
                explanation += f"• **Quantity:** {default.value} (minimum viable)\n"
            elif default.field == 'duration_months':
                explanation += f"• **Duration:** {default.value} month(s) (standard period)\n"
            elif default.field == 'region':
                explanation += f"• **Region:** {default.value} (your configured region)\n"
            elif default.field == 'volume_type':
                explanation += f"• **Storage Type:** {default.value} (cost-effective option)\n"
            elif default.field == 'size_gb' or default.field == 'storage_gb':
                explanation += f"• **Storage Size:** {default.value} GB (minimum viable)\n"
            elif default.field == 'engine':
                explanation += f"• **Database Engine:** {default.value} (popular choice)\n"
            else:
                explanation += f"• **{default.field.replace('_', ' ').title()}:** {default.value}\n"
        
        explanation += "\n💡 **To customize, try:**\n"
        
        if resource_type == 'ec2':
            explanation += "• \"2 t3.small instances for 3 months\"\n"
            explanation += "• \"m5.large server in us-west-2 for 6 months\"\n"
        elif resource_type == 'rds':
            explanation += "• \"db.t3.small PostgreSQL database for 6 months\"\n"
            explanation += "• \"MySQL RDS with 100 GB storage for 1 year\"\n"
        elif resource_type == 'ebs':
            explanation += "• \"500 GB GP3 storage for 1 year\"\n"
            explanation += "• \"1 TB IO1 volume for 6 months\"\n"
        
        return explanation
    
    def get_refinement_suggestions(self, resource_type: str, applied_defaults: List[AppliedDefault]) -> List[str]:
        """Generate suggestions for query refinement"""
        
        suggestions = []
        
        # General suggestions based on what was defaulted
        defaulted_fields = [d.field for d in applied_defaults]
        
        if 'instance_type' in defaulted_fields:
            if resource_type == 'ec2':
                suggestions.append("Specify instance type: t3.small, m5.large, c5.xlarge, etc.")
            elif resource_type == 'rds':
                suggestions.append("Specify database instance: db.t3.small, db.m5.large, etc.")
        
        if 'quantity' in defaulted_fields:
            suggestions.append("Specify quantity: '2 instances', '5 servers', etc.")
        
        if 'duration_months' in defaulted_fields:
            suggestions.append("Specify duration: 'for 3 months', 'for 1 year', etc.")
        
        if 'size_gb' in defaulted_fields or 'storage_gb' in defaulted_fields:
            suggestions.append("Specify storage size: '100 GB', '1 TB', etc.")
        
        if 'region' in defaulted_fields:
            suggestions.append("Specify region: 'in us-west-2', 'in eu-west-1', etc.")
        
        # Add resource-specific suggestions
        if resource_type == 'ec2':
            suggestions.append("Compare options: 'cost of t3.micro vs t3.small'")
        elif resource_type == 'rds':
            suggestions.append("Specify engine: 'MySQL', 'PostgreSQL', 'MariaDB'")
        
        return suggestions[:3]  # Limit to top 3 suggestions
    
    def _detect_all_resource_types(self, query: str) -> List[str]:
        """Detect all resource types mentioned in the query"""
        query_lower = query.lower()
        detected = []
        
        # Check for EC2/compute resources
        if any(term in query_lower for term in ['ec2', 'instance', 'server', 'compute', 'vm']):
            detected.append('ec2')
        
        # Check for RDS/database resources
        if any(term in query_lower for term in ['rds', 'database', 'db', 'mysql', 'postgres', 'postgresql']):
            detected.append('rds')
        
        # Check for storage resources
        if any(term in query_lower for term in ['storage', 'ebs', 'volume', 'disk', 'gb', 'tb']):
            # Only add storage if it's not already covered by EC2 (EC2 includes EBS)
            if 'ec2' not in detected:
                detected.append('ebs')
        
        # Check for S3 resources
        if any(term in query_lower for term in ['s3', 'bucket', 'object storage']):
            detected.append('s3')
        
        # Check for Lambda resources
        if any(term in query_lower for term in ['lambda', 'function', 'serverless']):
            detected.append('lambda')
        
        # If no resources detected, default to EC2
        if not detected:
            detected.append('ec2')
        
        return detected
    
    def _generate_multi_resource_notes(self, query: str, detected_resources: List[str]) -> str:
        """Generate notes about multi-resource queries"""
        query_lower = query.lower()
        notes = []
        
        # Check for storage mentioned with EC2
        if 'ec2' in detected_resources and any(term in query_lower for term in ['gb', 'tb', 'storage']):
            storage_match = re.search(r'(\d+)\s*gb', query_lower)
            if storage_match:
                storage_size = storage_match.group(1)
                notes.append(f"Additional EBS storage: ~${int(storage_size) * 0.08:.2f}/month for {storage_size}GB GP3 storage")
        
        # Check for PostgreSQL/RDS mentioned
        if 'rds' in detected_resources:
            postgres_match = re.search(r'(\d+)\s*postgres', query_lower)
            if postgres_match:
                postgres_count = postgres_match.group(1)
                notes.append(f"PostgreSQL databases: Ask separately for '{postgres_count} PostgreSQL databases' to get RDS costs")
            else:
                notes.append("PostgreSQL databases: Ask separately for 'PostgreSQL database costs' to get RDS pricing")
        
        return " | ".join(notes) if notes else ""
    
    def _add_multi_resource_cost_notes(self, result: Dict[str, Any], query: str):
        """Add cost breakdown notes for multi-resource queries"""
        query_lower = query.lower()
        
        # Add storage cost note if storage is mentioned with EC2
        if result['resource_type'] == 'ec2':
            storage_match = re.search(r'(\d+)\s*gb', query_lower)
            if storage_match:
                storage_size = int(storage_match.group(1))
                quantity = result.get('quantity', 1)
                total_storage = storage_size * quantity
                storage_cost = total_storage * 0.08  # GP3 pricing per GB/month
                result['storage_note'] = f"Additional storage cost: ~${storage_cost:.2f}/month for {total_storage}GB GP3 EBS storage ({quantity}x {storage_size}GB)"
        
        # Add database note if PostgreSQL is mentioned
        if any(term in query_lower for term in ['postgres', 'postgresql']):
            postgres_match = re.search(r'(\d+)\s*postgres', query_lower)
            if postgres_match:
                postgres_count = postgres_match.group(1)
                result['database_note'] = f"PostgreSQL costs not included. For {postgres_count} PostgreSQL databases, ask: 'cost of {postgres_count} PostgreSQL databases'"
            else:
                result['database_note'] = "PostgreSQL costs not included. Ask separately: 'cost of PostgreSQL database'"