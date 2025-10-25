"""
API Cost Tracker Service
Tracks and estimates costs for AWS API calls made by the application
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import json

logger = logging.getLogger(__name__)


@dataclass
class APICall:
    """Represents an API call with cost information"""
    service: str
    operation: str
    timestamp: datetime
    estimated_cost: float
    details: Dict = field(default_factory=dict)


@dataclass
class ServiceUsage:
    """Usage statistics for a service"""
    service_name: str
    total_calls: int
    total_cost: float
    operations: Dict[str, int] = field(default_factory=dict)
    details: Dict = field(default_factory=dict)


class APICostTracker:
    """Tracks API costs for the application"""
    
    # AWS API Pricing (as of 2024/2025 - approximate)
    COST_EXPLORER_PRICING = {
        'GetCostAndUsage': 0.01,  # $0.01 per request
        'GetUsageReport': 0.01,
        'GetDimensionValues': 0.01,
        'GetReservationCoverage': 0.01,
        'GetReservationPurchaseRecommendation': 0.01,
        'GetReservationUtilization': 0.01,
    }
    
    BEDROCK_PRICING = {
        # Claude 3 Haiku pricing (per 1K tokens)
        'us.anthropic.claude-3-haiku-20240307-v1:0': {
            'input_tokens': 0.00025,   # $0.25 per 1M input tokens
            'output_tokens': 0.00125,  # $1.25 per 1M output tokens
        }
    }
    
    EC2_PRICING = {
        'DescribeInstances': 0.0,  # Free
        'DescribeVolumes': 0.0,    # Free
        'DescribeImages': 0.0,     # Free
    }
    
    RDS_PRICING = {
        'DescribeDBInstances': 0.0,  # Free
        'DescribeDBClusters': 0.0,   # Free
    }
    
    def __init__(self):
        self.api_calls: List[APICall] = []
        self.session_start = datetime.now()
    
    def track_cost_explorer_call(self, operation: str, details: Dict = None) -> float:
        """Track a Cost Explorer API call"""
        cost = self.COST_EXPLORER_PRICING.get(operation, 0.01)
        
        api_call = APICall(
            service='Cost Explorer',
            operation=operation,
            timestamp=datetime.now(),
            estimated_cost=cost,
            details=details or {}
        )
        
        self.api_calls.append(api_call)
        logger.info(f"💰 Cost Explorer API: {operation} - ${cost:.4f}")
        return cost
    
    def track_bedrock_call(self, model_id: str, input_tokens: int, output_tokens: int, 
                          operation: str = 'InvokeModel') -> float:
        """Track a Bedrock API call with token usage"""
        pricing = self.BEDROCK_PRICING.get(model_id, {
            'input_tokens': 0.00025,
            'output_tokens': 0.00125
        })
        
        input_cost = (input_tokens / 1000) * pricing['input_tokens']
        output_cost = (output_tokens / 1000) * pricing['output_tokens']
        total_cost = input_cost + output_cost
        
        api_call = APICall(
            service='Bedrock',
            operation=operation,
            timestamp=datetime.now(),
            estimated_cost=total_cost,
            details={
                'model_id': model_id,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'input_cost': input_cost,
                'output_cost': output_cost
            }
        )
        
        self.api_calls.append(api_call)
        logger.info(f"🤖 Bedrock API: {operation} - ${total_cost:.6f} ({input_tokens}+{output_tokens} tokens)")
        return total_cost
    
    def track_ec2_call(self, operation: str, instance_count: int = 0) -> float:
        """Track an EC2 API call"""
        cost = self.EC2_PRICING.get(operation, 0.0)
        
        api_call = APICall(
            service='EC2',
            operation=operation,
            timestamp=datetime.now(),
            estimated_cost=cost,
            details={'instance_count': instance_count}
        )
        
        self.api_calls.append(api_call)
        if cost > 0:
            logger.info(f"🖥️ EC2 API: {operation} - ${cost:.4f}")
        return cost
    
    def track_rds_call(self, operation: str, db_count: int = 0) -> float:
        """Track an RDS API call"""
        cost = self.RDS_PRICING.get(operation, 0.0)
        
        api_call = APICall(
            service='RDS',
            operation=operation,
            timestamp=datetime.now(),
            estimated_cost=cost,
            details={'db_count': db_count}
        )
        
        self.api_calls.append(api_call)
        if cost > 0:
            logger.info(f"🗄️ RDS API: {operation} - ${cost:.4f}")
        return cost
    
    def get_session_summary(self) -> Dict:
        """Get summary of API costs for current session"""
        if not self.api_calls:
            return {
                'total_cost': 0.0,
                'total_calls': 0,
                'services': {},
                'session_duration': 0
            }
        
        services = {}
        total_cost = 0.0
        
        for call in self.api_calls:
            if call.service not in services:
                services[call.service] = ServiceUsage(
                    service_name=call.service,
                    total_calls=0,
                    total_cost=0.0
                )
            
            service = services[call.service]
            service.total_calls += 1
            service.total_cost += call.estimated_cost
            
            if call.operation not in service.operations:
                service.operations[call.operation] = 0
            service.operations[call.operation] += 1
            
            # Add service-specific details
            if call.service == 'Bedrock' and 'input_tokens' in call.details:
                if 'total_input_tokens' not in service.details:
                    service.details['total_input_tokens'] = 0
                    service.details['total_output_tokens'] = 0
                service.details['total_input_tokens'] += call.details['input_tokens']
                service.details['total_output_tokens'] += call.details['output_tokens']
            
            total_cost += call.estimated_cost
        
        session_duration = (datetime.now() - self.session_start).total_seconds()
        
        return {
            'total_cost': total_cost,
            'total_calls': len(self.api_calls),
            'services': {name: service for name, service in services.items()},
            'session_duration': session_duration,
            'session_start': self.session_start,
            'cost_per_minute': (total_cost / (session_duration / 60)) if session_duration > 0 else 0
        }
    
    def get_detailed_breakdown(self) -> List[Dict]:
        """Get detailed breakdown of all API calls"""
        return [
            {
                'timestamp': call.timestamp.isoformat(),
                'service': call.service,
                'operation': call.operation,
                'cost': call.estimated_cost,
                'details': call.details
            }
            for call in self.api_calls
        ]
    
    def estimate_monthly_cost(self, daily_usage_multiplier: float = 1.0) -> Dict:
        """Estimate monthly costs based on current usage patterns"""
        summary = self.get_session_summary()
        
        if summary['session_duration'] == 0:
            return {'estimated_monthly_cost': 0.0, 'breakdown': {}}
        
        # Calculate cost per hour
        cost_per_hour = summary['total_cost'] / (summary['session_duration'] / 3600)
        
        # Estimate daily cost (assuming similar usage pattern)
        daily_cost = cost_per_hour * 24 * daily_usage_multiplier
        
        # Estimate monthly cost (30 days)
        monthly_cost = daily_cost * 30
        
        # Service breakdown
        service_breakdown = {}
        for service_name, service in summary['services'].items():
            service_hourly = service.total_cost / (summary['session_duration'] / 3600)
            service_monthly = service_hourly * 24 * 30 * daily_usage_multiplier
            service_breakdown[service_name] = {
                'monthly_cost': service_monthly,
                'calls_per_hour': service.total_calls / (summary['session_duration'] / 3600),
                'estimated_monthly_calls': service.total_calls * 24 * 30 * daily_usage_multiplier
            }
        
        return {
            'estimated_monthly_cost': monthly_cost,
            'estimated_daily_cost': daily_cost,
            'cost_per_hour': cost_per_hour,
            'breakdown': service_breakdown,
            'assumptions': {
                'daily_usage_multiplier': daily_usage_multiplier,
                'hours_per_day': 24,
                'days_per_month': 30
            }
        }
    
    def reset_session(self):
        """Reset the tracking for a new session"""
        self.api_calls.clear()
        self.session_start = datetime.now()
        logger.info("🔄 API cost tracking session reset")


# Global instance
api_cost_tracker = APICostTracker()