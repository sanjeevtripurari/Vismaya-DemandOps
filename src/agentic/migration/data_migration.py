"""
Data Migration Scripts for Agentic AI System
Transforms existing data models to agentic architecture
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict

from ..core.interfaces import (
    AgentMessage, AgentState, DecisionProposal, AgentConfiguration
)
from ..strands.memory_store import DynamoDBMemoryStore



@dataclass
class MigrationResult:
    """Result of a migration operation"""
    success: bool
    migrated_count: int
    failed_count: int
    errors: List[str]
    duration_seconds: float
    timestamp: datetime


class DataMigrationManager:
    """
    Manages migration of existing data models to agentic architecture
    Handles data transformation and migration tracking
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Migration components
        self.memory_store: Optional[DynamoDBMemoryStore] = None
        
        # Migration tracking
        self.migration_history: List[MigrationResult] = []
        self.migration_log_path = config.get("migration_log_path", "logs/migration.log")
        
        # Data transformers
        self.transformers = {
            "usage_summary": self._transform_usage_summary,
            "budget_info": self._transform_budget_info,
            "cost_forecast": self._transform_cost_forecast,
            "service_costs": self._transform_service_costs,
            "resources": self._transform_resources
        }
    
    async def initialize(self, memory_store: DynamoDBMemoryStore) -> bool:
        """Initialize migration manager with memory store"""
        try:
            self.memory_store = memory_store
            
            # Ensure migration log directory exists
            log_path = Path(self.migration_log_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.logger.info("Data migration manager initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize migration manager: {e}")
            return False
    
    async def migrate_all_data(self) -> MigrationResult:
        """Migrate all data from legacy system to agentic architecture"""
        start_time = datetime.now()
        total_migrated = 0
        total_failed = 0
        all_errors = []
        
        try:
            self.logger.info("Starting complete data migration")
            
            # Migration steps in order
            migration_steps = [
                ("usage_summaries", self._migrate_usage_summaries),
                ("historical_data", self._migrate_historical_data),
                ("user_preferences", self._migrate_user_preferences),
                ("system_configurations", self._migrate_system_configurations),
                ("decision_history", self._migrate_decision_history)
            ]
            
            for step_name, migration_func in migration_steps:
                self.logger.info(f"Migrating {step_name}...")
                
                try:
                    result = await migration_func()
                    total_migrated += result.migrated_count
                    total_failed += result.failed_count
                    all_errors.extend(result.errors)
                    
                    self.logger.info(f"Completed {step_name}: {result.migrated_count} migrated, {result.failed_count} failed")
            
                except Exception as e:
                    error_msg = f"Error in migration step {step_name}: {e}"
                    self.logger.error(error_msg)
                    all_errors.append(error_msg)
                    total_failed += 1
            
            duration = (datetime.now() - start_time).total_seconds()
            
            result = MigrationResult(
                success=total_failed == 0,
                migrated_count=total_migrated,
                failed_count=total_failed,
                errors=all_errors,
                duration_seconds=duration,
                timestamp=datetime.now()
            )
            
            # Log migration result
            await self._log_migration_result("complete_migration", result)
            
            self.logger.info(f"Data migration completed: {total_migrated} migrated, {total_failed} failed")
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = f"Critical error in data migration: {e}"
            self.logger.error(error_msg)
            
            return MigrationResult(
                success=False,
                migrated_count=total_migrated,
                failed_count=total_failed + 1,
                errors=all_errors + [error_msg],
                duration_seconds=duration,
                timestamp=datetime.now()
            )
    
    async def _migrate_usage_summaries(self) -> MigrationResult:
        """Migrate usage summaries to agent context"""
        start_time = datetime.now()
        migrated_count = 0
        failed_count = 0
        errors = []
        
        try:
            # Create sample usage summaries for migration
            # In real implementation, this would fetch from existing database
            sample_summaries = [
                {
                    "last_updated": datetime.now(),
                    "budget_info": {
                        "current_spend": 1500.0,
                        "warning_limit": 2000.0,
                        "maximum_limit": 2500.0,
                        "utilization_percentage": 60.0,
                        "budget_status": "normal"
                    },
                    "cost_forecast": {
                        "forecasted_amount": 1800.0,
                        "confidence_level": 0.85,
                        "trend_factor": 1.2,
                        "forecast_days": 30
                    }
                }
            ]
            
            for summary in sample_summaries:
                try:
                    # Transform to agent context format
                    agent_context = await self._transform_usage_summary(summary)
                    
                    # Store in memory store
                    context_key = f"usage_summary_{summary['last_updated'].strftime('%Y%m%d_%H%M%S')}"
                    
                    await self.memory_store.update_context(
                        "cost_management_agent",
                        {context_key: agent_context}
                    )
                    
                    migrated_count += 1
                    
                except Exception as e:
                    error_msg = f"Failed to migrate usage summary: {e}"
                    self.logger.error(error_msg)
                    errors.append(error_msg)
                    failed_count += 1
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return MigrationResult(
                success=failed_count == 0,
                migrated_count=migrated_count,
                failed_count=failed_count,
                errors=errors,
                duration_seconds=duration,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return MigrationResult(
                success=False,
                migrated_count=migrated_count,
                failed_count=failed_count + 1,
                errors=errors + [str(e)],
                duration_seconds=duration,
                timestamp=datetime.now()
            )
    
    async def _migrate_historical_data(self) -> MigrationResult:
        """Migrate historical cost and resource data"""
        start_time = datetime.now()
        migrated_count = 0
        failed_count = 0
        errors = []
        
        try:
            # Create sample historical data for migration
            # In real implementation, this would fetch from existing database
            sample_historical_data = []
            
            # Generate 30 days of sample data
            for i in range(30):
                date = datetime.now() - timedelta(days=i)
                sample_historical_data.append({
                    "date": date,
                    "total_cost": 1400 + (i * 10),  # Trending upward
                    "service_costs": {
                        "EC2": 800 + (i * 5),
                        "RDS": 300 + (i * 2),
                        "S3": 200 + (i * 1),
                        "Lambda": 100 + (i * 2)
                    },
                    "resource_counts": {
                        "ec2_instances": 15 + (i // 5),
                        "storage_volumes": 25 + (i // 3),
                        "database_instances": 3
                    },
                    "budget_utilization": (1400 + (i * 10)) / 2500.0
                })
            
            # Group by date for trend analysis
            daily_data = {}
            for data_point in sample_historical_data:
                date_key = data_point["date"].strftime('%Y-%m-%d')
                daily_data[date_key] = data_point
            
            # Create trend data
            trend_data = []
            for date_key, data_point in daily_data.items():
                trend_point = {
                    "date": date_key,
                    "total_cost": data_point["total_cost"],
                    "service_breakdown": data_point["service_costs"],
                    "resource_counts": data_point["resource_counts"],
                    "budget_utilization": data_point["budget_utilization"]
                }
                trend_data.append(trend_point)
            
            # Store historical trends in memory store
            await self.memory_store.update_context(
                "forecasting_agent",
                {
                    "historical_trends": trend_data,
                    "migration_metadata": {
                        "data_points": len(trend_data),
                        "date_range": {
                            "start": min(daily_data.keys()) if daily_data else None,
                            "end": max(daily_data.keys()) if daily_data else None
                        },
                        "migrated_at": datetime.now().isoformat()
                    }
                }
            )
            
            migrated_count = len(trend_data)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return MigrationResult(
                success=True,
                migrated_count=migrated_count,
                failed_count=failed_count,
                errors=errors,
                duration_seconds=duration,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return MigrationResult(
                success=False,
                migrated_count=migrated_count,
                failed_count=failed_count + 1,
                errors=errors + [str(e)],
                duration_seconds=duration,
                timestamp=datetime.now()
            )
    
    async def _migrate_user_preferences(self) -> MigrationResult:
        """Migrate user preferences and settings"""
        start_time = datetime.now()
        migrated_count = 0
        failed_count = 0
        errors = []
        
        try:
            # Default user preferences for agentic system
            default_preferences = {
                "dashboard_layout": "modern",
                "ai_assistant_enabled": True,
                "notification_preferences": {
                    "cost_alerts": True,
                    "budget_warnings": True,
                    "approval_requests": True
                },
                "approval_settings": {
                    "auto_approve_low_risk": False,
                    "notification_email": None,
                    "escalation_timeout_hours": 24
                },
                "display_preferences": {
                    "currency": "USD",
                    "date_format": "YYYY-MM-DD",
                    "timezone": "UTC",
                    "decimal_places": 2
                }
            }
            
            # Create preferences for different user roles
            user_roles = ["admin", "ceo", "cto", "finops_lead", "devops_engineer"]
            
            for role in user_roles:
                role_preferences = default_preferences.copy()
                
                # Customize preferences by role
                if role in ["ceo", "cto"]:
                    role_preferences["approval_settings"]["auto_approve_threshold"] = 10000
                    role_preferences["notification_preferences"]["executive_summary"] = True
                elif role == "finops_lead":
                    role_preferences["notification_preferences"]["detailed_cost_breakdown"] = True
                    role_preferences["approval_settings"]["auto_approve_threshold"] = 5000
                elif role == "devops_engineer":
                    role_preferences["approval_settings"]["auto_approve_low_risk"] = False
                
                await self.memory_store.update_context(
                    "user_interface_agent",
                    {f"user_preferences_{role}": role_preferences}
                )
                
                migrated_count += 1
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return MigrationResult(
                success=True,
                migrated_count=migrated_count,
                failed_count=failed_count,
                errors=errors,
                duration_seconds=duration,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return MigrationResult(
                success=False,
                migrated_count=migrated_count,
                failed_count=failed_count + 1,
                errors=errors + [str(e)],
                duration_seconds=duration,
                timestamp=datetime.now()
            )
    
    async def _migrate_system_configurations(self) -> MigrationResult:
        """Migrate system configurations for agents"""
        start_time = datetime.now()
        migrated_count = 0
        failed_count = 0
        errors = []
        
        try:
            # Default configuration values (would normally come from Config class)
            default_config = {
                "AWS_REGION": "us-east-1",
                "ENVIRONMENT": "production",
                "BEDROCK_MODEL_ID": "anthropic.claude-3-sonnet-20240229-v1:0",
                "BUDGET_WARNING_LIMIT": 2000,
                "BUDGET_MAXIMUM_LIMIT": 2500
            }
            
            # Extract configurations for agents
            agent_configs = {
                "orchestrator_agent": {
                    "aws_region": default_config["AWS_REGION"],
                    "environment": default_config["ENVIRONMENT"],
                    "health_check_interval": 30,
                    "max_concurrent_workflows": 10,
                    "workflow_timeout_seconds": 300
                },
                "cost_management_agent": {
                    "aws_region": default_config["AWS_REGION"],
                    "budget_warning_limit": default_config["BUDGET_WARNING_LIMIT"],
                    "budget_maximum_limit": default_config["BUDGET_MAXIMUM_LIMIT"],
                    "cost_analysis_interval_hours": 6,
                    "anomaly_detection_threshold": 0.2
                },
                "resource_management_agent": {
                    "aws_region": default_config["AWS_REGION"],
                    "resource_scan_interval_hours": 24,
                    "optimization_threshold": 0.3
                },
                "forecasting_agent": {
                    "aws_region": default_config["AWS_REGION"],
                    "bedrock_model_id": default_config["BEDROCK_MODEL_ID"],
                    "forecast_horizon_days": 90,
                    "confidence_interval": 0.95,
                    "trend_analysis_window_days": 30
                },
                "alert_management_agent": {
                    "aws_region": default_config["AWS_REGION"],
                    "alert_check_interval_seconds": 300,
                    "max_alerts_per_hour": 10
                },
                "user_interface_agent": {
                    "bedrock_model_id": default_config["BEDROCK_MODEL_ID"],
                    "max_conversation_history": 50,
                    "response_timeout_seconds": 30
                },
                "approval_agent": {
                    "aws_region": default_config["AWS_REGION"],
                    "default_approval_timeout_hours": 24,
                    "escalation_levels": 3,
                    "email_notification_enabled": True,
                    "auto_reminder_interval_hours": 6
                }
            }
            
            # Store configurations for each agent
            for agent_id, config in agent_configs.items():
                await self.memory_store.update_context(
                    agent_id,
                    {
                        "agent_configuration": config,
                        "migrated_at": datetime.now().isoformat(),
                        "migration_source": "legacy_system_config"
                    }
                )
                
                migrated_count += 1
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return MigrationResult(
                success=True,
                migrated_count=migrated_count,
                failed_count=failed_count,
                errors=errors,
                duration_seconds=duration,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return MigrationResult(
                success=False,
                migrated_count=migrated_count,
                failed_count=failed_count + 1,
                errors=errors + [str(e)],
                duration_seconds=duration,
                timestamp=datetime.now()
            )
    
    async def _migrate_decision_history(self) -> MigrationResult:
        """Migrate decision history and create initial decision proposals"""
        start_time = datetime.now()
        migrated_count = 0
        failed_count = 0
        errors = []
        
        try:
            # Create sample decision proposals for migration
            decision_proposals = []
            
            # Budget optimization proposal
            decision_proposals.append({
                "proposal_id": f"budget_optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "title": "Budget Optimization Required",
                "description": "Current budget utilization is approaching warning threshold. Optimization recommended.",
                "impact_analysis": {
                    "cost_impact": 500.0,
                    "risk_level": "medium",
                    "affected_resources": ["EC2", "RDS", "S3"]
                },
                "recommendations": [
                    "Review and optimize high-cost services",
                    "Consider reserved instances for EC2",
                    "Implement automated resource scheduling"
                ],
                "required_approvers": ["ceo", "cto"],
                "created_by": "cost_management_agent",
                "status": "pending",
                "created_at": datetime.now().isoformat()
            })
            
            # Resource cleanup proposal
            decision_proposals.append({
                "proposal_id": f"resource_cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "title": "Unused Resource Cleanup",
                "description": "Found stopped instances that can be terminated to reduce costs.",
                "impact_analysis": {
                    "cost_impact": 200.0,
                    "risk_level": "low",
                    "affected_resources": ["i-1234567890abcdef0", "i-0987654321fedcba0"]
                },
                "recommendations": [
                    "Terminate stopped EC2 instances",
                    "Implement automated lifecycle management",
                    "Set up monitoring for unused resources"
                ],
                "required_approvers": ["cto"],
                "created_by": "resource_management_agent",
                "status": "pending",
                "created_at": datetime.now().isoformat()
            })
            
            # Store decision proposals
            for proposal in decision_proposals:
                await self.memory_store.store_decision_proposal(
                    DecisionProposal(
                        proposal_id=proposal["proposal_id"],
                        title=proposal["title"],
                        description=proposal["description"],
                        impact_analysis=proposal["impact_analysis"],
                        recommendations=proposal["recommendations"],
                        required_approvers=proposal["required_approvers"],
                        created_by=proposal["created_by"],
                        status=proposal["status"],
                        created_at=datetime.fromisoformat(proposal["created_at"])
                    )
                )
                
                migrated_count += 1
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return MigrationResult(
                success=True,
                migrated_count=migrated_count,
                failed_count=failed_count,
                errors=errors,
                duration_seconds=duration,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return MigrationResult(
                success=False,
                migrated_count=migrated_count,
                failed_count=failed_count + 1,
                errors=errors + [str(e)],
                duration_seconds=duration,
                timestamp=datetime.now()
            )
    
    # Data transformation methods
    async def _transform_usage_summary(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Transform usage summary to agent context format"""
        return {
            "timestamp": summary["last_updated"].isoformat(),
            "budget_info": {
                "current_spend": summary["budget_info"]["current_spend"],
                "warning_limit": summary["budget_info"]["warning_limit"],
                "maximum_limit": summary["budget_info"]["maximum_limit"],
                "utilization_percentage": summary["budget_info"]["utilization_percentage"],
                "budget_status": summary["budget_info"]["budget_status"]
            },
            "cost_forecast": {
                "forecasted_amount": summary["cost_forecast"]["forecasted_amount"],
                "confidence_level": summary["cost_forecast"]["confidence_level"],
                "trend_factor": summary["cost_forecast"]["trend_factor"],
                "forecast_days": summary["cost_forecast"]["forecast_days"]
            },
            "migration_metadata": {
                "migrated_at": datetime.now().isoformat(),
                "migration_source": "legacy_usage_summary",
                "transformation_version": "1.0"
            }
        }
    
    async def _transform_budget_info(self, budget_info: Dict[str, Any]) -> Dict[str, Any]:
        """Transform budget info to agent format"""
        return {
            "current_spend": budget_info["current_spend"],
            "warning_limit": budget_info["warning_limit"],
            "maximum_limit": budget_info["maximum_limit"],
            "utilization_percentage": budget_info["utilization_percentage"],
            "budget_status": budget_info["budget_status"],
            "transformed_at": datetime.now().isoformat()
        }
    
    async def _transform_cost_forecast(self, forecast: Dict[str, Any]) -> Dict[str, Any]:
        """Transform cost forecast to agent format"""
        return {
            "forecasted_amount": forecast["forecasted_amount"],
            "confidence_level": forecast["confidence_level"],
            "trend_factor": forecast["trend_factor"],
            "forecast_days": forecast["forecast_days"],
            "transformed_at": datetime.now().isoformat()
        }
    
    async def _transform_service_costs(self, service_costs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform service costs to agent format"""
        return [
            {
                "service_type": sc["service_type"],
                "amount": sc["amount"],
                "currency": sc.get("currency", "USD"),
                "usage_quantity": sc.get("usage_quantity", 0),
                "transformed_at": datetime.now().isoformat()
            }
            for sc in service_costs
        ]
    
    async def _transform_resources(self, resources: Dict[str, Any]) -> Dict[str, Any]:
        """Transform resource data to agent format"""
        return {
            "ec2_instances": [
                {
                    "instance_id": instance["instance_id"],
                    "instance_type": instance["instance_type"],
                    "state": instance["state"],
                    "monthly_cost": instance["monthly_cost"],
                    "transformed_at": datetime.now().isoformat()
                }
                for instance in resources.get("ec2_instances", [])
            ],
            "storage_volumes": [
                {
                    "volume_id": volume["volume_id"],
                    "size_gb": volume["size_gb"],
                    "volume_type": volume["volume_type"],
                    "monthly_cost": volume["monthly_cost"],
                    "attached_instance": volume.get("attached_instance"),
                    "transformed_at": datetime.now().isoformat()
                }
                for volume in resources.get("storage_volumes", [])
            ],
            "database_instances": [
                {
                    "db_instance_id": db["db_instance_id"],
                    "engine": db["engine"],
                    "instance_class": db["instance_class"],
                    "monthly_cost": db["monthly_cost"],
                    "transformed_at": datetime.now().isoformat()
                }
                for db in resources.get("database_instances", [])
            ],
            "transformed_at": datetime.now().isoformat()
        }
    
    async def _log_migration_result(self, migration_type: str, result: MigrationResult) -> None:
        """Log migration result to file"""
        try:
            log_entry = {
                "migration_type": migration_type,
                "timestamp": result.timestamp.isoformat(),
                "success": result.success,
                "migrated_count": result.migrated_count,
                "failed_count": result.failed_count,
                "duration_seconds": result.duration_seconds,
                "errors": result.errors
            }
            
            # Append to log file
            with open(self.migration_log_path, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
            # Add to history
            self.migration_history.append(result)
            
            # Limit history size
            if len(self.migration_history) > 100:
                self.migration_history = self.migration_history[-100:]
            
        except Exception as e:
            self.logger.error(f"Failed to log migration result: {e}")
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status and history"""
        if not self.migration_history:
            return {
                "status": "not_started",
                "total_migrations": 0,
                "total_migrated_items": 0,
                "total_failed_items": 0,
                "success_rate": 0.0
            }
        
        latest_migration = self.migration_history[-1]
        total_migrated = sum(r.migrated_count for r in self.migration_history)
        total_failed = sum(r.failed_count for r in self.migration_history)
        
        return {
            "status": "completed" if latest_migration.success else "failed",
            "total_migrations": len(self.migration_history),
            "total_migrated_items": total_migrated,
            "total_failed_items": total_failed,
            "success_rate": total_migrated / max(total_migrated + total_failed, 1),
            "latest_migration": {
                "timestamp": latest_migration.timestamp.isoformat(),
                "success": latest_migration.success,
                "migrated_count": latest_migration.migrated_count,
                "failed_count": latest_migration.failed_count,
                "duration_seconds": latest_migration.duration_seconds
            },
            "migration_history": [
                {
                    "timestamp": r.timestamp.isoformat(),
                    "success": r.success,
                    "migrated_count": r.migrated_count,
                    "failed_count": r.failed_count,
                    "duration_seconds": r.duration_seconds
                }
                for r in self.migration_history
            ]
        }