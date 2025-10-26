"""
Graceful Degradation Manager
Handles partial system failures by providing degraded but functional service
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field

from .models import AgentStatus, SystemHealth


class ServiceLevel(Enum):
    """Service levels for graceful degradation"""
    FULL = "full"
    DEGRADED = "degraded"
    MINIMAL = "minimal"
    EMERGENCY = "emergency"
    OFFLINE = "offline"


class FeatureCategory(Enum):
    """Categories of features for degradation prioritization"""
    CRITICAL = "critical"        # Must always work
    IMPORTANT = "important"      # Should work if possible
    NICE_TO_HAVE = "nice_to_have"  # Can be disabled
    OPTIONAL = "optional"        # First to be disabled


@dataclass
class Feature:
    """Represents a system feature that can be degraded"""
    name: str
    category: FeatureCategory
    dependencies: List[str] = field(default_factory=list)
    resource_cost: float = 1.0  # Relative resource cost
    user_impact: float = 1.0    # Impact on user experience (1-10)
    enabled: bool = True
    degraded: bool = False
    last_check: Optional[datetime] = None
    
    def can_be_disabled(self) -> bool:
        """Check if feature can be safely disabled"""
        return self.category in [FeatureCategory.NICE_TO_HAVE, FeatureCategory.OPTIONAL]
    
    def should_be_prioritized(self) -> bool:
        """Check if feature should be prioritized for resources"""
        return self.category == FeatureCategory.CRITICAL


@dataclass
class DegradationRule:
    """Rule for when and how to degrade services"""
    name: str
    condition: str  # Condition that triggers degradation
    target_service_level: ServiceLevel
    features_to_disable: List[str] = field(default_factory=list)
    features_to_degrade: List[str] = field(default_factory=list)
    priority: int = 1  # Higher priority rules are evaluated first
    cooldown_minutes: int = 5  # Minimum time between applications
    last_applied: Optional[datetime] = None
    
    def can_apply(self) -> bool:
        """Check if rule can be applied (considering cooldown)"""
        if self.last_applied is None:
            return True
        
        return datetime.now() - self.last_applied > timedelta(minutes=self.cooldown_minutes)


class GracefulDegradationManager:
    """
    Manages graceful degradation of system services during partial failures
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Current service level
        self.current_service_level = ServiceLevel.FULL
        self.target_service_level = ServiceLevel.FULL
        
        # Feature management
        self.features: Dict[str, Feature] = {}
        self.feature_dependencies: Dict[str, Set[str]] = {}
        
        # Degradation rules
        self.degradation_rules: List[DegradationRule] = []
        self.recovery_rules: List[DegradationRule] = []
        
        # System state tracking
        self.system_health: Optional[SystemHealth] = None
        self.agent_statuses: Dict[str, AgentStatus] = {}
        self.resource_utilization: Dict[str, float] = {}
        
        # Degradation history
        self.degradation_history: List[Dict[str, Any]] = []
        self.current_degradations: Dict[str, Any] = {}
        
        # Monitoring
        self._monitoring_task: Optional[asyncio.Task] = None
        self._recovery_task: Optional[asyncio.Task] = None
        
        # Initialize features and rules
        self._initialize_features()
        self._initialize_degradation_rules()
        
        # Start monitoring if event loop is available
        try:
            self._start_monitoring()
        except RuntimeError:
            # No event loop available (e.g., during testing)
            pass
    
    def _initialize_features(self) -> None:
        """Initialize system features with their categories and dependencies"""
        default_features = {
            # Critical features - must always work
            "user_authentication": Feature(
                name="user_authentication",
                category=FeatureCategory.CRITICAL,
                dependencies=[],
                resource_cost=0.5,
                user_impact=10.0
            ),
            "basic_cost_tracking": Feature(
                name="basic_cost_tracking",
                category=FeatureCategory.CRITICAL,
                dependencies=["user_authentication"],
                resource_cost=1.0,
                user_impact=9.0
            ),
            "emergency_alerts": Feature(
                name="emergency_alerts",
                category=FeatureCategory.CRITICAL,
                dependencies=["user_authentication"],
                resource_cost=0.5,
                user_impact=8.0
            ),
            
            # Important features - should work if possible
            "real_time_monitoring": Feature(
                name="real_time_monitoring",
                category=FeatureCategory.IMPORTANT,
                dependencies=["basic_cost_tracking"],
                resource_cost=2.0,
                user_impact=7.0
            ),
            "cost_forecasting": Feature(
                name="cost_forecasting",
                category=FeatureCategory.IMPORTANT,
                dependencies=["basic_cost_tracking"],
                resource_cost=3.0,
                user_impact=6.0
            ),
            "approval_workflows": Feature(
                name="approval_workflows",
                category=FeatureCategory.IMPORTANT,
                dependencies=["user_authentication"],
                resource_cost=1.5,
                user_impact=7.0
            ),
            
            # Nice to have features
            "advanced_analytics": Feature(
                name="advanced_analytics",
                category=FeatureCategory.NICE_TO_HAVE,
                dependencies=["basic_cost_tracking", "cost_forecasting"],
                resource_cost=4.0,
                user_impact=5.0
            ),
            "custom_dashboards": Feature(
                name="custom_dashboards",
                category=FeatureCategory.NICE_TO_HAVE,
                dependencies=["user_authentication"],
                resource_cost=2.5,
                user_impact=4.0
            ),
            "detailed_reporting": Feature(
                name="detailed_reporting",
                category=FeatureCategory.NICE_TO_HAVE,
                dependencies=["basic_cost_tracking"],
                resource_cost=3.5,
                user_impact=5.0
            ),
            
            # Optional features - first to be disabled
            "ai_recommendations": Feature(
                name="ai_recommendations",
                category=FeatureCategory.OPTIONAL,
                dependencies=["cost_forecasting", "advanced_analytics"],
                resource_cost=5.0,
                user_impact=3.0
            ),
            "export_features": Feature(
                name="export_features",
                category=FeatureCategory.OPTIONAL,
                dependencies=["basic_cost_tracking"],
                resource_cost=1.0,
                user_impact=2.0
            ),
            "theme_customization": Feature(
                name="theme_customization",
                category=FeatureCategory.OPTIONAL,
                dependencies=["user_authentication"],
                resource_cost=0.5,
                user_impact=1.0
            )
        }
        
        # Merge with configuration
        features_config = self.config.get("features", {})
        for feature_name, feature_data in features_config.items():
            if feature_name in default_features:
                # Update existing feature
                feature = default_features[feature_name]
                if "category" in feature_data:
                    feature.category = FeatureCategory(feature_data["category"])
                if "resource_cost" in feature_data:
                    feature.resource_cost = feature_data["resource_cost"]
                if "user_impact" in feature_data:
                    feature.user_impact = feature_data["user_impact"]
            else:
                # Add new feature
                default_features[feature_name] = Feature(
                    name=feature_name,
                    category=FeatureCategory(feature_data.get("category", "optional")),
                    dependencies=feature_data.get("dependencies", []),
                    resource_cost=feature_data.get("resource_cost", 1.0),
                    user_impact=feature_data.get("user_impact", 1.0)
                )
        
        self.features = default_features
        
        # Build dependency graph
        self._build_dependency_graph()
        
        self.logger.info(f"Initialized {len(self.features)} features for graceful degradation")
    
    def _build_dependency_graph(self) -> None:
        """Build feature dependency graph"""
        self.feature_dependencies = {}
        
        for feature_name, feature in self.features.items():
            self.feature_dependencies[feature_name] = set()
            
            # Add direct dependencies
            for dep in feature.dependencies:
                if dep in self.features:
                    self.feature_dependencies[feature_name].add(dep)
            
            # Add transitive dependencies
            self._add_transitive_dependencies(feature_name, set())
    
    def _add_transitive_dependencies(self, feature_name: str, visited: Set[str]) -> None:
        """Add transitive dependencies for a feature"""
        if feature_name in visited:
            return  # Avoid cycles
        
        visited.add(feature_name)
        feature = self.features[feature_name]
        
        for dep in feature.dependencies:
            if dep in self.features:
                self.feature_dependencies[feature_name].add(dep)
                
                # Add dependencies of dependencies
                self._add_transitive_dependencies(dep, visited.copy())
                self.feature_dependencies[feature_name].update(
                    self.feature_dependencies.get(dep, set())
                )
    
    def _initialize_degradation_rules(self) -> None:
        """Initialize degradation and recovery rules"""
        default_degradation_rules = [
            # High resource utilization
            DegradationRule(
                name="high_cpu_usage",
                condition="cpu_usage > 80",
                target_service_level=ServiceLevel.DEGRADED,
                features_to_disable=["ai_recommendations", "theme_customization"],
                features_to_degrade=["advanced_analytics"],
                priority=3,
                cooldown_minutes=2
            ),
            
            # Multiple agent failures
            DegradationRule(
                name="multiple_agent_failures",
                condition="failed_agents >= 2",
                target_service_level=ServiceLevel.MINIMAL,
                features_to_disable=["ai_recommendations", "export_features", "custom_dashboards"],
                features_to_degrade=["real_time_monitoring", "detailed_reporting"],
                priority=5,
                cooldown_minutes=1
            ),
            
            # Critical agent failure
            DegradationRule(
                name="critical_agent_failure",
                condition="cost_management_agent_failed",
                target_service_level=ServiceLevel.EMERGENCY,
                features_to_disable=["cost_forecasting", "advanced_analytics", "ai_recommendations"],
                features_to_degrade=["real_time_monitoring"],
                priority=8,
                cooldown_minutes=0
            ),
            
            # System overload
            DegradationRule(
                name="system_overload",
                condition="memory_usage > 90 or error_rate > 50",
                target_service_level=ServiceLevel.EMERGENCY,
                features_to_disable=["ai_recommendations", "advanced_analytics", "detailed_reporting"],
                features_to_degrade=["real_time_monitoring", "custom_dashboards"],
                priority=7,
                cooldown_minutes=0
            )
        ]
        
        # Recovery rules (opposite conditions)
        default_recovery_rules = [
            DegradationRule(
                name="cpu_usage_normal",
                condition="cpu_usage < 60",
                target_service_level=ServiceLevel.FULL,
                priority=1,
                cooldown_minutes=5
            ),
            
            DegradationRule(
                name="agents_recovered",
                condition="failed_agents < 1",
                target_service_level=ServiceLevel.FULL,
                priority=2,
                cooldown_minutes=3
            ),
            
            DegradationRule(
                name="system_stable",
                condition="memory_usage < 70 and error_rate < 10",
                target_service_level=ServiceLevel.DEGRADED,
                priority=3,
                cooldown_minutes=2
            )
        ]
        
        # Merge with configuration
        rules_config = self.config.get("degradation_rules", [])
        self.degradation_rules = default_degradation_rules + [
            DegradationRule(**rule) for rule in rules_config
        ]
        
        recovery_config = self.config.get("recovery_rules", [])
        self.recovery_rules = default_recovery_rules + [
            DegradationRule(**rule) for rule in recovery_config
        ]
        
        # Sort by priority (higher first)
        self.degradation_rules.sort(key=lambda r: r.priority, reverse=True)
        self.recovery_rules.sort(key=lambda r: r.priority, reverse=True)
        
        self.logger.info(f"Initialized {len(self.degradation_rules)} degradation rules and "
                        f"{len(self.recovery_rules)} recovery rules")
    
    def _start_monitoring(self) -> None:
        """Start background monitoring tasks"""
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self._recovery_task = asyncio.create_task(self._recovery_loop())
    
    async def start_monitoring(self) -> None:
        """Start monitoring tasks (for use when event loop is available)"""
        if self._monitoring_task is None or self._monitoring_task.done():
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        if self._recovery_task is None or self._recovery_task.done():
            self._recovery_task = asyncio.create_task(self._recovery_loop())
    
    async def update_system_state(
        self, 
        system_health: SystemHealth, 
        agent_statuses: Dict[str, AgentStatus],
        resource_utilization: Dict[str, float]
    ) -> None:
        """Update system state for degradation decisions"""
        self.system_health = system_health
        self.agent_statuses = agent_statuses
        self.resource_utilization = resource_utilization
        
        # Trigger immediate evaluation
        await self._evaluate_degradation_rules()
    
    async def _evaluate_degradation_rules(self) -> None:
        """Evaluate degradation rules and apply if necessary"""
        try:
            current_conditions = self._get_current_conditions()
            
            # Check degradation rules
            for rule in self.degradation_rules:
                if rule.can_apply() and self._evaluate_condition(rule.condition, current_conditions):
                    if rule.target_service_level.value < self.current_service_level.value:
                        await self._apply_degradation_rule(rule)
                        break  # Apply only one rule at a time
            
            # Check recovery rules
            for rule in self.recovery_rules:
                if rule.can_apply() and self._evaluate_condition(rule.condition, current_conditions):
                    if rule.target_service_level.value > self.current_service_level.value:
                        await self._apply_recovery_rule(rule)
                        break  # Apply only one rule at a time
                        
        except Exception as e:
            self.logger.error(f"Error evaluating degradation rules: {e}")
    
    def _get_current_conditions(self) -> Dict[str, Any]:
        """Get current system conditions for rule evaluation"""
        conditions = {
            "cpu_usage": self.resource_utilization.get("cpu_usage", 0),
            "memory_usage": self.resource_utilization.get("memory_usage", 0),
            "error_rate": self.resource_utilization.get("error_rate", 0),
            "failed_agents": sum(1 for status in self.agent_statuses.values() 
                               if status in [AgentStatus.ERROR, AgentStatus.OFFLINE]),
            "total_agents": len(self.agent_statuses),
            "cost_management_agent_failed": self.agent_statuses.get("cost_management", AgentStatus.OFFLINE) 
                                          in [AgentStatus.ERROR, AgentStatus.OFFLINE]
        }
        
        return conditions
    
    def _evaluate_condition(self, condition: str, current_conditions: Dict[str, Any]) -> bool:
        """Evaluate a condition string against current conditions"""
        try:
            # Simple condition evaluation (in production, use a proper expression evaluator)
            for var_name, value in current_conditions.items():
                condition = condition.replace(var_name, str(value))
            
            # Basic operators
            condition = condition.replace(" and ", " and ")
            condition = condition.replace(" or ", " or ")
            
            # Evaluate (this is simplified - use ast.literal_eval or similar in production)
            return eval(condition)
            
        except Exception as e:
            self.logger.error(f"Error evaluating condition '{condition}': {e}")
            return False
    
    async def _apply_degradation_rule(self, rule: DegradationRule) -> None:
        """Apply a degradation rule"""
        try:
            self.logger.warning(f"Applying degradation rule: {rule.name}")
            
            # Update service level
            old_level = self.current_service_level
            self.current_service_level = rule.target_service_level
            
            # Disable features
            for feature_name in rule.features_to_disable:
                if feature_name in self.features:
                    await self._disable_feature(feature_name)
            
            # Degrade features
            for feature_name in rule.features_to_degrade:
                if feature_name in self.features:
                    await self._degrade_feature(feature_name)
            
            # Record degradation
            degradation_record = {
                "rule_name": rule.name,
                "timestamp": datetime.now().isoformat(),
                "old_service_level": old_level.value,
                "new_service_level": self.current_service_level.value,
                "features_disabled": rule.features_to_disable,
                "features_degraded": rule.features_to_degrade,
                "trigger_conditions": self._get_current_conditions()
            }
            
            self.degradation_history.append(degradation_record)
            self.current_degradations[rule.name] = degradation_record
            
            # Update rule application time
            rule.last_applied = datetime.now()
            
            self.logger.info(f"Applied degradation rule {rule.name}: {old_level.value} -> {self.current_service_level.value}")
            
        except Exception as e:
            self.logger.error(f"Error applying degradation rule {rule.name}: {e}")
    
    async def _apply_recovery_rule(self, rule: DegradationRule) -> None:
        """Apply a recovery rule"""
        try:
            self.logger.info(f"Applying recovery rule: {rule.name}")
            
            # Update service level
            old_level = self.current_service_level
            self.current_service_level = rule.target_service_level
            
            # Re-enable features based on new service level
            await self._recover_features_for_service_level(self.current_service_level)
            
            # Clear current degradations
            self.current_degradations.clear()
            
            # Record recovery
            recovery_record = {
                "rule_name": rule.name,
                "timestamp": datetime.now().isoformat(),
                "old_service_level": old_level.value,
                "new_service_level": self.current_service_level.value,
                "recovery_conditions": self._get_current_conditions()
            }
            
            self.degradation_history.append(recovery_record)
            
            # Update rule application time
            rule.last_applied = datetime.now()
            
            self.logger.info(f"Applied recovery rule {rule.name}: {old_level.value} -> {self.current_service_level.value}")
            
        except Exception as e:
            self.logger.error(f"Error applying recovery rule {rule.name}: {e}")
    
    async def _disable_feature(self, feature_name: str) -> None:
        """Disable a feature and its dependents"""
        if feature_name not in self.features:
            return
        
        feature = self.features[feature_name]
        if not feature.enabled:
            return  # Already disabled
        
        self.logger.info(f"Disabling feature: {feature_name}")
        
        # Disable the feature
        feature.enabled = False
        feature.last_check = datetime.now()
        
        # Disable dependent features
        for dependent_name, dependent_feature in self.features.items():
            if feature_name in self.feature_dependencies.get(dependent_name, set()):
                if dependent_feature.enabled:
                    await self._disable_feature(dependent_name)
    
    async def _degrade_feature(self, feature_name: str) -> None:
        """Degrade a feature (reduce functionality but keep enabled)"""
        if feature_name not in self.features:
            return
        
        feature = self.features[feature_name]
        if feature.degraded:
            return  # Already degraded
        
        self.logger.info(f"Degrading feature: {feature_name}")
        
        feature.degraded = True
        feature.last_check = datetime.now()
    
    async def _recover_features_for_service_level(self, service_level: ServiceLevel) -> None:
        """Recover features appropriate for the service level"""
        # Define which features should be enabled for each service level
        service_level_features = {
            ServiceLevel.FULL: [FeatureCategory.CRITICAL, FeatureCategory.IMPORTANT, 
                              FeatureCategory.NICE_TO_HAVE, FeatureCategory.OPTIONAL],
            ServiceLevel.DEGRADED: [FeatureCategory.CRITICAL, FeatureCategory.IMPORTANT, 
                                  FeatureCategory.NICE_TO_HAVE],
            ServiceLevel.MINIMAL: [FeatureCategory.CRITICAL, FeatureCategory.IMPORTANT],
            ServiceLevel.EMERGENCY: [FeatureCategory.CRITICAL],
            ServiceLevel.OFFLINE: []
        }
        
        allowed_categories = service_level_features.get(service_level, [])
        
        # Enable/disable features based on service level
        for feature_name, feature in self.features.items():
            if feature.category in allowed_categories:
                # Check if dependencies are met
                if self._are_dependencies_met(feature_name):
                    if not feature.enabled:
                        self.logger.info(f"Re-enabling feature: {feature_name}")
                        feature.enabled = True
                    
                    # Remove degradation for full service
                    if service_level == ServiceLevel.FULL and feature.degraded:
                        self.logger.info(f"Removing degradation from feature: {feature_name}")
                        feature.degraded = False
            else:
                # Disable features not allowed at this service level
                if feature.enabled:
                    await self._disable_feature(feature_name)
    
    def _are_dependencies_met(self, feature_name: str) -> bool:
        """Check if all dependencies for a feature are met"""
        dependencies = self.feature_dependencies.get(feature_name, set())
        
        for dep_name in dependencies:
            if dep_name in self.features:
                if not self.features[dep_name].enabled:
                    return False
        
        return True
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current degradation status"""
        enabled_features = [name for name, feature in self.features.items() if feature.enabled]
        degraded_features = [name for name, feature in self.features.items() if feature.degraded]
        disabled_features = [name for name, feature in self.features.items() if not feature.enabled]
        
        return {
            "service_level": self.current_service_level.value,
            "target_service_level": self.target_service_level.value,
            "enabled_features": enabled_features,
            "degraded_features": degraded_features,
            "disabled_features": disabled_features,
            "active_degradations": list(self.current_degradations.keys()),
            "total_features": len(self.features),
            "feature_breakdown": {
                "critical": len([f for f in self.features.values() if f.category == FeatureCategory.CRITICAL]),
                "important": len([f for f in self.features.values() if f.category == FeatureCategory.IMPORTANT]),
                "nice_to_have": len([f for f in self.features.values() if f.category == FeatureCategory.NICE_TO_HAVE]),
                "optional": len([f for f in self.features.values() if f.category == FeatureCategory.OPTIONAL])
            }
        }
    
    def get_feature_status(self, feature_name: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific feature"""
        if feature_name not in self.features:
            return None
        
        feature = self.features[feature_name]
        dependencies = self.feature_dependencies.get(feature_name, set())
        
        return {
            "name": feature.name,
            "category": feature.category.value,
            "enabled": feature.enabled,
            "degraded": feature.degraded,
            "dependencies": list(dependencies),
            "resource_cost": feature.resource_cost,
            "user_impact": feature.user_impact,
            "last_check": feature.last_check.isoformat() if feature.last_check else None,
            "dependencies_met": self._are_dependencies_met(feature_name)
        }
    
    def get_degradation_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get degradation history"""
        return self.degradation_history[-limit:]
    
    async def force_service_level(self, service_level: ServiceLevel) -> bool:
        """Force a specific service level (for testing or manual intervention)"""
        try:
            self.logger.warning(f"Forcing service level to: {service_level.value}")
            
            old_level = self.current_service_level
            self.current_service_level = service_level
            self.target_service_level = service_level
            
            # Apply features for this service level
            await self._recover_features_for_service_level(service_level)
            
            # Record manual intervention
            manual_record = {
                "rule_name": "manual_intervention",
                "timestamp": datetime.now().isoformat(),
                "old_service_level": old_level.value,
                "new_service_level": service_level.value,
                "manual": True
            }
            
            self.degradation_history.append(manual_record)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error forcing service level: {e}")
            return False
    
    # Background monitoring tasks
    
    async def _monitoring_loop(self) -> None:
        """Background monitoring loop"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                # Evaluate degradation rules
                await self._evaluate_degradation_rules()
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
    
    async def _recovery_loop(self) -> None:
        """Background recovery monitoring loop"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Check if we can recover to a higher service level
                if self.current_service_level != ServiceLevel.FULL:
                    await self._check_recovery_opportunities()
                
            except Exception as e:
                self.logger.error(f"Error in recovery loop: {e}")
    
    async def _check_recovery_opportunities(self) -> None:
        """Check if system can recover to higher service level"""
        try:
            current_conditions = self._get_current_conditions()
            
            # Check if conditions allow for higher service level
            target_levels = [ServiceLevel.FULL, ServiceLevel.DEGRADED, ServiceLevel.MINIMAL]
            
            for target_level in target_levels:
                if target_level.value > self.current_service_level.value:
                    if self._can_support_service_level(target_level, current_conditions):
                        self.logger.info(f"Recovery opportunity detected: can upgrade to {target_level.value}")
                        # Let the recovery rules handle the actual upgrade
                        break
                        
        except Exception as e:
            self.logger.error(f"Error checking recovery opportunities: {e}")
    
    def _can_support_service_level(self, service_level: ServiceLevel, conditions: Dict[str, Any]) -> bool:
        """Check if current conditions can support a service level"""
        # Simple heuristics - in production, this would be more sophisticated
        if service_level == ServiceLevel.FULL:
            return (conditions.get("cpu_usage", 100) < 70 and 
                   conditions.get("memory_usage", 100) < 80 and
                   conditions.get("failed_agents", 10) == 0)
        elif service_level == ServiceLevel.DEGRADED:
            return (conditions.get("cpu_usage", 100) < 85 and 
                   conditions.get("memory_usage", 100) < 90 and
                   conditions.get("failed_agents", 10) <= 1)
        elif service_level == ServiceLevel.MINIMAL:
            return (conditions.get("failed_agents", 10) <= 2 and
                   not conditions.get("cost_management_agent_failed", True))
        
        return True
    
    async def shutdown(self) -> None:
        """Shutdown graceful degradation manager"""
        try:
            if self._monitoring_task:
                self._monitoring_task.cancel()
            if self._recovery_task:
                self._recovery_task.cancel()
            
            self.logger.info("Graceful degradation manager shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")


# Factory function
def create_graceful_degradation_manager(config: Optional[Dict[str, Any]] = None) -> GracefulDegradationManager:
    """Create graceful degradation manager with default configuration"""
    default_config = {
        "features": {},
        "degradation_rules": [],
        "recovery_rules": []
    }
    
    if config:
        default_config.update(config)
    
    return GracefulDegradationManager(default_config)