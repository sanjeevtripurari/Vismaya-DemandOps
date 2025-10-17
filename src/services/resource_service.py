"""
Resource Management Service
Handles AWS resource inventory and management
Following Single Responsibility Principle
"""

import logging
from typing import List, Dict, Optional

from ..core.interfaces import IResourceProvider
from ..core.models import EC2Instance, StorageVolume, DatabaseInstance, ScenarioInput, ScenarioResult

logger = logging.getLogger(__name__)


class ResourceManagementService:
    """Service for AWS resource management"""
    
    def __init__(self, resource_provider: IResourceProvider):
        self._resource_provider = resource_provider
    
    async def get_resource_inventory(self) -> Dict:
        """Get complete resource inventory"""
        try:
            ec2_instances = await self._resource_provider.get_ec2_instances()
            storage_volumes = await self._resource_provider.get_storage_volumes()
            database_instances = await self._resource_provider.get_database_instances()
            
            return {
                "ec2_instances": ec2_instances,
                "storage_volumes": storage_volumes,
                "database_instances": database_instances,
                "total_ec2_cost": sum(instance.monthly_cost for instance in ec2_instances),
                "total_storage_cost": sum(volume.monthly_cost for volume in storage_volumes),
                "total_database_cost": sum(db.monthly_cost for db in database_instances)
            }
            
        except Exception as e:
            logger.error(f"Error getting resource inventory: {e}")
            return {
                "ec2_instances": [],
                "storage_volumes": [],
                "database_instances": [],
                "total_ec2_cost": 0,
                "total_storage_cost": 0,
                "total_database_cost": 0
            }
    
    async def get_ec2_summary(self) -> Dict:
        """Get EC2 instances summary"""
        try:
            instances = await self._resource_provider.get_ec2_instances()
            
            # Group by instance type
            type_summary = {}
            total_cost = 0
            
            for instance in instances:
                if instance.instance_type not in type_summary:
                    type_summary[instance.instance_type] = {
                        "count": 0,
                        "total_cost": 0,
                        "instances": []
                    }
                
                type_summary[instance.instance_type]["count"] += 1
                type_summary[instance.instance_type]["total_cost"] += instance.monthly_cost
                type_summary[instance.instance_type]["instances"].append(instance)
                total_cost += instance.monthly_cost
            
            return {
                "total_instances": len(instances),
                "total_monthly_cost": total_cost,
                "by_type": type_summary,
                "instances": instances
            }
            
        except Exception as e:
            logger.error(f"Error getting EC2 summary: {e}")
            return {
                "total_instances": 0,
                "total_monthly_cost": 0,
                "by_type": {},
                "instances": []
            }
    
    async def get_storage_summary(self) -> Dict:
        """Get storage volumes summary"""
        try:
            volumes = await self._resource_provider.get_storage_volumes()
            
            # Group by volume type
            type_summary = {}
            total_size = 0
            total_cost = 0
            
            for volume in volumes:
                if volume.volume_type not in type_summary:
                    type_summary[volume.volume_type] = {
                        "count": 0,
                        "total_size_gb": 0,
                        "total_cost": 0,
                        "volumes": []
                    }
                
                type_summary[volume.volume_type]["count"] += 1
                type_summary[volume.volume_type]["total_size_gb"] += volume.size_gb
                type_summary[volume.volume_type]["total_cost"] += volume.monthly_cost
                type_summary[volume.volume_type]["volumes"].append(volume)
                
                total_size += volume.size_gb
                total_cost += volume.monthly_cost
            
            return {
                "total_volumes": len(volumes),
                "total_size_gb": total_size,
                "total_monthly_cost": total_cost,
                "by_type": type_summary,
                "volumes": volumes
            }
            
        except Exception as e:
            logger.error(f"Error getting storage summary: {e}")
            return {
                "total_volumes": 0,
                "total_size_gb": 0,
                "total_monthly_cost": 0,
                "by_type": {},
                "volumes": []
            }
    
    async def get_database_summary(self) -> Dict:
        """Get database instances summary"""
        try:
            databases = await self._resource_provider.get_database_instances()
            
            # Group by engine
            engine_summary = {}
            total_cost = 0
            
            for db in databases:
                if db.engine not in engine_summary:
                    engine_summary[db.engine] = {
                        "count": 0,
                        "total_cost": 0,
                        "instances": []
                    }
                
                engine_summary[db.engine]["count"] += 1
                engine_summary[db.engine]["total_cost"] += db.monthly_cost
                engine_summary[db.engine]["instances"].append(db)
                total_cost += db.monthly_cost
            
            return {
                "total_databases": len(databases),
                "total_monthly_cost": total_cost,
                "by_engine": engine_summary,
                "databases": databases
            }
            
        except Exception as e:
            logger.error(f"Error getting database summary: {e}")
            return {
                "total_databases": 0,
                "total_monthly_cost": 0,
                "by_engine": {},
                "databases": []
            }
    
    def calculate_scenario_impact(self, 
                                current_inventory: Dict, 
                                scenario: ScenarioInput) -> Dict:
        """Calculate the impact of a what-if scenario"""
        try:
            current_cost = (
                current_inventory.get("total_ec2_cost", 0) +
                current_inventory.get("total_storage_cost", 0) +
                current_inventory.get("total_database_cost", 0)
            )
            
            # Estimate additional costs
            # These are rough estimates - in production, use actual AWS pricing API
            additional_ec2_cost = scenario.additional_ec2_instances * 120  # $120/month per t3.medium
            additional_storage_cost = scenario.additional_storage_gb * 0.10  # $0.10/GB/month for gp3
            
            total_additional_cost = additional_ec2_cost + additional_storage_cost
            new_total_cost = current_cost + total_additional_cost
            
            return {
                "current_monthly_cost": current_cost,
                "additional_monthly_cost": total_additional_cost,
                "new_total_monthly_cost": new_total_cost,
                "cost_increase_percentage": (total_additional_cost / current_cost * 100) if current_cost > 0 else 0,
                "breakdown": {
                    "additional_ec2_cost": additional_ec2_cost,
                    "additional_storage_cost": additional_storage_cost
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating scenario impact: {e}")
            return {
                "current_monthly_cost": 0,
                "additional_monthly_cost": 0,
                "new_total_monthly_cost": 0,
                "cost_increase_percentage": 0,
                "breakdown": {}
            }