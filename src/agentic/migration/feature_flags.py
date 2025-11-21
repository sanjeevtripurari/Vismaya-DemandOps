"""
Feature Flags System for Agentic AI Migration
Enables gradual rollout of agentic capabilities with fine-grained control
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Set, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path


class RolloutStrategy(Enum):
    """Rollout strategies for feature flags"""
    PERCENTAGE = "percentage"
    USER_LIST = "user_list"
    TIME_BASED = "time_based"
    CONDITIONAL = "conditional"
    A_B_TEST = "a_b_test"


@dataclass
class FeatureFlag:
    """Feature flag configuration"""
    name: str
    description: str
    enabled: bool = False
    rollout_strategy: RolloutStrategy = RolloutStrategy.PERCENTAGE
    rollout_percentage: float = 0.0
    target_users: List[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    conditions: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.target_users is None:
            self.target_users = []
        if self.conditions is None:
            self.conditions = {}
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


@dataclass
class FeatureEvaluation:
    """Result of feature flag evaluation"""
    feature_name: str
    enabled: bool
    reason: str
    user_id: Optional[str] = None
    context: Dict[str, Any] = None
    evaluation_time: datetime = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}
        if self.evaluation_time is None:
            self.evaluation_time = datetime.now()


class FeatureFlagManager:
    """
    Manages feature flags for gradual rollout of agentic capabilities
    Supports multiple rollout strategies and real-time flag updates
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Feature flags storage
        self.flags: Dict[str, FeatureFlag] = {}
        self.flag_file_path = config.get("flag_file_path", "config/feature_flags.json")
        
        # Evaluation tracking
        self.evaluations: List[FeatureEvaluation] = []
        self.max_evaluations = config.get("max_evaluations", 10000)
        
        # Callbacks for flag changes
        self.flag_change_callbacks: Dict[str, List[Callable]] = {}
        
        # Initialize default flags
        self._initialize_default_flags()
        
        # Load flags from file
        asyncio.create_task(self._load_flags_from_file())
    
    def _initialize_default_flags(self) -> None:
        """Initialize default feature flags for agentic system"""
        
        default_flags = {
            "agentic_cost_analysis": FeatureFlag(
                name="agentic_cost_analysis",
                description="Use agentic cost analysis instead of legacy service",
                enabled=False,
                rollout_strategy=RolloutStrategy.PERCENTAGE,
                rollout_percentage=0.0,
                metadata={
                    "category": "core_functionality",
                    "impact": "high",
                    "dependencies": ["cost_management_agent"]
                }
            ),
            "agentic_resource_management": FeatureFlag(
                name="agentic_resource_management",
                description="Use agentic resource management instead of legacy service",
                enabled=False,
                rollout_strategy=RolloutStrategy.PERCENTAGE,
                rollout_percentage=0.0,
                metadata={
                    "category": "core_functionality",
                    "impact": "high",
                    "dependencies": ["resource_management_agent"]
                }
            ),
            "agentic_forecasting": FeatureFlag(
                name="agentic_forecasting",
                description="Use agentic forecasting instead of legacy service",
                enabled=False,
                rollout_strategy=RolloutStrategy.PERCENTAGE,
                rollout_percentage=0.0,
                metadata={
                    "category": "core_functionality",
                    "impact": "medium",
                    "dependencies": ["forecasting_agent"]
                }
            ),
            "agentic_dashboard": FeatureFlag(
                name="agentic_dashboard",
                description="Use agentic dashboard backend",
                enabled=False,
                rollout_strategy=RolloutStrategy.PERCENTAGE,
                rollout_percentage=0.0,
                metadata={
                    "category": "user_interface",
                    "impact": "high",
                    "dependencies": ["orchestrator_agent", "user_interface_agent"]
                }
            ),
            "approval_workflows": FeatureFlag(
                name="approval_workflows",
                description="Enable approval workflow functionality",
                enabled=False,
                rollout_strategy=RolloutStrategy.USER_LIST,
                target_users=["admin", "ceo", "cto"],
                metadata={
                    "category": "governance",
                    "impact": "medium",
                    "dependencies": ["approval_agent"]
                }
            ),
            "real_time_decisions": FeatureFlag(
                name="real_time_decisions",
                description="Enable real-time decision tracking and notifications",
                enabled=False,
                rollout_strategy=RolloutStrategy.PERCENTAGE,
                rollout_percentage=0.0,
                metadata={
                    "category": "governance",
                    "impact": "low",
                    "dependencies": ["approval_agent", "notification_system"]
                }
            ),
            "enhanced_ai_assistant": FeatureFlag(
                name="enhanced_ai_assistant",
                description="Use enhanced AI assistant with multi-agent coordination",
                enabled=False,
                rollout_strategy=RolloutStrategy.PERCENTAGE,
                rollout_percentage=0.0,
                metadata={
                    "category": "ai_features",
                    "impact": "medium",
                    "dependencies": ["user_interface_agent", "orchestrator_agent"]
                }
            ),
            "cost_optimization_recommendations": FeatureFlag(
                name="cost_optimization_recommendations",
                description="Enable AI-powered cost optimization recommendations",
                enabled=False,
                rollout_strategy=RolloutStrategy.PERCENTAGE,
                rollout_percentage=0.0,
                metadata={
                    "category": "ai_features",
                    "impact": "medium",
                    "dependencies": ["cost_management_agent", "resource_management_agent"]
                }
            ),
            "predictive_alerts": FeatureFlag(
                name="predictive_alerts",
                description="Enable predictive cost and resource alerts",
                enabled=False,
                rollout_strategy=RolloutStrategy.PERCENTAGE,
                rollout_percentage=0.0,
                metadata={
                    "category": "monitoring",
                    "impact": "low",
                    "dependencies": ["alert_management_agent", "forecasting_agent"]
                }
            ),
            "multi_agent_collaboration": FeatureFlag(
                name="multi_agent_collaboration",
                description="Enable advanced multi-agent collaboration features",
                enabled=False,
                rollout_strategy=RolloutStrategy.USER_LIST,
                target_users=["admin"],
                metadata={
                    "category": "advanced_features",
                    "impact": "high",
                    "dependencies": ["orchestrator_agent", "mcp_server", "strands_framework"]
                }
            )
        }
        
        self.flags.update(default_flags)
    
    async def _load_flags_from_file(self) -> None:
        """Load feature flags from configuration file"""
        
        try:
            flag_file = Path(self.flag_file_path)
            
            if flag_file.exists():
                with open(flag_file, 'r') as f:
                    flag_data = json.load(f)
                
                # Update flags from file
                for flag_name, flag_config in flag_data.items():
                    if flag_name in self.flags:
                        # Update existing flag
                        flag = self.flags[flag_name]
                        flag.enabled = flag_config.get("enabled", flag.enabled)
                        flag.rollout_percentage = flag_config.get("rollout_percentage", flag.rollout_percentage)
                        flag.target_users = flag_config.get("target_users", flag.target_users)
                        flag.conditions = flag_config.get("conditions", flag.conditions)
                        flag.updated_at = datetime.now()
                    else:
                        # Create new flag from file
                        self.flags[flag_name] = FeatureFlag(
                            name=flag_name,
                            description=flag_config.get("description", ""),
                            enabled=flag_config.get("enabled", False),
                            rollout_strategy=RolloutStrategy(flag_config.get("rollout_strategy", "percentage")),
                            rollout_percentage=flag_config.get("rollout_percentage", 0.0),
                            target_users=flag_config.get("target_users", []),
                            conditions=flag_config.get("conditions", {})
                        )
                
                self.logger.info(f"Loaded {len(flag_data)} feature flags from {flag_file}")
            
        except Exception as e:
            self.logger.error(f"Error loading feature flags from file: {e}")
    
    async def _save_flags_to_file(self) -> None:
        """Save feature flags to configuration file"""
        
        try:
            flag_file = Path(self.flag_file_path)
            flag_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert flags to serializable format
            flag_data = {}
            for flag_name, flag in self.flags.items():
                flag_data[flag_name] = {
                    "description": flag.description,
                    "enabled": flag.enabled,
                    "rollout_strategy": flag.rollout_strategy.value,
                    "rollout_percentage": flag.rollout_percentage,
                    "target_users": flag.target_users,
                    "conditions": flag.conditions,
                    "metadata": flag.metadata,
                    "updated_at": flag.updated_at.isoformat()
                }
            
            with open(flag_file, 'w') as f:
                json.dump(flag_data, f, indent=2, default=str)
            
            self.logger.info(f"Saved {len(flag_data)} feature flags to {flag_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving feature flags to file: {e}")
    
    def is_enabled(self, feature_name: str, user_id: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if a feature is enabled for a user/context"""
        
        evaluation = self.evaluate_flag(feature_name, user_id, context)
        return evaluation.enabled
    
    def evaluate_flag(self, feature_name: str, user_id: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> FeatureEvaluation:
        """Evaluate a feature flag and return detailed result"""
        
        if context is None:
            context = {}
        
        # Check if flag exists
        if feature_name not in self.flags:
            evaluation = FeatureEvaluation(
                feature_name=feature_name,
                enabled=False,
                reason="flag_not_found",
                user_id=user_id,
                context=context
            )
            self._track_evaluation(evaluation)
            return evaluation
        
        flag = self.flags[feature_name]
        
        # Check if flag is globally disabled
        if not flag.enabled:
            evaluation = FeatureEvaluation(
                feature_name=feature_name,
                enabled=False,
                reason="globally_disabled",
                user_id=user_id,
                context=context
            )
            self._track_evaluation(evaluation)
            return evaluation
        
        # Evaluate based on rollout strategy
        if flag.rollout_strategy == RolloutStrategy.PERCENTAGE:
            enabled = self._evaluate_percentage_rollout(flag, user_id)
            reason = "percentage_rollout"
        
        elif flag.rollout_strategy == RolloutStrategy.USER_LIST:
            enabled = self._evaluate_user_list_rollout(flag, user_id)
            reason = "user_list_rollout"
        
        elif flag.rollout_strategy == RolloutStrategy.TIME_BASED:
            enabled = self._evaluate_time_based_rollout(flag)
            reason = "time_based_rollout"
        
        elif flag.rollout_strategy == RolloutStrategy.CONDITIONAL:
            enabled = self._evaluate_conditional_rollout(flag, context)
            reason = "conditional_rollout"
        
        elif flag.rollout_strategy == RolloutStrategy.A_B_TEST:
            enabled = self._evaluate_ab_test_rollout(flag, user_id, context)
            reason = "ab_test_rollout"
        
        else:
            enabled = False
            reason = "unknown_strategy"
        
        evaluation = FeatureEvaluation(
            feature_name=feature_name,
            enabled=enabled,
            reason=reason,
            user_id=user_id,
            context=context
        )
        
        self._track_evaluation(evaluation)
        return evaluation
    
    def _evaluate_percentage_rollout(self, flag: FeatureFlag, user_id: Optional[str]) -> bool:
        """Evaluate percentage-based rollout"""
        
        if flag.rollout_percentage >= 100.0:
            return True
        
        if flag.rollout_percentage <= 0.0:
            return False
        
        if not user_id:
            # Use random rollout if no user ID
            import random
            return random.random() * 100 <= flag.rollout_percentage
        
        # Use consistent hash-based rollout
        import hashlib
        hash_input = f"{flag.name}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest()[:8], 16)
        percentage = (hash_value % 100) + 1
        
        return percentage <= flag.rollout_percentage
    
    def _evaluate_user_list_rollout(self, flag: FeatureFlag, user_id: Optional[str]) -> bool:
        """Evaluate user list-based rollout"""
        
        if not user_id:
            return False
        
        return user_id in flag.target_users
    
    def _evaluate_time_based_rollout(self, flag: FeatureFlag) -> bool:
        """Evaluate time-based rollout"""
        
        now = datetime.now()
        
        if flag.start_time and now < flag.start_time:
            return False
        
        if flag.end_time and now > flag.end_time:
            return False
        
        return True
    
    def _evaluate_conditional_rollout(self, flag: FeatureFlag, context: Dict[str, Any]) -> bool:
        """Evaluate conditional rollout based on context"""
        
        if not flag.conditions:
            return True
        
        # Simple condition evaluation
        for condition_key, expected_value in flag.conditions.items():
            if condition_key not in context:
                return False
            
            actual_value = context[condition_key]
            
            if isinstance(expected_value, dict):
                # Complex condition (e.g., {"operator": ">=", "value": 10})
                operator = expected_value.get("operator", "==")
                value = expected_value.get("value")
                
                if operator == "==" and actual_value != value:
                    return False
                elif operator == "!=" and actual_value == value:
                    return False
                elif operator == ">" and actual_value <= value:
                    return False
                elif operator == ">=" and actual_value < value:
                    return False
                elif operator == "<" and actual_value >= value:
                    return False
                elif operator == "<=" and actual_value > value:
                    return False
                elif operator == "in" and actual_value not in value:
                    return False
                elif operator == "not_in" and actual_value in value:
                    return False
            
            else:
                # Simple equality check
                if actual_value != expected_value:
                    return False
        
        return True
    
    def _evaluate_ab_test_rollout(self, flag: FeatureFlag, user_id: Optional[str], context: Dict[str, Any]) -> bool:
        """Evaluate A/B test rollout"""
        
        # A/B test logic - assign users to groups based on hash
        if not user_id:
            return False
        
        import hashlib
        hash_input = f"{flag.name}:ab_test:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest()[:8], 16)
        group = "A" if hash_value % 2 == 0 else "B"
        
        # Check if this group should have the feature enabled
        ab_config = flag.conditions.get("ab_test", {})
        enabled_groups = ab_config.get("enabled_groups", ["A"])
        
        return group in enabled_groups
    
    def _track_evaluation(self, evaluation: FeatureEvaluation) -> None:
        """Track feature flag evaluation for analytics"""
        
        self.evaluations.append(evaluation)
        
        # Limit evaluation history
        if len(self.evaluations) > self.max_evaluations:
            self.evaluations = self.evaluations[-self.max_evaluations:]
    
    async def enable_flag(self, feature_name: str, rollout_percentage: float = 100.0) -> bool:
        """Enable a feature flag"""
        
        if feature_name not in self.flags:
            return False
        
        flag = self.flags[feature_name]
        flag.enabled = True
        flag.rollout_percentage = rollout_percentage
        flag.updated_at = datetime.now()
        
        # Save to file
        await self._save_flags_to_file()
        
        # Notify callbacks
        await self._notify_flag_change(feature_name, flag)
        
        self.logger.info(f"Enabled feature flag: {feature_name} ({rollout_percentage}%)")
        return True
    
    async def disable_flag(self, feature_name: str) -> bool:
        """Disable a feature flag"""
        
        if feature_name not in self.flags:
            return False
        
        flag = self.flags[feature_name]
        flag.enabled = False
        flag.updated_at = datetime.now()
        
        # Save to file
        await self._save_flags_to_file()
        
        # Notify callbacks
        await self._notify_flag_change(feature_name, flag)
        
        self.logger.info(f"Disabled feature flag: {feature_name}")
        return True
    
    async def update_rollout_percentage(self, feature_name: str, percentage: float) -> bool:
        """Update rollout percentage for a feature flag"""
        
        if feature_name not in self.flags:
            return False
        
        flag = self.flags[feature_name]
        flag.rollout_percentage = max(0.0, min(100.0, percentage))
        flag.updated_at = datetime.now()
        
        # Save to file
        await self._save_flags_to_file()
        
        # Notify callbacks
        await self._notify_flag_change(feature_name, flag)
        
        self.logger.info(f"Updated rollout percentage for {feature_name}: {percentage}%")
        return True
    
    async def add_target_user(self, feature_name: str, user_id: str) -> bool:
        """Add user to target list for a feature flag"""
        
        if feature_name not in self.flags:
            return False
        
        flag = self.flags[feature_name]
        if user_id not in flag.target_users:
            flag.target_users.append(user_id)
            flag.updated_at = datetime.now()
            
            # Save to file
            await self._save_flags_to_file()
            
            # Notify callbacks
            await self._notify_flag_change(feature_name, flag)
            
            self.logger.info(f"Added user {user_id} to feature flag: {feature_name}")
        
        return True
    
    async def remove_target_user(self, feature_name: str, user_id: str) -> bool:
        """Remove user from target list for a feature flag"""
        
        if feature_name not in self.flags:
            return False
        
        flag = self.flags[feature_name]
        if user_id in flag.target_users:
            flag.target_users.remove(user_id)
            flag.updated_at = datetime.now()
            
            # Save to file
            await self._save_flags_to_file()
            
            # Notify callbacks
            await self._notify_flag_change(feature_name, flag)
            
            self.logger.info(f"Removed user {user_id} from feature flag: {feature_name}")
        
        return True
    
    def register_flag_change_callback(self, feature_name: str, callback: Callable[[str, FeatureFlag], None]) -> None:
        """Register callback for feature flag changes"""
        
        if feature_name not in self.flag_change_callbacks:
            self.flag_change_callbacks[feature_name] = []
        
        self.flag_change_callbacks[feature_name].append(callback)
    
    async def _notify_flag_change(self, feature_name: str, flag: FeatureFlag) -> None:
        """Notify callbacks about feature flag changes"""
        
        callbacks = self.flag_change_callbacks.get(feature_name, [])
        
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(feature_name, flag)
                else:
                    callback(feature_name, flag)
            except Exception as e:
                self.logger.error(f"Error in flag change callback for {feature_name}: {e}")
    
    def get_flag_status(self, feature_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed status of a feature flag"""
        
        if feature_name not in self.flags:
            return None
        
        flag = self.flags[feature_name]
        
        # Calculate evaluation statistics
        flag_evaluations = [e for e in self.evaluations if e.feature_name == feature_name]
        total_evaluations = len(flag_evaluations)
        enabled_evaluations = sum(1 for e in flag_evaluations if e.enabled)
        
        return {
            "name": flag.name,
            "description": flag.description,
            "enabled": flag.enabled,
            "rollout_strategy": flag.rollout_strategy.value,
            "rollout_percentage": flag.rollout_percentage,
            "target_users": flag.target_users,
            "conditions": flag.conditions,
            "metadata": flag.metadata,
            "created_at": flag.created_at.isoformat(),
            "updated_at": flag.updated_at.isoformat(),
            "statistics": {
                "total_evaluations": total_evaluations,
                "enabled_evaluations": enabled_evaluations,
                "enabled_rate": enabled_evaluations / max(total_evaluations, 1)
            }
        }
    
    def get_all_flags_status(self) -> Dict[str, Any]:
        """Get status of all feature flags"""
        
        return {
            flag_name: self.get_flag_status(flag_name)
            for flag_name in self.flags.keys()
        }
    
    def get_evaluation_analytics(self, hours: int = 24) -> Dict[str, Any]:
        """Get analytics for feature flag evaluations"""
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_evaluations = [e for e in self.evaluations if e.evaluation_time >= cutoff_time]
        
        # Group by feature
        feature_stats = {}
        for evaluation in recent_evaluations:
            feature_name = evaluation.feature_name
            
            if feature_name not in feature_stats:
                feature_stats[feature_name] = {
                    "total": 0,
                    "enabled": 0,
                    "reasons": {}
                }
            
            feature_stats[feature_name]["total"] += 1
            
            if evaluation.enabled:
                feature_stats[feature_name]["enabled"] += 1
            
            reason = evaluation.reason
            if reason not in feature_stats[feature_name]["reasons"]:
                feature_stats[feature_name]["reasons"][reason] = 0
            feature_stats[feature_name]["reasons"][reason] += 1
        
        # Calculate rates
        for stats in feature_stats.values():
            stats["enabled_rate"] = stats["enabled"] / max(stats["total"], 1)
        
        return {
            "time_period_hours": hours,
            "total_evaluations": len(recent_evaluations),
            "feature_statistics": feature_stats,
            "generated_at": datetime.now().isoformat()
        }