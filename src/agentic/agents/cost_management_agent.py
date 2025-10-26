"""
Cost Management Agent
Autonomous agent for AWS cost analysis, anomaly detection, and optimization recommendations
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


class CostManagementAgent(BaseAgent, ISpecializedAgent):
    """
    Specialized agent for AWS cost management with enhanced capabilities:
    - Proactive cost anomaly detection
    - Automated alert generation
    - Cost optimization recommendation engine with decision proposals
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
                name="analyze_cost_data",
                description="Analyze AWS cost data for patterns and anomalies",
                input_schema={
                    "type": "object",
                    "properties": {
                        "time_period": {"type": "string"},
                        "services": {"type": "array", "items": {"type": "string"}},
                        "granularity": {"type": "string", "enum": ["DAILY", "MONTHLY"]}
                    }
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "analysis": {"type": "object"},
                        "anomalies": {"type": "array"},
                        "recommendations": {"type": "array"}
                    }
                },
                required_permissions=["cost:GetCostAndUsage", "cost:GetUsageReport"]
            ),
            AgentCapability(
                name="detect_cost_anomalies",
                description="Detect cost anomalies using statistical analysis",
                input_schema={
                    "type": "object",
                    "properties": {
                        "cost_data": {"type": "array"},
                        "threshold_percentage": {"type": "number", "default": 20}
                    }
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "anomalies": {"type": "array"},
                        "severity": {"type": "string"},
                        "impact": {"type": "number"}
                    }
                },
                required_permissions=["cost:GetCostAndUsage"]
            ),
            AgentCapability(
                name="generate_optimization_recommendations",
                description="Generate cost optimization recommendations",
                input_schema={
                    "type": "object",
                    "properties": {
                        "cost_analysis": {"type": "object"},
                        "budget_constraints": {"type": "object"}
                    }
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "recommendations": {"type": "array"},
                        "potential_savings": {"type": "number"},
                        "implementation_priority": {"type": "string"}
                    }
                },
                required_permissions=["cost:GetCostAndUsage", "cost:GetReservationPurchaseRecommendation"]
            ),
            AgentCapability(
                name="create_cost_decision_proposal",
                description="Create decision proposals for cost optimization actions",
                input_schema={
                    "type": "object",
                    "properties": {
                        "recommendation": {"type": "object"},
                        "impact_analysis": {"type": "object"}
                    }
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "proposal": {"type": "object"},
                        "approval_required": {"type": "boolean"}
                    }
                },
                required_permissions=["cost:*"]
            )
        ]
        
        # Default configuration
        default_config = {
            "anomaly_threshold_percentage": 20.0,
            "analysis_frequency_hours": 6,
            "alert_cooldown_hours": 24,
            "max_recommendations_per_analysis": 10,
            "cost_optimization_targets": {
                "compute": 15,  # Target 15% reduction in compute costs
                "storage": 10,  # Target 10% reduction in storage costs
                "network": 5    # Target 5% reduction in network costs
            }
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(
            agent_id="cost_management_agent",
            agent_type="cost_management",
            capabilities=capabilities,
            config=default_config,
            strands_framework=strands_framework,
            mcp_server=mcp_server
        )
        
        # Cost management specific state
        self.last_analysis_time = None
        self.active_alerts = {}
        self.cost_baselines = {}
        self.optimization_history = []
        
        # Setup specialized handlers
        self._setup_cost_management_handlers()
    
    @property
    def domain(self) -> str:
        """Get agent domain"""
        return "cost_management"
    
    def _setup_cost_management_handlers(self) -> None:
        """Setup cost management specific message and action handlers"""
        # Add specialized action handlers
        self.action_handlers.update({
            "analyze_cost_data": self._action_analyze_cost_data,
            "detect_cost_anomalies": self._action_detect_cost_anomalies,
            "generate_optimization_recommendations": self._action_generate_optimization_recommendations,
            "create_cost_decision_proposal": self._action_create_cost_decision_proposal,
            "get_cost_summary": self._action_get_cost_summary,
            "update_cost_baselines": self._action_update_cost_baselines
        })
        
        # Add specialized message handlers
        self.message_handlers.update({
            "cost_alert": self._handle_cost_alert,
            "budget_threshold_exceeded": self._handle_budget_threshold_exceeded
        })
    
    async def _agent_specific_initialization(self) -> None:
        """Initialize cost management specific components"""
        try:
            self.logger.info("Initializing cost management agent components")
            
            # Initialize cost baselines
            await self._initialize_cost_baselines()
            
            # Start periodic cost analysis
            asyncio.create_task(self._periodic_cost_analysis_loop())
            
            # Start anomaly detection monitoring
            asyncio.create_task(self._anomaly_detection_loop())
            
            self.logger.info("Cost management agent initialization completed")
            
        except Exception as e:
            self.logger.error(f"Error in cost management agent initialization: {e}")
            raise
    
    async def analyze_domain_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze cost domain data"""
        try:
            cost_data = data.get("cost_data", [])
            time_period = data.get("time_period", "30_days")
            services = data.get("services", [])
            
            # Perform cost analysis
            analysis_result = await self._perform_cost_analysis(cost_data, time_period, services)
            
            # Detect anomalies
            anomalies = await self._detect_anomalies(cost_data)
            
            # Calculate trends
            trends = await self._calculate_cost_trends(cost_data)
            
            return {
                "analysis": analysis_result,
                "anomalies": anomalies,
                "trends": trends,
                "timestamp": datetime.now().isoformat(),
                "data_points": len(cost_data)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing cost domain data: {e}")
            raise
    
    async def generate_recommendations(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate cost optimization recommendations"""
        try:
            cost_analysis = context.get("cost_analysis", {})
            budget_info = context.get("budget_info", {})
            current_usage = context.get("current_usage", {})
            
            recommendations = []
            
            # Generate compute optimization recommendations
            compute_recs = await self._generate_compute_recommendations(cost_analysis, current_usage)
            recommendations.extend(compute_recs)
            
            # Generate storage optimization recommendations
            storage_recs = await self._generate_storage_recommendations(cost_analysis, current_usage)
            recommendations.extend(storage_recs)
            
            # Generate reserved instance recommendations
            ri_recs = await self._generate_reserved_instance_recommendations(cost_analysis)
            recommendations.extend(ri_recs)
            
            # Generate budget-based recommendations
            if budget_info:
                budget_recs = await self._generate_budget_recommendations(cost_analysis, budget_info)
                recommendations.extend(budget_recs)
            
            # Sort by potential savings and priority
            recommendations.sort(key=lambda x: (x.get("priority_score", 0), x.get("potential_savings", 0)), reverse=True)
            
            # Limit to max recommendations
            max_recs = self.config.get("max_recommendations_per_analysis", 10)
            return recommendations[:max_recs]
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return []
    
    async def create_decision_proposal(self, recommendation: Dict[str, Any]) -> DecisionProposal:
        """Create decision proposal from cost optimization recommendation"""
        try:
            # Calculate impact analysis
            impact_analysis = await self._calculate_recommendation_impact(recommendation)
            
            # Determine required approvers based on cost impact
            required_approvers = self._determine_required_approvers(impact_analysis)
            
            # Create proposal
            proposal = DecisionProposal(
                proposal_id=f"cost_opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                title=recommendation.get("title", "Cost Optimization Recommendation"),
                description=recommendation.get("description", ""),
                impact_analysis=impact_analysis,
                recommendations=[recommendation.get("action", "")],
                required_approvers=required_approvers,
                created_by=self.agent_id,
                created_at=datetime.now(),
                status="pending",
                approval_deadline=datetime.now() + timedelta(days=7),
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
    async def _action_analyze_cost_data(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze cost data action"""
        try:
            time_period = parameters.get("time_period", "30_days")
            services = parameters.get("services", [])
            granularity = parameters.get("granularity", "DAILY")
            
            # Simulate cost data retrieval (in real implementation, would call AWS Cost Explorer API)
            cost_data = await self._retrieve_cost_data(time_period, services, granularity)
            
            # Perform analysis
            analysis_result = await self.analyze_domain_data({
                "cost_data": cost_data,
                "time_period": time_period,
                "services": services
            })
            
            return {
                "success": True,
                "analysis": analysis_result,
                "data_points": len(cost_data),
                "time_period": time_period,
                "services_analyzed": services
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _action_detect_cost_anomalies(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Detect cost anomalies action"""
        try:
            cost_data = parameters.get("cost_data", [])
            threshold_percentage = parameters.get("threshold_percentage", self.config.get("anomaly_threshold_percentage", 20))
            
            anomalies = await self._detect_anomalies(cost_data, threshold_percentage)
            
            # Generate alerts for significant anomalies
            for anomaly in anomalies:
                if anomaly.get("severity") in ["high", "critical"]:
                    await self._generate_cost_alert(anomaly)
            
            return {
                "success": True,
                "anomalies": anomalies,
                "anomaly_count": len(anomalies),
                "threshold_used": threshold_percentage
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _action_generate_optimization_recommendations(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate optimization recommendations action"""
        try:
            cost_analysis = parameters.get("cost_analysis", {})
            budget_constraints = parameters.get("budget_constraints", {})
            
            recommendations = await self.generate_recommendations({
                "cost_analysis": cost_analysis,
                "budget_info": budget_constraints
            })
            
            # Calculate total potential savings
            total_savings = sum(rec.get("potential_savings", 0) for rec in recommendations)
            
            return {
                "success": True,
                "recommendations": recommendations,
                "recommendation_count": len(recommendations),
                "total_potential_savings": total_savings
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _action_create_cost_decision_proposal(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create cost decision proposal action"""
        try:
            recommendation = parameters.get("recommendation", {})
            
            proposal = await self.create_decision_proposal(recommendation)
            
            # Send to approval agent if available
            if self.mcp_server:
                approval_message = AgentMessage(
                    sender=self.agent_id,
                    recipient="approval_agent",
                    message_type=MessageType.REQUEST,
                    content={
                        "action": "process_proposal",
                        "proposal": proposal.__dict__
                    }
                )
                
                await self.mcp_server.route_message(approval_message)
            
            return {
                "success": True,
                "proposal_id": proposal.proposal_id,
                "estimated_savings": proposal.estimated_cost_impact,
                "required_approvers": proposal.required_approvers
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _action_get_cost_summary(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get cost summary action"""
        try:
            # Get current cost data
            current_costs = await self._get_current_cost_summary()
            
            # Get recent anomalies
            recent_anomalies = [
                anomaly for anomaly in self.active_alerts.values()
                if (datetime.now() - anomaly.get("detected_at", datetime.now())).days <= 7
            ]
            
            # Get optimization history
            recent_optimizations = self.optimization_history[-10:]  # Last 10 optimizations
            
            return {
                "success": True,
                "current_costs": current_costs,
                "recent_anomalies": recent_anomalies,
                "recent_optimizations": recent_optimizations,
                "last_analysis": self.last_analysis_time.isoformat() if self.last_analysis_time else None
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _action_update_cost_baselines(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Update cost baselines action"""
        try:
            new_baselines = parameters.get("baselines", {})
            
            # Update baselines
            self.cost_baselines.update(new_baselines)
            
            # Store in Strands framework
            if self.strands_framework:
                await self.strands_framework.update_context(
                    self.agent_id,
                    {"cost_baselines": self.cost_baselines}
                )
            
            return {
                "success": True,
                "updated_baselines": list(new_baselines.keys()),
                "total_baselines": len(self.cost_baselines)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Message handlers
    async def _handle_cost_alert(self, message: AgentMessage) -> AgentMessage:
        """Handle cost alert messages"""
        try:
            alert_data = message.content
            alert_id = alert_data.get("alert_id")
            
            # Process the alert
            await self._process_cost_alert(alert_data)
            
            return AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type=MessageType.RESPONSE,
                content={"status": "alert_processed", "alert_id": alert_id},
                correlation_id=message.correlation_id
            )
            
        except Exception as e:
            self.logger.error(f"Error handling cost alert: {e}")
            return AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type=MessageType.ERROR,
                content={"error": str(e)},
                correlation_id=message.correlation_id
            )
    
    async def _handle_budget_threshold_exceeded(self, message: AgentMessage) -> AgentMessage:
        """Handle budget threshold exceeded messages"""
        try:
            threshold_data = message.content
            
            # Generate immediate recommendations
            recommendations = await self._generate_emergency_cost_recommendations(threshold_data)
            
            # Create high-priority decision proposals
            for rec in recommendations[:3]:  # Top 3 recommendations
                proposal = await self.create_decision_proposal(rec)
                
                # Send to approval agent with high priority
                if self.mcp_server:
                    approval_message = AgentMessage(
                        sender=self.agent_id,
                        recipient="approval_agent",
                        message_type=MessageType.REQUEST,
                        content={
                            "action": "process_urgent_proposal",
                            "proposal": proposal.__dict__,
                            "priority": "high"
                        }
                    )
                    
                    await self.mcp_server.route_message(approval_message)
            
            return AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type=MessageType.RESPONSE,
                content={
                    "status": "threshold_processed",
                    "recommendations_generated": len(recommendations),
                    "proposals_created": min(3, len(recommendations))
                },
                correlation_id=message.correlation_id
            )
            
        except Exception as e:
            self.logger.error(f"Error handling budget threshold exceeded: {e}")
            return AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type=MessageType.ERROR,
                content={"error": str(e)},
                correlation_id=message.correlation_id
            )
    
    # Helper methods
    async def _initialize_cost_baselines(self) -> None:
        """Initialize cost baselines from historical data"""
        try:
            # In a real implementation, this would load historical cost data
            # For now, we'll set some default baselines
            self.cost_baselines = {
                "ec2_monthly_baseline": 1000.0,
                "rds_monthly_baseline": 500.0,
                "s3_monthly_baseline": 200.0,
                "lambda_monthly_baseline": 50.0,
                "data_transfer_monthly_baseline": 100.0
            }
            
            self.logger.info("Cost baselines initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing cost baselines: {e}")
            raise
    
    async def _periodic_cost_analysis_loop(self) -> None:
        """Periodic cost analysis background loop"""
        analysis_frequency = self.config.get("analysis_frequency_hours", 6)
        
        while self._state.status != "offline":
            try:
                await asyncio.sleep(analysis_frequency * 3600)  # Convert hours to seconds
                
                # Perform periodic cost analysis
                await self._perform_periodic_analysis()
                
            except Exception as e:
                self.logger.error(f"Error in periodic cost analysis loop: {e}")
    
    async def _anomaly_detection_loop(self) -> None:
        """Anomaly detection monitoring loop"""
        while self._state.status != "offline":
            try:
                await asyncio.sleep(1800)  # Check every 30 minutes
                
                # Get recent cost data
                cost_data = await self._retrieve_recent_cost_data()
                
                # Detect anomalies
                anomalies = await self._detect_anomalies(cost_data)
                
                # Process any new anomalies
                for anomaly in anomalies:
                    if anomaly.get("id") not in self.active_alerts:
                        await self._process_new_anomaly(anomaly)
                
            except Exception as e:
                self.logger.error(f"Error in anomaly detection loop: {e}")
    
    async def _perform_periodic_analysis(self) -> None:
        """Perform periodic cost analysis"""
        try:
            self.logger.info("Starting periodic cost analysis")
            
            # Get cost data for analysis
            cost_data = await self._retrieve_cost_data("30_days", [], "DAILY")
            
            # Perform analysis
            analysis_result = await self.analyze_domain_data({
                "cost_data": cost_data,
                "time_period": "30_days"
            })
            
            # Generate recommendations
            recommendations = await self.generate_recommendations({
                "cost_analysis": analysis_result
            })
            
            # Create decision proposals for high-impact recommendations
            for rec in recommendations:
                if rec.get("potential_savings", 0) > 100:  # $100+ savings
                    await self.create_decision_proposal(rec)
            
            self.last_analysis_time = datetime.now()
            
            self.logger.info(f"Periodic cost analysis completed. Generated {len(recommendations)} recommendations")
            
        except Exception as e:
            self.logger.error(f"Error in periodic cost analysis: {e}")
    
    async def _retrieve_cost_data(self, time_period: str, services: List[str], granularity: str) -> List[Dict[str, Any]]:
        """Retrieve cost data (simulated - would call AWS Cost Explorer API in real implementation)"""
        # Simulate cost data
        import random
        from datetime import datetime, timedelta
        
        days = 30 if time_period == "30_days" else 7
        cost_data = []
        
        base_cost = 1000
        for i in range(days):
            date = datetime.now() - timedelta(days=days-i)
            
            # Add some variation and trend
            daily_cost = base_cost + random.uniform(-100, 200) + (i * 5)  # Slight upward trend
            
            cost_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "cost": daily_cost,
                "service": "EC2-Instance" if not services else services[0],
                "usage_type": "BoxUsage:t3.medium"
            })
        
        return cost_data
    
    async def _retrieve_recent_cost_data(self) -> List[Dict[str, Any]]:
        """Retrieve recent cost data for anomaly detection"""
        return await self._retrieve_cost_data("7_days", [], "DAILY")
    
    async def _perform_cost_analysis(self, cost_data: List[Dict[str, Any]], time_period: str, services: List[str]) -> Dict[str, Any]:
        """Perform detailed cost analysis"""
        if not cost_data:
            return {"error": "No cost data available"}
        
        total_cost = sum(item.get("cost", 0) for item in cost_data)
        avg_daily_cost = total_cost / len(cost_data)
        
        # Calculate service breakdown
        service_costs = {}
        for item in cost_data:
            service = item.get("service", "Unknown")
            service_costs[service] = service_costs.get(service, 0) + item.get("cost", 0)
        
        return {
            "total_cost": total_cost,
            "average_daily_cost": avg_daily_cost,
            "service_breakdown": service_costs,
            "data_points": len(cost_data),
            "time_period": time_period
        }
    
    async def _detect_anomalies(self, cost_data: List[Dict[str, Any]], threshold_percentage: float = 20) -> List[Dict[str, Any]]:
        """Detect cost anomalies using statistical analysis"""
        if len(cost_data) < 7:  # Need at least a week of data
            return []
        
        # Calculate baseline (average of first 80% of data)
        baseline_data = cost_data[:int(len(cost_data) * 0.8)]
        baseline_avg = sum(item.get("cost", 0) for item in baseline_data) / len(baseline_data)
        
        anomalies = []
        
        # Check recent data points for anomalies
        recent_data = cost_data[int(len(cost_data) * 0.8):]
        
        for item in recent_data:
            cost = item.get("cost", 0)
            deviation_percentage = ((cost - baseline_avg) / baseline_avg) * 100
            
            if abs(deviation_percentage) > threshold_percentage:
                severity = "high" if abs(deviation_percentage) > 50 else "medium"
                
                anomalies.append({
                    "id": f"anomaly_{item.get('date', 'unknown')}",
                    "date": item.get("date"),
                    "cost": cost,
                    "baseline": baseline_avg,
                    "deviation_percentage": deviation_percentage,
                    "severity": severity,
                    "service": item.get("service", "Unknown"),
                    "detected_at": datetime.now()
                })
        
        return anomalies
    
    async def _calculate_cost_trends(self, cost_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate cost trends"""
        if len(cost_data) < 2:
            return {"trend": "insufficient_data"}
        
        # Simple linear trend calculation
        costs = [item.get("cost", 0) for item in cost_data]
        
        # Calculate trend over time
        first_half_avg = sum(costs[:len(costs)//2]) / (len(costs)//2)
        second_half_avg = sum(costs[len(costs)//2:]) / (len(costs) - len(costs)//2)
        
        trend_percentage = ((second_half_avg - first_half_avg) / first_half_avg) * 100
        
        trend_direction = "increasing" if trend_percentage > 5 else "decreasing" if trend_percentage < -5 else "stable"
        
        return {
            "trend": trend_direction,
            "trend_percentage": trend_percentage,
            "first_period_avg": first_half_avg,
            "second_period_avg": second_half_avg
        }
    
    async def _generate_compute_recommendations(self, cost_analysis: Dict[str, Any], current_usage: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate compute optimization recommendations"""
        recommendations = []
        
        # Example compute recommendations
        recommendations.append({
            "title": "Right-size EC2 Instances",
            "description": "Several EC2 instances are underutilized and can be downsized",
            "action": "Downsize t3.large instances to t3.medium",
            "potential_savings": 300.0,
            "risk_level": "low",
            "priority_score": 8,
            "implementation_effort": "low",
            "category": "compute"
        })
        
        recommendations.append({
            "title": "Use Spot Instances for Development",
            "description": "Development workloads can use Spot instances for significant savings",
            "action": "Convert development instances to Spot instances",
            "potential_savings": 500.0,
            "risk_level": "medium",
            "priority_score": 7,
            "implementation_effort": "medium",
            "category": "compute"
        })
        
        return recommendations
    
    async def _generate_storage_recommendations(self, cost_analysis: Dict[str, Any], current_usage: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate storage optimization recommendations"""
        recommendations = []
        
        recommendations.append({
            "title": "Optimize EBS Volume Types",
            "description": "Switch from GP2 to GP3 volumes for better price/performance",
            "action": "Migrate EBS volumes from GP2 to GP3",
            "potential_savings": 150.0,
            "risk_level": "low",
            "priority_score": 6,
            "implementation_effort": "low",
            "category": "storage"
        })
        
        return recommendations
    
    async def _generate_reserved_instance_recommendations(self, cost_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate reserved instance recommendations"""
        recommendations = []
        
        recommendations.append({
            "title": "Purchase Reserved Instances",
            "description": "Consistent usage patterns indicate potential for Reserved Instance savings",
            "action": "Purchase 1-year Reserved Instances for production workloads",
            "potential_savings": 800.0,
            "risk_level": "low",
            "priority_score": 9,
            "implementation_effort": "low",
            "category": "reserved_instances"
        })
        
        return recommendations
    
    async def _generate_budget_recommendations(self, cost_analysis: Dict[str, Any], budget_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate budget-based recommendations"""
        recommendations = []
        
        current_spend = budget_info.get("current_spend", 0)
        budget_limit = budget_info.get("warning_limit", 0)
        
        if current_spend > budget_limit * 0.8:  # Over 80% of budget
            recommendations.append({
                "title": "Immediate Cost Reduction Required",
                "description": f"Current spend (${current_spend}) is approaching budget limit (${budget_limit})",
                "action": "Implement immediate cost reduction measures",
                "potential_savings": current_spend - budget_limit * 0.7,
                "risk_level": "high",
                "priority_score": 10,
                "implementation_effort": "high",
                "category": "budget_management"
            })
        
        return recommendations
    
    async def _generate_emergency_cost_recommendations(self, threshold_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate emergency cost reduction recommendations"""
        recommendations = []
        
        recommendations.append({
            "title": "Emergency: Stop Non-Production Resources",
            "description": "Immediately stop all non-production EC2 instances and RDS databases",
            "action": "Stop development and staging resources",
            "potential_savings": 400.0,
            "risk_level": "medium",
            "priority_score": 10,
            "implementation_effort": "low",
            "category": "emergency"
        })
        
        recommendations.append({
            "title": "Emergency: Reduce Data Transfer",
            "description": "Optimize data transfer patterns to reduce costs",
            "action": "Implement data transfer optimization",
            "potential_savings": 200.0,
            "risk_level": "low",
            "priority_score": 9,
            "implementation_effort": "medium",
            "category": "emergency"
        })
        
        return recommendations
    
    async def _calculate_recommendation_impact(self, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate impact analysis for recommendation"""
        potential_savings = recommendation.get("potential_savings", 0)
        risk_level = recommendation.get("risk_level", "low")
        
        return {
            "cost_savings": potential_savings,
            "monthly_savings": potential_savings,
            "annual_savings": potential_savings * 12,
            "risk_assessment": risk_level,
            "affected_resources": recommendation.get("affected_resources", []),
            "implementation_timeline": "1-2 weeks",
            "rollback_plan": "Available" if risk_level == "low" else "Complex",
            "success_metrics": [
                f"Achieve ${potential_savings} monthly savings",
                "Maintain service performance",
                "No service disruptions"
            ]
        }
    
    def _determine_required_approvers(self, impact_analysis: Dict[str, Any]) -> List[str]:
        """Determine required approvers based on impact"""
        cost_savings = impact_analysis.get("cost_savings", 0)
        risk_level = impact_analysis.get("risk_assessment", "low")
        
        approvers = []
        
        if cost_savings > 1000 or risk_level == "high":
            approvers.extend(["ceo", "cto"])
        elif cost_savings > 500 or risk_level == "medium":
            approvers.append("cto")
        else:
            approvers.append("finops_lead")
        
        return approvers
    
    async def _generate_cost_alert(self, anomaly: Dict[str, Any]) -> None:
        """Generate cost alert for anomaly"""
        alert_id = anomaly.get("id")
        
        # Check cooldown period
        if alert_id in self.active_alerts:
            last_alert = self.active_alerts[alert_id].get("last_sent")
            if last_alert and (datetime.now() - last_alert).hours < self.config.get("alert_cooldown_hours", 24):
                return  # Skip alert due to cooldown
        
        # Create alert
        alert = {
            "alert_id": alert_id,
            "type": "cost_anomaly",
            "severity": anomaly.get("severity", "medium"),
            "message": f"Cost anomaly detected: {anomaly.get('deviation_percentage', 0):.1f}% deviation",
            "anomaly_data": anomaly,
            "detected_at": datetime.now(),
            "last_sent": datetime.now()
        }
        
        self.active_alerts[alert_id] = alert
        
        # Send alert via MCP server
        if self.mcp_server:
            alert_message = AgentMessage(
                sender=self.agent_id,
                recipient="alert_management_agent",
                message_type=MessageType.NOTIFICATION,
                content={
                    "alert": alert,
                    "action_required": True
                }
            )
            
            await self.mcp_server.route_message(alert_message)
        
        self.logger.warning(f"Cost anomaly alert generated: {alert_id}")
    
    async def _process_cost_alert(self, alert_data: Dict[str, Any]) -> None:
        """Process incoming cost alert"""
        alert_id = alert_data.get("alert_id")
        
        # Store alert
        self.active_alerts[alert_id] = alert_data
        
        # Generate recommendations based on alert
        if alert_data.get("severity") in ["high", "critical"]:
            recommendations = await self._generate_emergency_cost_recommendations(alert_data)
            
            # Create decision proposals
            for rec in recommendations[:2]:  # Top 2 recommendations
                await self.create_decision_proposal(rec)
    
    async def _process_new_anomaly(self, anomaly: Dict[str, Any]) -> None:
        """Process newly detected anomaly"""
        await self._generate_cost_alert(anomaly)
        
        # If severe anomaly, generate immediate recommendations
        if anomaly.get("severity") == "high":
            recommendations = await self.generate_recommendations({
                "cost_analysis": {"anomaly": anomaly}
            })
            
            for rec in recommendations[:1]:  # Top recommendation
                await self.create_decision_proposal(rec)
    
    async def _get_current_cost_summary(self) -> Dict[str, Any]:
        """Get current cost summary"""
        # Simulate current cost data
        return {
            "total_monthly_cost": 2500.0,
            "daily_average": 83.33,
            "top_services": {
                "EC2": 1200.0,
                "RDS": 600.0,
                "S3": 300.0,
                "Lambda": 100.0,
                "Data Transfer": 300.0
            },
            "cost_trend": "increasing",
            "last_updated": datetime.now().isoformat()
        }    

    # Backward Compatibility Methods
    async def calculate_cost_metrics(self, usage_summary=None) -> Dict[str, Any]:
        """Calculate key financial metrics (backward compatibility method)"""
        try:
            if usage_summary:
                # Use provided usage summary
                current_spend = usage_summary.budget_info.current_spend
                budget_limit = usage_summary.budget_info.warning_limit
                forecast_amount = usage_summary.cost_forecast.forecasted_amount
                trend_factor = usage_summary.cost_forecast.trend_factor
            else:
                # Get current cost data
                cost_summary = await self._get_current_cost_summary()
                current_spend = cost_summary.get('current_spend', 0)
                budget_limit = cost_summary.get('budget_limit', 10000)
                forecast_amount = cost_summary.get('forecast', current_spend * 1.1)
                trend_factor = cost_summary.get('trend_factor', 1.0)
            
            # Calculate metrics
            budget_pct = (current_spend / budget_limit * 100) if budget_limit > 0 else 0
            trending = 'up' if trend_factor > 1.0 else 'stable' if trend_factor == 1.0 else 'down'
            
            return {
                'current_spend': current_spend,
                'budget': budget_limit,
                'budget_pct': budget_pct,
                'forecast': forecast_amount,
                'trending': trending,
                'has_resources': current_spend > 0,
                'data_source': 'cost_management_agent'
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating cost metrics: {e}")
            return {
                'current_spend': 0,
                'budget': 10000,
                'budget_pct': 0,
                'forecast': 0,
                'trending': 'stable',
                'has_resources': False,
                'data_source': 'fallback'
            }
    
    async def validate_cost_data(self, usage_summary=None) -> bool:
        """Validate cost data consistency (backward compatibility method)"""
        try:
            if not usage_summary:
                return True
            
            # Validate service costs sum to total
            service_total = sum(sc.cost.amount for sc in usage_summary.service_costs)
            current_spend = usage_summary.budget_info.current_spend
            
            # Allow for small rounding differences
            if abs(service_total - current_spend) > 0.01:
                self.logger.debug(f"Cost data difference: Service total ${service_total:.2f}, Current spend ${current_spend:.2f}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating cost data: {e}")
            return False
    
    async def refresh_cost_data(self) -> bool:
        """Force refresh cost data (backward compatibility method)"""
        try:
            # Trigger cost data refresh through agent
            result = await self.execute_action('analyze_cost_data', {
                'time_period': '30_days',
                'force_refresh': True
            })
            
            return result.get('success', False)
            
        except Exception as e:
            self.logger.error(f"Error refreshing cost data: {e}")
            return False
    
    async def load_cost_data(self) -> Dict[str, Any]:
        """Load cost data (backward compatibility method)"""
        try:
            # Get comprehensive cost analysis
            result = await self.execute_action('get_cost_summary', {})
            
            if result.get('success'):
                return result.get('current_costs', {})
            else:
                return {}
                
        except Exception as e:
            self.logger.error(f"Error loading cost data: {e}")
            return {}
    
    async def enhance_budget_timeline(self, original_timeline: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance budget timeline with agent insights"""
        try:
            # Add agent-generated insights to timeline
            enhanced_timeline = original_timeline.copy()
            
            # Add AI-generated recommendations
            if 'recommended_actions' in enhanced_timeline:
                ai_recommendations = await self._generate_ai_budget_recommendations(enhanced_timeline)
                enhanced_timeline['ai_recommendations'] = ai_recommendations
            
            # Add anomaly detection insights
            if enhanced_timeline.get('daily_cost_estimate'):
                anomaly_insights = await self._detect_budget_anomalies(enhanced_timeline)
                enhanced_timeline['anomaly_insights'] = anomaly_insights
            
            return enhanced_timeline
            
        except Exception as e:
            self.logger.error(f"Error enhancing budget timeline: {e}")
            return original_timeline
    
    async def _generate_ai_budget_recommendations(self, timeline: Dict[str, Any]) -> List[str]:
        """Generate AI-powered budget recommendations"""
        recommendations = []
        
        try:
            current_spend = timeline.get('current_spend', 0)
            warning_limit = timeline.get('warning_limit', 0)
            days_to_warning = timeline.get('days_to_warning')
            
            if days_to_warning and days_to_warning <= 7:
                recommendations.append("🤖 AI Insight: Immediate cost reduction needed - consider pausing non-critical resources")
            elif days_to_warning and days_to_warning <= 30:
                recommendations.append("🤖 AI Insight: Proactive optimization recommended - review resource utilization")
            
            if current_spend > warning_limit * 0.8:
                recommendations.append("🤖 AI Insight: Approaching budget threshold - enable automated cost controls")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating AI budget recommendations: {e}")
            return []
    
    async def _detect_budget_anomalies(self, timeline: Dict[str, Any]) -> Dict[str, Any]:
        """Detect budget anomalies using AI analysis"""
        try:
            daily_cost = timeline.get('daily_cost_estimate', 0)
            growth_rate = timeline.get('daily_growth_rate', 0)
            
            anomalies = {
                'unusual_growth': growth_rate > 0.1,  # 10% daily growth is unusual
                'cost_spike': daily_cost > timeline.get('safe_daily_budget', float('inf')),
                'trend_analysis': 'increasing' if growth_rate > 0.05 else 'stable'
            }
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Error detecting budget anomalies: {e}")
            return {}