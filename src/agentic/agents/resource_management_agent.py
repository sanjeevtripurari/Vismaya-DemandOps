"""
Resource Management Agent
Autonomous agent for AWS resource optimization, utilization monitoring, and lifecycle management
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

from ..core.base_agent import BaseAgent
from ..core.interfaces import ISpecializedAgent, IStrandsFramework, IMCPServer
from ..core.models import (
    AgentCapability, DecisionProposal, AgentMessage, MessageType,
    SystemEvent, SystemEventType
)


class ResourceManagementAgent(BaseAgent, ISpecializedAgent):
    """
    Specialized agent for AWS resource management with enhanced capabilities:
    - Intelligent resource utilization monitoring
    - Rightsizing recommendations
    - Automated resource lifecycle management with approval workflows
    """
    
    def __init__(
        self,
        strands_framework: Optional[IStrandsFramework] = None,
        mcp_server: Optional[IMCPServer] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        # Define agent capabilities
        capabilities = [
            AgentCapability(
                name="monitor_resource_utilization",
                description="Monitor AWS resource utilization across services",
                input_schema={
                    "type": "object",
                    "properties": {
                        "resource_types": {"type": "array", "items": {"type": "string"}},
                        "time_period": {"type": "string"},
                        "metrics": {"type": "array", "items": {"type": "string"}}
                    }
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "utilization_data": {"type": "object"},
                        "underutilized_resources": {"type": "array"},
                        "overutilized_resources": {"type": "array"}
                    }
                },
                required_permissions=["cloudwatch:GetMetricStatistics", "ec2:DescribeInstances", "rds:DescribeDBInstances"]
            ),
            AgentCapability(
                name="generate_rightsizing_recommendations",
                description="Generate rightsizing recommendations for AWS resources",
                input_schema={
                    "type": "object",
                    "properties": {
                        "utilization_data": {"type": "object"},
                        "cost_data": {"type": "object"},
                        "performance_requirements": {"type": "object"}
                    }
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "recommendations": {"type": "array"},
                        "potential_savings": {"type": "number"},
                        "performance_impact": {"type": "string"}
                    }
                },
                required_permissions=["ec2:DescribeInstanceTypes", "rds:DescribeDBInstanceClasses"]
            )
        ]
        
        # Default configuration
        default_config = {
            "utilization_threshold_low": 20.0,
            "utilization_threshold_high": 80.0,
            "monitoring_frequency_minutes": 30,
            "supported_resource_types": ["ec2", "rds", "ebs", "lambda", "ecs"]
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(
            agent_id="resource_management_agent",
            agent_type="resource_management",
            capabilities=capabilities,
            config=default_config,
            strands_framework=strands_framework,
            mcp_server=mcp_server
        )
        
        # Resource management specific state
        self.resource_inventory = {}
        self.utilization_history = {}
        self.lifecycle_schedules = {}
        
        # Setup specialized handlers
        self._setup_resource_management_handlers()
    
    @property
    def domain(self) -> str:
        """Get agent domain"""
        return "resource_management"
    
    def _setup_resource_management_handlers(self) -> None:
        """Setup resource management specific message and action handlers"""
        self.action_handlers.update({
            "monitor_resource_utilization": self._action_monitor_resource_utilization,
            "generate_rightsizing_recommendations": self._action_generate_rightsizing_recommendations,
            "get_resource_inventory": self._action_get_resource_inventory
        })
    
    async def _agent_specific_initialization(self) -> None:
        """Initialize resource management specific components"""
        try:
            self.logger.info("Initializing resource management agent components")
            await self._initialize_resource_inventory()
            asyncio.create_task(self._resource_monitoring_loop())
            self.logger.info("Resource management agent initialization completed")
        except Exception as e:
            self.logger.error(f"Error in resource management agent initialization: {e}")
            raise
    
    async def analyze_domain_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze resource domain data"""
        try:
            resource_data = data.get("resource_data", {})
            utilization_data = data.get("utilization_data", {})
            
            # Analyze resource utilization
            utilization_analysis = await self._analyze_resource_utilization(utilization_data)
            
            # Identify optimization opportunities
            optimization_opportunities = await self._identify_optimization_opportunities(resource_data, utilization_data)
            
            return {
                "utilization_analysis": utilization_analysis,
                "optimization_opportunities": optimization_opportunities,
                "timestamp": datetime.now().isoformat(),
                "resources_analyzed": len(resource_data)
            }
        except Exception as e:
            self.logger.error(f"Error analyzing resource domain data: {e}")
            raise
    
    async def generate_recommendations(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate resource optimization recommendations"""
        try:
            utilization_data = context.get("utilization_data", {})
            cost_data = context.get("cost_data", {})
            
            recommendations = []
            
            # Generate rightsizing recommendations
            rightsizing_recs = await self._generate_rightsizing_recommendations(utilization_data, cost_data)
            recommendations.extend(rightsizing_recs)
            
            # Generate lifecycle management recommendations
            lifecycle_recs = await self._generate_lifecycle_recommendations(utilization_data)
            recommendations.extend(lifecycle_recs)
            
            # Sort by potential impact and priority
            recommendations.sort(key=lambda x: (x.get("priority_score", 0), x.get("potential_savings", 0)), reverse=True)
            
            return recommendations
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return []
    
    async def create_decision_proposal(self, recommendation: Dict[str, Any]) -> DecisionProposal:
        """Create decision proposal from resource optimization recommendation"""
        try:
            # Calculate impact analysis
            impact_analysis = await self._calculate_resource_recommendation_impact(recommendation)
            
            # Determine required approvers
            required_approvers = self._determine_required_approvers(impact_analysis, recommendation)
            
            # Create proposal
            proposal = DecisionProposal(
                proposal_id=f"resource_opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                title=recommendation.get("title", "Resource Optimization Recommendation"),
                description=recommendation.get("description", ""),
                impact_analysis=impact_analysis,
                recommendations=[recommendation.get("action", "")],
                required_approvers=required_approvers,
                created_by=self.agent_id,
                created_at=datetime.now(),
                status="pending",
                approval_deadline=datetime.now() + timedelta(days=5),
                estimated_cost_impact=impact_analysis.get("cost_savings", 0),
                risk_level=recommendation.get("risk_level", "low")
            )
            
            # Store proposal in memory
            if self.strands_framework:
                await self.strands_framework.store_decision_history(proposal)
            
            return proposal
        except Exception as e:
            self.logger.error(f"Error creating decision proposal: {e}")
            raise
    
    # Action handlers
    async def _action_monitor_resource_utilization(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor resource utilization action"""
        try:
            resource_types = parameters.get("resource_types", self.config.get("supported_resource_types"))
            time_period = parameters.get("time_period", "24_hours")
            
            utilization_data = {}
            underutilized_resources = []
            overutilized_resources = []
            
            for resource_type in resource_types:
                type_data = await self._get_resource_utilization(resource_type, time_period)
                utilization_data[resource_type] = type_data
                
                # Identify under/over utilized resources
                for resource_id, data in type_data.items():
                    avg_utilization = data.get("average_cpu_utilization", 0)
                    
                    if avg_utilization < self.config.get("utilization_threshold_low", 20):
                        underutilized_resources.append({
                            "resource_id": resource_id,
                            "resource_type": resource_type,
                            "utilization": avg_utilization,
                            "recommendation": "Consider downsizing or terminating"
                        })
                    elif avg_utilization > self.config.get("utilization_threshold_high", 80):
                        overutilized_resources.append({
                            "resource_id": resource_id,
                            "resource_type": resource_type,
                            "utilization": avg_utilization,
                            "recommendation": "Consider upsizing or load balancing"
                        })
            
            return {
                "success": True,
                "utilization_data": utilization_data,
                "underutilized_resources": underutilized_resources,
                "overutilized_resources": overutilized_resources
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _action_generate_rightsizing_recommendations(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate rightsizing recommendations action"""
        try:
            utilization_data = parameters.get("utilization_data", {})
            cost_data = parameters.get("cost_data", {})
            
            recommendations = await self._generate_rightsizing_recommendations(utilization_data, cost_data)
            total_savings = sum(rec.get("potential_savings", 0) for rec in recommendations)
            
            return {
                "success": True,
                "recommendations": recommendations,
                "recommendation_count": len(recommendations),
                "total_potential_savings": total_savings
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _action_get_resource_inventory(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get resource inventory action"""
        try:
            resource_types = parameters.get("resource_types", [])
            
            if not resource_types:
                resource_types = self.config.get("supported_resource_types")
            
            inventory = {}
            for resource_type in resource_types:
                inventory[resource_type] = await self._get_resource_inventory_by_type(resource_type)
            
            return {
                "success": True,
                "inventory": inventory,
                "total_resources": sum(len(resources) for resources in inventory.values())
            }
        except Exception as e:
            return {"success": False, "error": str(e)}  
  # Helper methods
    async def _initialize_resource_inventory(self) -> None:
        """Initialize resource inventory from AWS APIs"""
        try:
            # Simulate resource inventory
            self.resource_inventory = {
                "ec2": {
                    "i-1234567890abcdef0": {
                        "instance_type": "t3.medium",
                        "state": "running",
                        "tags": {"Environment": "production", "Application": "web-server"}
                    },
                    "i-0987654321fedcba0": {
                        "instance_type": "t3.large",
                        "state": "running",
                        "tags": {"Environment": "development", "Application": "api-server"}
                    }
                },
                "rds": {
                    "db-instance-1": {
                        "instance_class": "db.t3.micro",
                        "engine": "mysql",
                        "state": "available",
                        "tags": {"Environment": "production", "Application": "database"}
                    }
                }
            }
            self.logger.info("Resource inventory initialized")
        except Exception as e:
            self.logger.error(f"Error initializing resource inventory: {e}")
            raise
    
    async def _resource_monitoring_loop(self) -> None:
        """Resource monitoring background loop"""
        monitoring_frequency = self.config.get("monitoring_frequency_minutes", 30)
        
        while self._state.status != "offline":
            try:
                await asyncio.sleep(monitoring_frequency * 60)
                await self._perform_resource_monitoring()
            except Exception as e:
                self.logger.error(f"Error in resource monitoring loop: {e}")
    
    async def _perform_resource_monitoring(self) -> None:
        """Perform resource monitoring"""
        try:
            self.logger.info("Starting resource monitoring")
            
            for resource_type in self.config.get("supported_resource_types", []):
                utilization_data = await self._get_resource_utilization(resource_type, "1_hour")
                
                # Update utilization history
                for resource_id, data in utilization_data.items():
                    if resource_id not in self.utilization_history:
                        self.utilization_history[resource_id] = []
                    
                    self.utilization_history[resource_id].append({
                        "timestamp": datetime.now().isoformat(),
                        "utilization": data
                    })
                    
                    # Keep only last 24 hours of data
                    self.utilization_history[resource_id] = self.utilization_history[resource_id][-24:]
            
            self.logger.info("Resource monitoring completed")
        except Exception as e:
            self.logger.error(f"Error in resource monitoring: {e}")
    
    async def _get_resource_utilization(self, resource_type: str, time_period: str) -> Dict[str, Any]:
        """Get resource utilization data (simulated)"""
        import random
        
        utilization_data = {}
        resources = self.resource_inventory.get(resource_type, {})
        
        for resource_id in resources:
            utilization_data[resource_id] = {
                "average_cpu_utilization": random.uniform(10, 90),
                "max_cpu_utilization": random.uniform(50, 100),
                "average_memory_utilization": random.uniform(20, 80),
                "network_in": random.uniform(1000, 10000),
                "network_out": random.uniform(1000, 10000)
            }
        
        return utilization_data
    
    async def _analyze_resource_utilization(self, utilization_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze resource utilization patterns"""
        if not utilization_data:
            return {"error": "No utilization data available"}
        
        total_resources = sum(len(resources) for resources in utilization_data.values())
        underutilized_count = 0
        overutilized_count = 0
        
        for resource_type, resources in utilization_data.items():
            for resource_id, data in resources.items():
                cpu_util = data.get("average_cpu_utilization", 0)
                
                if cpu_util < self.config.get("utilization_threshold_low", 20):
                    underutilized_count += 1
                elif cpu_util > self.config.get("utilization_threshold_high", 80):
                    overutilized_count += 1
        
        return {
            "total_resources": total_resources,
            "underutilized_count": underutilized_count,
            "overutilized_count": overutilized_count,
            "utilization_efficiency": ((total_resources - underutilized_count - overutilized_count) / total_resources) * 100 if total_resources > 0 else 0
        }
    
    async def _identify_optimization_opportunities(self, resource_data: Dict[str, Any], utilization_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify resource optimization opportunities"""
        opportunities = []
        
        for resource_type, resources in utilization_data.items():
            for resource_id, data in resources.items():
                cpu_util = data.get("average_cpu_utilization", 0)
                
                if cpu_util < 20:
                    opportunities.append({
                        "type": "rightsizing",
                        "resource_id": resource_id,
                        "resource_type": resource_type,
                        "current_utilization": cpu_util,
                        "recommendation": "Downsize or terminate",
                        "potential_savings": 200.0
                    })
                elif cpu_util > 80:
                    opportunities.append({
                        "type": "scaling",
                        "resource_id": resource_id,
                        "resource_type": resource_type,
                        "current_utilization": cpu_util,
                        "recommendation": "Upsize or add capacity",
                        "potential_cost": 150.0
                    })
        
        return opportunities
    
    async def _generate_rightsizing_recommendations(self, utilization_data: Dict[str, Any], cost_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate rightsizing recommendations"""
        recommendations = []
        
        for resource_type, resources in utilization_data.items():
            for resource_id, data in resources.items():
                cpu_util = data.get("average_cpu_utilization", 0)
                
                if cpu_util < 20:  # Underutilized
                    if resource_type == "ec2":
                        current_type = self.resource_inventory.get("ec2", {}).get(resource_id, {}).get("instance_type", "t3.medium")
                        recommended_type = self._get_smaller_instance_type(current_type)
                        
                        recommendations.append({
                            "title": f"Downsize EC2 Instance {resource_id}",
                            "description": f"Instance is underutilized ({cpu_util:.1f}% CPU). Downsize from {current_type} to {recommended_type}",
                            "action": f"Resize instance from {current_type} to {recommended_type}",
                            "resource_id": resource_id,
                            "resource_type": resource_type,
                            "current_utilization": cpu_util,
                            "potential_savings": 150.0,
                            "risk_level": "low",
                            "priority_score": 7,
                            "implementation_effort": "medium",
                            "category": "rightsizing"
                        })
                
                elif cpu_util > 80:  # Overutilized
                    if resource_type == "ec2":
                        current_type = self.resource_inventory.get("ec2", {}).get(resource_id, {}).get("instance_type", "t3.medium")
                        recommended_type = self._get_larger_instance_type(current_type)
                        
                        recommendations.append({
                            "title": f"Upsize EC2 Instance {resource_id}",
                            "description": f"Instance is overutilized ({cpu_util:.1f}% CPU). Upsize from {current_type} to {recommended_type}",
                            "action": f"Resize instance from {current_type} to {recommended_type}",
                            "resource_id": resource_id,
                            "resource_type": resource_type,
                            "current_utilization": cpu_util,
                            "potential_cost": 100.0,
                            "risk_level": "medium",
                            "priority_score": 8,
                            "implementation_effort": "medium",
                            "category": "performance"
                        })
        
        return recommendations
    
    async def _generate_lifecycle_recommendations(self, utilization_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate lifecycle management recommendations"""
        recommendations = []
        
        # Check for development resources that could be scheduled
        for resource_type, resources in self.resource_inventory.items():
            for resource_id, resource_info in resources.items():
                tags = resource_info.get("tags", {})
                environment = tags.get("Environment", "").lower()
                
                if environment in ["development", "staging", "test"]:
                    recommendations.append({
                        "title": f"Schedule {resource_type.upper()} Resource {resource_id}",
                        "description": f"Non-production resource can be scheduled to reduce costs",
                        "action": f"Implement start/stop schedule for {resource_id}",
                        "resource_id": resource_id,
                        "resource_type": resource_type,
                        "potential_savings": 300.0,
                        "risk_level": "low",
                        "priority_score": 6,
                        "implementation_effort": "low",
                        "category": "lifecycle"
                    })
        
        return recommendations
    
    def _get_smaller_instance_type(self, current_type: str) -> str:
        """Get smaller instance type for rightsizing"""
        size_map = {
            "t3.large": "t3.medium",
            "t3.medium": "t3.small",
            "t3.small": "t3.micro",
            "m5.large": "m5.medium",
            "m5.medium": "t3.medium"
        }
        return size_map.get(current_type, current_type)
    
    def _get_larger_instance_type(self, current_type: str) -> str:
        """Get larger instance type for rightsizing"""
        size_map = {
            "t3.micro": "t3.small",
            "t3.small": "t3.medium",
            "t3.medium": "t3.large",
            "t3.large": "t3.xlarge",
            "m5.medium": "m5.large"
        }
        return size_map.get(current_type, current_type)
    
    async def _calculate_resource_recommendation_impact(self, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate impact analysis for resource recommendation"""
        potential_savings = recommendation.get("potential_savings", 0)
        potential_cost = recommendation.get("potential_cost", 0)
        risk_level = recommendation.get("risk_level", "low")
        
        net_impact = potential_savings - potential_cost
        
        return {
            "cost_savings": net_impact,
            "monthly_impact": net_impact,
            "annual_impact": net_impact * 12,
            "risk_assessment": risk_level,
            "affected_resources": [recommendation.get("resource_id", "unknown")],
            "performance_impact": "minimal" if risk_level == "low" else "moderate",
            "implementation_timeline": "1-3 days",
            "rollback_plan": "Available" if risk_level == "low" else "Complex",
            "success_metrics": [
                f"Achieve ${net_impact} monthly impact",
                "Maintain resource performance",
                "No service disruptions"
            ]
        }
    
    def _determine_required_approvers(self, impact_analysis: Dict[str, Any], recommendation: Dict[str, Any]) -> List[str]:
        """Determine required approvers based on impact and risk"""
        cost_impact = abs(impact_analysis.get("cost_savings", 0))
        risk_level = impact_analysis.get("risk_assessment", "low")
        
        approvers = []
        
        if cost_impact > 500 or risk_level == "high":
            approvers.extend(["cto", "finops_lead"])
        elif cost_impact > 200 or risk_level == "medium":
            approvers.append("finops_lead")
        else:
            approvers.append("devops_engineer")
        
        return approvers
    
    async def _get_resource_inventory_by_type(self, resource_type: str) -> Dict[str, Any]:
        """Get resource inventory by type"""
        return self.resource_inventory.get(resource_type, {})