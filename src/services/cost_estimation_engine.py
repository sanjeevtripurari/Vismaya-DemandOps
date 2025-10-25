"""
Cost Estimation Engine
Calculates accurate cost estimates based on AWS pricing data and usage parameters
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from ..core.interfaces import ICostEstimationEngine
from ..core.models import (
    ResourceSpecification, PricingData, CostEstimateResponse,
    TimePeriod, BudgetImpactAnalysis, BudgetInfo, ResourceType,
    PricingModel, PricingAPIError
)

logger = logging.getLogger(__name__)


class CostEstimationEngine(ICostEstimationEngine):
    """Engine for calculating accurate AWS resource cost estimates"""
    
    def __init__(self):
        # Additional cost factors (data transfer, storage, etc.)
        self.additional_cost_factors = {
            ResourceType.EC2: {
                'ebs_storage_gb_month': 0.10,  # GP3 storage cost per GB/month
                'data_transfer_gb': 0.09,      # Data transfer out cost per GB
                'elastic_ip': 3.65             # Elastic IP cost per month
            },
            ResourceType.RDS: {
                'backup_storage_gb_month': 0.095,  # Backup storage cost per GB/month
                'data_transfer_gb': 0.09           # Data transfer out cost per GB
            },
            ResourceType.EBS: {
                'snapshot_gb_month': 0.05,     # Snapshot storage cost per GB/month
                'iops_provisioned': 0.065      # Provisioned IOPS cost per IOPS/month
            }
        }
    
    async def estimate_resource_cost(self, resource_spec: ResourceSpecification, 
                                   pricing_data: PricingData, 
                                   duration: TimePeriod) -> CostEstimateResponse:
        """Calculate total cost estimate for resource over specified duration"""
        try:
            logger.info(f"Calculating cost estimate for {resource_spec.resource_type.value} over {duration.description}")
            
            if not pricing_data.has_pricing_data:
                return CostEstimateResponse(
                    resource_spec=resource_spec,
                    pricing_breakdown={},
                    total_cost=0.0,
                    duration=duration,
                    error_message="No pricing data available for this resource configuration"
                )
            
            # Calculate costs for different pricing models
            pricing_breakdown = {}
            
            # On-Demand pricing
            if pricing_data.on_demand_hourly:
                on_demand_cost = self._calculate_on_demand_cost(
                    pricing_data.on_demand_hourly, 
                    resource_spec, 
                    duration
                )
                pricing_breakdown['On-Demand'] = on_demand_cost
            
            # Reserved Instance pricing
            if pricing_data.reserved_monthly:
                reserved_cost = self._calculate_reserved_cost(
                    pricing_data.reserved_monthly, 
                    resource_spec, 
                    duration
                )
                pricing_breakdown['Reserved (1-year)'] = reserved_cost
            
            # Spot pricing (if available)
            if pricing_data.spot_hourly:
                spot_cost = self._calculate_spot_cost(
                    pricing_data.spot_hourly, 
                    resource_spec, 
                    duration
                )
                pricing_breakdown['Spot'] = spot_cost
            
            # Calculate additional costs
            additional_costs = self._calculate_additional_costs(resource_spec, duration)
            if additional_costs:
                for cost_type, cost_amount in additional_costs.items():
                    pricing_breakdown[f"Additional: {cost_type}"] = cost_amount
            
            # Calculate total cost (use on-demand as primary, fallback to first available)
            if 'On-Demand' in pricing_breakdown:
                total_cost = pricing_breakdown['On-Demand']
            elif pricing_breakdown:
                # Use the first non-zero cost if on-demand is not available
                total_cost = next((cost for cost in pricing_breakdown.values() if cost > 0), 0.0)
            else:
                total_cost = 0.0
            
            # Generate recommendations
            recommendations = self._generate_cost_recommendations(
                resource_spec, pricing_breakdown, duration
            )
            
            response = CostEstimateResponse(
                resource_spec=resource_spec,
                pricing_breakdown=pricing_breakdown,
                total_cost=total_cost,
                duration=duration,
                recommendations=recommendations,
                data_source=pricing_data.source,
                timestamp=datetime.now()
            )
            
            logger.info(f"✅ Cost estimate calculated: ${total_cost:.2f} for {duration.description}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to calculate cost estimate: {e}")
            return CostEstimateResponse(
                resource_spec=resource_spec,
                pricing_breakdown={},
                total_cost=0.0,
                duration=duration,
                error_message=f"Cost calculation failed: {str(e)}"
            )
    
    async def calculate_budget_impact(self, cost_estimate: float, 
                                    current_budget: BudgetInfo) -> BudgetImpactAnalysis:
        """Analyze impact of additional costs on current budget"""
        try:
            new_total_cost = current_budget.current_spend + cost_estimate
            
            # Calculate threshold impacts
            warning_threshold_impact = max(0, new_total_cost - current_budget.warning_limit)
            critical_threshold_impact = max(0, new_total_cost - current_budget.maximum_limit)
            
            # Check if thresholds are exceeded
            exceeds_warning = new_total_cost > current_budget.warning_limit
            exceeds_critical = new_total_cost > current_budget.maximum_limit
            
            # Calculate timeline changes (simplified)
            days_to_warning_change = None
            days_to_critical_change = None
            
            # Generate recommendations based on impact
            recommendations = []
            
            if exceeds_critical:
                recommendations.extend([
                    f"🚨 CRITICAL: Adding this resource would exceed your maximum budget limit by ${critical_threshold_impact:.2f}",
                    "Consider reducing the resource size or duration",
                    "Review current spending to identify cost reduction opportunities"
                ])
            elif exceeds_warning:
                recommendations.extend([
                    f"⚠️ WARNING: Adding this resource would exceed your warning limit by ${warning_threshold_impact:.2f}",
                    "Monitor your budget closely if you proceed",
                    "Consider using Reserved Instances or Spot instances for cost savings"
                ])
            elif warning_threshold_impact > current_budget.remaining_budget * 0.5:
                recommendations.extend([
                    f"📊 This resource would use {(cost_estimate/current_budget.remaining_budget)*100:.1f}% of your remaining budget",
                    "Budget impact is significant but manageable",
                    "Consider cost optimization options"
                ])
            else:
                recommendations.extend([
                    "✅ This resource fits comfortably within your current budget",
                    f"Remaining budget after this resource: ${current_budget.remaining_budget - cost_estimate:.2f}"
                ])
            
            return BudgetImpactAnalysis(
                additional_cost=cost_estimate,
                new_total_cost=new_total_cost,
                warning_threshold_impact=warning_threshold_impact,
                critical_threshold_impact=critical_threshold_impact,
                days_to_warning_change=days_to_warning_change,
                days_to_critical_change=days_to_critical_change,
                exceeds_warning=exceeds_warning,
                exceeds_critical=exceeds_critical,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Failed to calculate budget impact: {e}")
            return BudgetImpactAnalysis(
                additional_cost=cost_estimate,
                new_total_cost=current_budget.current_spend + cost_estimate,
                warning_threshold_impact=0.0,
                critical_threshold_impact=0.0,
                recommendations=[f"Budget impact calculation failed: {str(e)}"]
            )
    
    def _calculate_on_demand_cost(self, hourly_rate: float, 
                                resource_spec: ResourceSpecification, 
                                duration: TimePeriod) -> float:
        """Calculate On-Demand cost"""
        total_hours = duration.hours
        base_cost = hourly_rate * total_hours * resource_spec.quantity
        
        # Add any resource-specific multipliers
        if resource_spec.resource_type == ResourceType.RDS:
            # RDS instances typically have higher costs due to managed service overhead
            base_cost *= 1.0  # No additional multiplier, pricing already includes management
        
        return base_cost
    
    def _calculate_reserved_cost(self, monthly_rate: float, 
                               resource_spec: ResourceSpecification, 
                               duration: TimePeriod) -> float:
        """Calculate Reserved Instance cost"""
        total_months = duration.months
        base_cost = monthly_rate * total_months * resource_spec.quantity
        
        # Reserved instances are typically 30-60% cheaper than On-Demand
        # The pricing data should already reflect this, so no additional discount
        return base_cost
    
    def _calculate_spot_cost(self, spot_hourly_rate: float, 
                           resource_spec: ResourceSpecification, 
                           duration: TimePeriod) -> float:
        """Calculate Spot instance cost"""
        total_hours = duration.hours
        base_cost = spot_hourly_rate * total_hours * resource_spec.quantity
        
        # Add spot interruption risk factor (assume 95% availability)
        # This is a rough estimate - actual spot availability varies
        availability_factor = 0.95
        adjusted_cost = base_cost / availability_factor
        
        return adjusted_cost
    
    def _calculate_additional_costs(self, resource_spec: ResourceSpecification, 
                                  duration: TimePeriod) -> Dict[str, float]:
        """Calculate additional costs based on resource type and specifications"""
        additional_costs = {}
        
        if resource_spec.resource_type == ResourceType.EC2:
            # EBS storage cost
            if resource_spec.additional_specs.get('ebs_storage_gb'):
                storage_gb = resource_spec.additional_specs['ebs_storage_gb']
                storage_cost = (storage_gb * 
                              self.additional_cost_factors[ResourceType.EC2]['ebs_storage_gb_month'] * 
                              duration.months * resource_spec.quantity)
                additional_costs['EBS Storage'] = storage_cost
            
            # Elastic IP cost (if specified)
            if resource_spec.additional_specs.get('elastic_ip'):
                eip_cost = (self.additional_cost_factors[ResourceType.EC2]['elastic_ip'] * 
                           duration.months * resource_spec.quantity)
                additional_costs['Elastic IP'] = eip_cost
        
        elif resource_spec.resource_type == ResourceType.RDS:
            # Backup storage cost
            if resource_spec.additional_specs.get('allocated_storage'):
                storage_gb = resource_spec.additional_specs['allocated_storage']
                # Assume 20% additional backup storage
                backup_storage_gb = storage_gb * 0.2
                backup_cost = (backup_storage_gb * 
                             self.additional_cost_factors[ResourceType.RDS]['backup_storage_gb_month'] * 
                             duration.months * resource_spec.quantity)
                additional_costs['Backup Storage'] = backup_cost
        
        elif resource_spec.resource_type == ResourceType.EBS:
            # Snapshot cost (assume monthly snapshots)
            if resource_spec.additional_specs.get('size_gb'):
                size_gb = resource_spec.additional_specs['size_gb']
                snapshot_cost = (size_gb * 
                               self.additional_cost_factors[ResourceType.EBS]['snapshot_gb_month'] * 
                               duration.months * resource_spec.quantity)
                additional_costs['Snapshots'] = snapshot_cost
            
            # Provisioned IOPS cost (for io1/io2 volumes)
            volume_type = resource_spec.additional_specs.get('volume_type', 'gp3')
            if volume_type in ['io1', 'io2']:
                iops = resource_spec.additional_specs.get('iops', 3000)
                iops_cost = (iops * 
                           self.additional_cost_factors[ResourceType.EBS]['iops_provisioned'] * 
                           duration.months * resource_spec.quantity)
                additional_costs['Provisioned IOPS'] = iops_cost
        
        return additional_costs
    
    def _generate_cost_recommendations(self, resource_spec: ResourceSpecification, 
                                     pricing_breakdown: Dict[str, float], 
                                     duration: TimePeriod) -> List[str]:
        """Generate cost optimization recommendations"""
        recommendations = []
        
        if not pricing_breakdown:
            return ["No pricing data available for recommendations"]
        
        # Find cheapest option
        cheapest_option = min(pricing_breakdown.items(), key=lambda x: x[1])
        most_expensive = max(pricing_breakdown.items(), key=lambda x: x[1])
        
        if len(pricing_breakdown) > 1:
            savings = most_expensive[1] - cheapest_option[1]
            savings_percent = (savings / most_expensive[1]) * 100
            
            recommendations.append(
                f"💰 Best value: {cheapest_option[0]} (${cheapest_option[1]:.2f}) "
                f"saves ${savings:.2f} ({savings_percent:.1f}%) vs {most_expensive[0]}"
            )
        
        # Duration-specific recommendations
        if duration.months >= 12:
            recommendations.append(
                "📅 For long-term usage (12+ months), Reserved Instances offer the best savings"
            )
        elif duration.months >= 1:
            recommendations.append(
                "⏱️ For medium-term usage, consider Savings Plans for additional flexibility"
            )
        else:
            recommendations.append(
                "🚀 For short-term usage, On-Demand or Spot instances are most suitable"
            )
        
        # Resource-specific recommendations
        if resource_spec.resource_type == ResourceType.EC2:
            if resource_spec.instance_type and 't3' in resource_spec.instance_type:
                recommendations.append(
                    "💡 T3 instances are burstable - monitor CPU credits for consistent performance"
                )
            
            recommendations.append(
                "🔧 Consider rightsizing: monitor actual usage and adjust instance type as needed"
            )
        
        elif resource_spec.resource_type == ResourceType.RDS:
            recommendations.append(
                "🗄️ RDS includes automated backups, patching, and monitoring in the price"
            )
            
            if resource_spec.additional_specs.get('engine') == 'mysql':
                recommendations.append(
                    "🔄 Consider Aurora MySQL for better performance and cost efficiency at scale"
                )
        
        elif resource_spec.resource_type == ResourceType.EBS:
            volume_type = resource_spec.additional_specs.get('volume_type', 'gp3')
            if volume_type == 'gp2':
                recommendations.append(
                    "⚡ Consider upgrading to GP3 for better price/performance ratio"
                )
        
        # Quantity-based recommendations
        if resource_spec.quantity > 1:
            recommendations.append(
                f"📊 Total cost is for {resource_spec.quantity} resources. "
                f"Per-resource cost: ${cheapest_option[1]/resource_spec.quantity:.2f}"
            )
        
        return recommendations