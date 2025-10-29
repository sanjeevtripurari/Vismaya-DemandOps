"""
MCP Server for Cost Estimation
Provides cost estimation tools for external projects
"""

import asyncio
import json
import logging
from typing import Dict, Any, List
from datetime import datetime

from ..application.dependency_injection import DependencyContainer
from ..core.models import ForecastingContext
from config import Config

logger = logging.getLogger(__name__)


class CostEstimationMCPServer:
    """MCP Server for cost estimation services"""
    
    def __init__(self):
        self.container = DependencyContainer(Config)
        self.container.initialize()
        self.forecasting_ai = None
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize required services"""
        try:
            self.forecasting_ai = self.container.get('forecasting_ai_assistant')
            logger.info("Cost estimation MCP server initialized")
        except Exception as e:
            logger.error(f"Failed to initialize MCP server: {e}")
    
    async def estimate_single_resource_cost(self, resource_type: str, quantity: str, duration: str = "1 month") -> Dict[str, Any]:
        """Estimate cost for a single resource"""
        try:
            if not self.forecasting_ai:
                return {"error": "Forecasting AI not available"}
            
            context = ForecastingContext()
            query = f"cost of {quantity} {resource_type} for {duration}"
            
            response = await self.forecasting_ai.chat_response(query, context)
            
            # Extract cost from response
            import re
            cost_pattern = r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)'
            matches = re.findall(cost_pattern, response)
            
            cost_value = matches[0].replace(',', '') if matches else "0"
            
            return {
                "resource_type": resource_type,
                "quantity": quantity,
                "duration": duration,
                "estimated_cost": f"${cost_value}",
                "full_response": response,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error estimating cost: {e}")
            return {"error": str(e)}
    
    async def estimate_bulk_resources_cost(self, resources: List[Dict[str, str]]) -> Dict[str, Any]:
        """Estimate costs for multiple resources"""
        try:
            results = []
            total_cost = 0
            
            for resource in resources:
                resource_type = resource.get('resource_type', '')
                quantity = resource.get('quantity', '')
                duration = resource.get('duration', '1 month')
                
                estimate = await self.estimate_single_resource_cost(resource_type, quantity, duration)
                results.append(estimate)
                
                # Add to total if no error
                if 'error' not in estimate:
                    cost_str = estimate['estimated_cost'].replace('$', '').replace(',', '')
                    try:
                        total_cost += float(cost_str)
                    except:
                        pass
            
            return {
                "resources": results,
                "total_estimated_cost": f"${total_cost:,.2f}",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error estimating bulk costs: {e}")
            return {"error": str(e)}
    
    async def get_available_resource_types(self) -> Dict[str, Any]:
        """Get list of supported resource types"""
        return {
            "supported_resources": [
                "EC2", "RDS", "S3", "EBS", "Lambda", 
                "CloudFront", "Route53", "ECS", "EKS",
                "VPC", "Load Balancer", "NAT Gateway"
            ],
            "example_queries": [
                "2 t3.medium EC2 instances for 3 months",
                "1 db.r6g.large PostgreSQL database for 6 months",
                "500 GB S3 storage for 1 year",
                "10 Lambda functions for 2 months"
            ]
        }
    
    def get_mcp_tools(self) -> List[Dict[str, Any]]:
        """Get MCP tool definitions"""
        return [
            {
                "name": "estimate_single_resource_cost",
                "description": "Estimate cost for a single AWS resource",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "resource_type": {
                            "type": "string",
                            "description": "Type of AWS resource (EC2, RDS, S3, etc.)"
                        },
                        "quantity": {
                            "type": "string", 
                            "description": "Quantity or size specification (e.g., '2 t3.medium', '100 GB')"
                        },
                        "duration": {
                            "type": "string",
                            "description": "Duration for cost calculation (e.g., '1 month', '6 months')",
                            "default": "1 month"
                        }
                    },
                    "required": ["resource_type", "quantity"]
                }
            },
            {
                "name": "estimate_bulk_resources_cost",
                "description": "Estimate costs for multiple AWS resources",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "resources": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "resource_type": {"type": "string"},
                                    "quantity": {"type": "string"},
                                    "duration": {"type": "string", "default": "1 month"}
                                },
                                "required": ["resource_type", "quantity"]
                            }
                        }
                    },
                    "required": ["resources"]
                }
            },
            {
                "name": "get_available_resource_types",
                "description": "Get list of supported AWS resource types and examples",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]


# MCP Server instance
mcp_server = CostEstimationMCPServer()


async def handle_mcp_call(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP tool calls"""
    try:
        if tool_name == "estimate_single_resource_cost":
            return await mcp_server.estimate_single_resource_cost(
                arguments.get('resource_type', ''),
                arguments.get('quantity', ''),
                arguments.get('duration', '1 month')
            )
        elif tool_name == "estimate_bulk_resources_cost":
            return await mcp_server.estimate_bulk_resources_cost(
                arguments.get('resources', [])
            )
        elif tool_name == "get_available_resource_types":
            return await mcp_server.get_available_resource_types()
        else:
            return {"error": f"Unknown tool: {tool_name}"}
            
    except Exception as e:
        logger.error(f"MCP call error: {e}")
        return {"error": str(e)}