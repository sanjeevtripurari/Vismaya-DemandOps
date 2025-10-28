"""
Agent Strand for Cost Estimation
Provides multi-agent workflow support for cost estimation
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime

from ..application.dependency_injection import DependencyContainer
from ..core.models import ForecastingContext
from config import Config

logger = logging.getLogger(__name__)


class CostEstimationStrand:
    """Agent strand for cost estimation workflows"""
    
    def __init__(self):
        self.container = DependencyContainer(Config)
        self.container.initialize()
        self.forecasting_ai = None
        self.strand_id = f"cost_estimation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize required services"""
        try:
            self.forecasting_ai = self.container.get('forecasting_ai_assistant')
            logger.info(f"Cost estimation strand {self.strand_id} initialized")
        except Exception as e:
            logger.error(f"Failed to initialize strand: {e}")
    
    async def process_cost_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a cost estimation request through the strand"""
        try:
            request_type = request.get('type', 'single')
            
            if request_type == 'single':
                return await self._process_single_resource(request)
            elif request_type == 'bulk':
                return await self._process_bulk_resources(request)
            elif request_type == 'comparison':
                return await self._process_resource_comparison(request)
            else:
                return {"error": f"Unknown request type: {request_type}"}
                
        except Exception as e:
            logger.error(f"Error processing cost request: {e}")
            return {"error": str(e)}
    
    async def _process_single_resource(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process single resource cost estimation"""
        try:
            resource_type = request.get('resource_type', '')
            quantity = request.get('quantity', '')
            duration = request.get('duration', '1 month')
            
            context = ForecastingContext()
            query = f"cost of {quantity} {resource_type} for {duration}"
            
            response = await self.forecasting_ai.chat_response(query, context)
            
            return {
                "strand_id": self.strand_id,
                "request_type": "single",
                "resource_type": resource_type,
                "quantity": quantity,
                "duration": duration,
                "response": response,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _process_bulk_resources(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process bulk resource cost estimation"""
        try:
            resources = request.get('resources', [])
            results = []
            
            # Process resources in parallel for efficiency
            tasks = []
            for resource in resources:
                task = self._process_single_resource(resource)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            return {
                "strand_id": self.strand_id,
                "request_type": "bulk",
                "resource_count": len(resources),
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _process_resource_comparison(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process resource comparison request"""
        try:
            resources = request.get('resources', [])
            comparison_results = []
            
            for resource in resources:
                result = await self._process_single_resource(resource)
                comparison_results.append(result)
            
            return {
                "strand_id": self.strand_id,
                "request_type": "comparison",
                "comparison_results": comparison_results,
                "recommendation": self._generate_comparison_recommendation(comparison_results),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _generate_comparison_recommendation(self, results: List[Dict[str, Any]]) -> str:
        """Generate recommendation based on comparison results"""
        try:
            # Extract costs from responses
            costs = []
            for result in results:
                response = result.get('response', '')
                import re
                cost_pattern = r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)'
                matches = re.findall(cost_pattern, response)
                if matches:
                    cost_value = float(matches[0].replace(',', ''))
                    costs.append((result.get('resource_type', ''), cost_value))
            
            if costs:
                # Find cheapest option
                cheapest = min(costs, key=lambda x: x[1])
                return f"Most cost-effective option: {cheapest[0]} at ${cheapest[1]:,.2f}"
            else:
                return "Unable to determine cost comparison"
                
        except Exception as e:
            return f"Error generating recommendation: {str(e)}"
    
    def get_strand_info(self) -> Dict[str, Any]:
        """Get information about this strand"""
        return {
            "strand_id": self.strand_id,
            "type": "cost_estimation",
            "capabilities": [
                "single_resource_estimation",
                "bulk_resource_estimation", 
                "resource_comparison",
                "cost_optimization_recommendations"
            ],
            "supported_resources": [
                "EC2", "RDS", "S3", "EBS", "Lambda",
                "CloudFront", "Route53", "ECS", "EKS"
            ]
        }


# Global strand registry
_strand_registry = {}


def create_cost_estimation_strand() -> CostEstimationStrand:
    """Create a new cost estimation strand"""
    strand = CostEstimationStrand()
    _strand_registry[strand.strand_id] = strand
    return strand


def get_strand(strand_id: str) -> CostEstimationStrand:
    """Get existing strand by ID"""
    return _strand_registry.get(strand_id)


def list_active_strands() -> List[str]:
    """List all active strand IDs"""
    return list(_strand_registry.keys())


async def process_strand_request(strand_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
    """Process request through specific strand"""
    strand = get_strand(strand_id)
    if not strand:
        return {"error": f"Strand {strand_id} not found"}
    
    return await strand.process_cost_request(request)