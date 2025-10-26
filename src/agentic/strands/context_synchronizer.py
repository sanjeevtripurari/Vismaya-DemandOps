"""
Context Synchronization Service for Strands Framework
Real-time context sharing and synchronization between agents
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum

from ..core.interfaces import IContextManager
from ..core.models import AgentMessage, SystemEvent


class SyncStrategy(Enum):
    """Context synchronization strategies"""
    IMMEDIATE = "immediate"  # Sync immediately on change
    BATCHED = "batched"      # Batch changes and sync periodically
    ON_DEMAND = "on_demand"  # Sync only when requested
    CONFLICT_AWARE = "conflict_aware"  # Sync with conflict detection


class ConflictResolution(Enum):
    """Conflict resolution strategies"""
    LAST_WRITER_WINS = "last_writer_wins"
    FIRST_WRITER_WINS = "first_writer_wins"
    MERGE_VALUES = "merge_values"
    MANUAL_RESOLUTION = "manual_resolution"
    PRIORITY_BASED = "priority_based"


@dataclass
class SyncOperation:
    """Represents a context synchronization operation"""
    operation_id: str
    agent_ids: List[str]
    context_keys: List[str]
    strategy: SyncStrategy
    conflict_resolution: ConflictResolution
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    status: str = "pending"  # pending, in_progress, completed, failed
    conflicts_detected: List[str] = field(default_factory=list)
    resolution_applied: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextChange:
    """Represents a context change event"""
    agent_id: str
    context_key: str
    old_value: Any
    new_value: Any
    timestamp: datetime = field(default_factory=datetime.now)
    change_type: str = "update"  # create, update, delete
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContextSynchronizer:
    """
    Real-time context synchronization service
    Handles cross-agent context sharing with conflict resolution
    """
    
    def __init__(self, context_manager: IContextManager, config: Dict[str, Any]):
        self.context_manager = context_manager
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Synchronization state
        self.active_sync_operations: Dict[str, SyncOperation] = {}
        self.pending_changes: Dict[str, List[ContextChange]] = defaultdict(list)
        self.sync_subscriptions: Dict[str, Set[str]] = defaultdict(set)  # agent_id -> context_keys
        
        # Configuration
        self.batch_interval = config.get("batch_sync_interval", 5.0)  # seconds
        self.max_batch_size = config.get("max_batch_size", 100)
        self.conflict_timeout = config.get("conflict_timeout", 300)  # seconds
        
        # Agent priorities for conflict resolution
        self.agent_priorities = config.get("agent_priorities", {
            "orchestrator": 100,
            "approval": 90,
            "cost_management": 80,
            "resource_management": 80,
            "forecasting": 70,
            "alert_management": 60,
            "user_interface": 50
        })
        
        # Synchronization locks
        self.sync_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        
        # Start background tasks
        self._start_background_tasks()
    
    def _start_background_tasks(self) -> None:
        """Start background synchronization tasks"""
        try:
            # Only start background tasks if there's a running event loop
            loop = asyncio.get_running_loop()
            asyncio.create_task(self._batch_sync_processor())
            asyncio.create_task(self._conflict_monitor())
            asyncio.create_task(self._cleanup_completed_operations())
        except RuntimeError:
            # No running event loop - likely in test mode
            # Background tasks will be started when needed
            pass
    
    async def subscribe_to_context(self, agent_id: str, context_keys: List[str]) -> bool:
        """Subscribe agent to context changes for specific keys"""
        try:
            self.sync_subscriptions[agent_id].update(context_keys)
            self.logger.info(f"Agent {agent_id} subscribed to context keys: {context_keys}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error subscribing agent to context: {e}")
            return False
    
    async def unsubscribe_from_context(self, agent_id: str, context_keys: List[str]) -> bool:
        """Unsubscribe agent from context changes"""
        try:
            self.sync_subscriptions[agent_id].difference_update(context_keys)
            self.logger.info(f"Agent {agent_id} unsubscribed from context keys: {context_keys}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error unsubscribing agent from context: {e}")
            return False
    
    async def notify_context_change(self, agent_id: str, context_key: str, old_value: Any, new_value: Any) -> None:
        """Notify synchronizer of context change"""
        try:
            change = ContextChange(
                agent_id=agent_id,
                context_key=context_key,
                old_value=old_value,
                new_value=new_value,
                change_type="update" if old_value is not None else "create"
            )
            
            # Add to pending changes
            self.pending_changes[context_key].append(change)
            
            # Find subscribers for this context key
            subscribers = []
            for sub_agent_id, subscribed_keys in self.sync_subscriptions.items():
                if context_key in subscribed_keys and sub_agent_id != agent_id:
                    subscribers.append(sub_agent_id)
            
            if subscribers:
                # Trigger immediate sync for critical changes
                if self._is_critical_change(context_key, new_value):
                    await self.sync_context_immediate(subscribers, [context_key])
                else:
                    # Add to batch sync queue
                    self.logger.debug(f"Context change queued for batch sync: {context_key} -> {subscribers}")
            
        except Exception as e:
            self.logger.error(f"Error notifying context change: {e}")
    
    async def sync_context_immediate(self, agent_ids: List[str], context_keys: List[str]) -> SyncOperation:
        """Perform immediate context synchronization"""
        try:
            operation = SyncOperation(
                operation_id=f"sync_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                agent_ids=agent_ids,
                context_keys=context_keys,
                strategy=SyncStrategy.IMMEDIATE,
                conflict_resolution=ConflictResolution.LAST_WRITER_WINS
            )
            
            self.active_sync_operations[operation.operation_id] = operation
            operation.status = "in_progress"
            
            # Perform synchronization
            await self._execute_sync_operation(operation)
            
            return operation
            
        except Exception as e:
            self.logger.error(f"Error in immediate context sync: {e}")
            operation.status = "failed"
            return operation
    
    async def sync_context_with_conflict_resolution(self, agent_ids: List[str], context_keys: List[str], 
                                                   resolution_strategy: ConflictResolution) -> SyncOperation:
        """Perform context synchronization with specific conflict resolution"""
        try:
            operation = SyncOperation(
                operation_id=f"sync_conflict_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                agent_ids=agent_ids,
                context_keys=context_keys,
                strategy=SyncStrategy.CONFLICT_AWARE,
                conflict_resolution=resolution_strategy
            )
            
            self.active_sync_operations[operation.operation_id] = operation
            operation.status = "in_progress"
            
            # Perform synchronization with conflict detection
            await self._execute_sync_operation_with_conflicts(operation)
            
            return operation
            
        except Exception as e:
            self.logger.error(f"Error in conflict-aware context sync: {e}")
            operation.status = "failed"
            return operation
    
    async def _execute_sync_operation(self, operation: SyncOperation) -> None:
        """Execute a synchronization operation with enhanced versioning and conflict resolution"""
        try:
            # Get sync lock for the context keys
            lock_key = "_".join(sorted(operation.context_keys))
            async with self.sync_locks[lock_key]:
                
                # Create checkpoint before synchronization
                checkpoint_id = await self._create_sync_checkpoint(operation)
                
                # Collect current context values from all agents with version information
                context_values = {}
                for agent_id in operation.agent_ids:
                    agent_context = await self.context_manager.get_agent_context(agent_id)
                    for key in operation.context_keys:
                        if key in agent_context:
                            if key not in context_values:
                                context_values[key] = []
                            
                            # Extract agent type for priority calculation
                            agent_type = agent_id.split('_')[0] if '_' in agent_id else agent_id
                            priority = self.agent_priorities.get(agent_type, 50)
                            
                            context_values[key].append({
                                "agent_id": agent_id,
                                "agent_type": agent_type,
                                "value": agent_context[key],
                                "timestamp": agent_context.get(f"{key}_timestamp", datetime.now().isoformat()),
                                "version": agent_context.get(f"{key}_version", 0),
                                "priority": priority,
                                "has_authority": self._agent_has_conflict_authority(agent_type)
                            })
                
                # Resolve conflicts and determine final values with enhanced strategy
                final_values = {}
                version_updates = {}
                
                for key, values in context_values.items():
                    if len(values) > 1:
                        # Multiple values - potential conflict
                        resolved_value, resolution_metadata = await self._resolve_conflict_enhanced(
                            key, values, operation.conflict_resolution
                        )
                        final_values[key] = resolved_value
                        operation.conflicts_detected.append(key)
                        
                        # Update version information
                        new_version = max(v.get("version", 0) for v in values) + 1
                        version_updates[f"{key}_version"] = new_version
                        version_updates[f"{key}_sync_timestamp"] = datetime.now().isoformat()
                        version_updates[f"{key}_resolution_method"] = resolution_metadata["method"]
                        version_updates[f"{key}_resolved_from"] = resolution_metadata["source"]
                        
                    elif len(values) == 1:
                        # Single value - no conflict
                        final_values[key] = values[0]["value"]
                        # Still update version for consistency
                        version_updates[f"{key}_version"] = values[0].get("version", 0)
                        version_updates[f"{key}_sync_timestamp"] = datetime.now().isoformat()
                
                # Apply final values and version updates to all agents
                for agent_id in operation.agent_ids:
                    updates = {}
                    updates.update(final_values)
                    updates.update(version_updates)
                    
                    if updates:
                        await self.context_manager.update_agent_context(agent_id, updates)
                
                operation.status = "completed"
                operation.completed_at = datetime.now()
                operation.resolution_applied = final_values
                operation.metadata = {
                    "checkpoint_id": checkpoint_id,
                    "version_updates": version_updates,
                    "sync_method": "enhanced_versioned"
                }
                
        except Exception as e:
            self.logger.error(f"Error executing sync operation: {e}")
            operation.status = "failed"
            
            # Attempt rollback if checkpoint was created
            if hasattr(operation, 'metadata') and operation.metadata.get("checkpoint_id"):
                await self._rollback_sync_checkpoint(operation.metadata["checkpoint_id"])
    
    async def _create_sync_checkpoint(self, operation: SyncOperation) -> str:
        """Create a checkpoint before synchronization for rollback purposes"""
        try:
            checkpoint_id = f"sync_checkpoint_{operation.operation_id}"
            checkpoint_data = {
                "operation_id": operation.operation_id,
                "agent_ids": operation.agent_ids,
                "context_keys": operation.context_keys,
                "created_at": datetime.now().isoformat(),
                "agent_contexts": {}
            }
            
            # Capture current state of all agents
            for agent_id in operation.agent_ids:
                agent_context = await self.context_manager.get_agent_context(agent_id)
                checkpoint_data["agent_contexts"][agent_id] = {
                    key: agent_context.get(key) for key in operation.context_keys 
                    if key in agent_context
                }
            
            # Store checkpoint (in a real implementation, this would go to persistent storage)
            self._sync_checkpoints = getattr(self, '_sync_checkpoints', {})
            self._sync_checkpoints[checkpoint_id] = checkpoint_data
            
            return checkpoint_id
            
        except Exception as e:
            self.logger.error(f"Error creating sync checkpoint: {e}")
            return ""
    
    async def _rollback_sync_checkpoint(self, checkpoint_id: str) -> bool:
        """Rollback to a sync checkpoint"""
        try:
            checkpoints = getattr(self, '_sync_checkpoints', {})
            if checkpoint_id not in checkpoints:
                return False
            
            checkpoint_data = checkpoints[checkpoint_id]
            
            # Restore agent contexts
            for agent_id, context_data in checkpoint_data["agent_contexts"].items():
                if context_data:
                    await self.context_manager.update_agent_context(agent_id, context_data)
            
            self.logger.info(f"Successfully rolled back sync checkpoint: {checkpoint_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error rolling back sync checkpoint: {e}")
            return False
    
    async def _resolve_conflict_enhanced(self, context_key: str, values: List[Dict[str, Any]], 
                                       strategy: ConflictResolution) -> tuple[Any, Dict[str, str]]:
        """Enhanced conflict resolution with metadata"""
        try:
            resolution_metadata = {"method": strategy.value, "source": "unknown"}
            
            if strategy == ConflictResolution.LAST_WRITER_WINS:
                # Use the value with the latest timestamp
                latest_value = max(values, key=lambda x: x["timestamp"])
                resolution_metadata["source"] = latest_value["agent_id"]
                resolution_metadata["method"] = "timestamp_based"
                return latest_value["value"], resolution_metadata
            
            elif strategy == ConflictResolution.FIRST_WRITER_WINS:
                # Use the value with the earliest timestamp
                earliest_value = min(values, key=lambda x: x["timestamp"])
                resolution_metadata["source"] = earliest_value["agent_id"]
                resolution_metadata["method"] = "first_writer"
                return earliest_value["value"], resolution_metadata
            
            elif strategy == ConflictResolution.PRIORITY_BASED:
                # Use value from highest priority agent
                highest_priority = max(values, key=lambda x: x["priority"])
                resolution_metadata["source"] = highest_priority["agent_id"]
                resolution_metadata["method"] = "priority_based"
                return highest_priority["value"], resolution_metadata
            
            elif strategy == ConflictResolution.MERGE_VALUES:
                # Attempt to merge values (for dict/list types)
                merged_value = await self._merge_values(context_key, values)
                resolution_metadata["source"] = "merged"
                resolution_metadata["method"] = "value_merge"
                return merged_value, resolution_metadata
            
            else:
                # Default to authority-based if available, otherwise last writer wins
                authority_values = [v for v in values if v.get("has_authority", False)]
                if authority_values:
                    authority_value = max(authority_values, key=lambda x: x["priority"])
                    resolution_metadata["source"] = authority_value["agent_id"]
                    resolution_metadata["method"] = "authority_based"
                    return authority_value["value"], resolution_metadata
                else:
                    latest_value = max(values, key=lambda x: x["timestamp"])
                    resolution_metadata["source"] = latest_value["agent_id"]
                    resolution_metadata["method"] = "fallback_timestamp"
                    return latest_value["value"], resolution_metadata
                
        except Exception as e:
            self.logger.error(f"Error in enhanced conflict resolution for key {context_key}: {e}")
            # Fallback to first available value
            if values:
                resolution_metadata["source"] = values[0]["agent_id"]
                resolution_metadata["method"] = "error_fallback"
                return values[0]["value"], resolution_metadata
            return None, resolution_metadata
    
    def _agent_has_conflict_authority(self, agent_type: str) -> bool:
        """Check if agent type has conflict resolution authority"""
        authority_agents = ["orchestrator", "approval", "alert_management"]
        return agent_type in authority_agents
    
    async def _execute_sync_operation_with_conflicts(self, operation: SyncOperation) -> None:
        """Execute synchronization operation with enhanced conflict detection"""
        try:
            # Enhanced conflict detection and resolution
            await self._execute_sync_operation(operation)
            
            # Additional conflict analysis
            if operation.conflicts_detected:
                await self._analyze_conflicts(operation)
            
        except Exception as e:
            self.logger.error(f"Error executing conflict-aware sync operation: {e}")
            operation.status = "failed"
    
    async def _resolve_conflict(self, context_key: str, values: List[Dict[str, Any]], 
                               strategy: ConflictResolution) -> Any:
        """Resolve context conflicts using specified strategy"""
        try:
            if strategy == ConflictResolution.LAST_WRITER_WINS:
                # Use the value with the latest timestamp
                latest_value = max(values, key=lambda x: x["timestamp"])
                return latest_value["value"]
            
            elif strategy == ConflictResolution.FIRST_WRITER_WINS:
                # Use the value with the earliest timestamp
                earliest_value = min(values, key=lambda x: x["timestamp"])
                return earliest_value["value"]
            
            elif strategy == ConflictResolution.PRIORITY_BASED:
                # Use value from highest priority agent
                highest_priority = max(values, key=lambda x: self._get_agent_priority(x["agent_id"]))
                return highest_priority["value"]
            
            elif strategy == ConflictResolution.MERGE_VALUES:
                # Attempt to merge values (for dict/list types)
                return await self._merge_values(context_key, values)
            
            else:
                # Default to last writer wins
                latest_value = max(values, key=lambda x: x["timestamp"])
                return latest_value["value"]
                
        except Exception as e:
            self.logger.error(f"Error resolving conflict for key {context_key}: {e}")
            # Fallback to first available value
            return values[0]["value"] if values else None
    
    async def _merge_values(self, context_key: str, values: List[Dict[str, Any]]) -> Any:
        """Attempt to merge conflicting values"""
        try:
            # Extract the actual values
            actual_values = [v["value"] for v in values]
            
            # If all values are dictionaries, merge them
            if all(isinstance(v, dict) for v in actual_values):
                merged = {}
                for value_dict in actual_values:
                    merged.update(value_dict)
                return merged
            
            # If all values are lists, concatenate them
            elif all(isinstance(v, list) for v in actual_values):
                merged = []
                for value_list in actual_values:
                    merged.extend(value_list)
                return list(set(merged))  # Remove duplicates
            
            # If all values are the same, return one
            elif len(set(str(v) for v in actual_values)) == 1:
                return actual_values[0]
            
            # Otherwise, use last writer wins
            else:
                latest_value = max(values, key=lambda x: x["timestamp"])
                return latest_value["value"]
                
        except Exception as e:
            self.logger.error(f"Error merging values for key {context_key}: {e}")
            return values[0]["value"] if values else None
    
    def _get_agent_priority(self, agent_id: str) -> int:
        """Get priority for agent (higher number = higher priority)"""
        # Extract agent type from agent_id
        agent_type = agent_id.split('_')[0] if '_' in agent_id else agent_id
        return self.agent_priorities.get(agent_type, 50)  # Default priority
    
    def _is_critical_change(self, context_key: str, new_value: Any) -> bool:
        """Determine if a context change requires immediate synchronization"""
        critical_keys = [
            "system_alert", "budget_threshold_exceeded", "critical_error",
            "emergency_shutdown", "security_breach", "approval_required"
        ]
        
        return context_key in critical_keys or (
            isinstance(new_value, dict) and 
            new_value.get("priority") in ["critical", "emergency"]
        )
    
    async def _analyze_conflicts(self, operation: SyncOperation) -> None:
        """Analyze conflicts and generate insights"""
        try:
            conflict_analysis = {
                "operation_id": operation.operation_id,
                "conflicts_count": len(operation.conflicts_detected),
                "conflicted_keys": operation.conflicts_detected,
                "resolution_strategy": operation.conflict_resolution.value,
                "agents_involved": operation.agent_ids,
                "timestamp": datetime.now().isoformat()
            }
            
            # Log conflict analysis
            self.logger.warning(f"Context conflicts detected and resolved: {conflict_analysis}")
            
            # Store conflict analysis for future reference
            # This could be stored in the memory store for analytics
            
        except Exception as e:
            self.logger.error(f"Error analyzing conflicts: {e}")
    
    async def _batch_sync_processor(self) -> None:
        """Background task to process batched synchronization"""
        while True:
            try:
                await asyncio.sleep(self.batch_interval)
                
                if self.pending_changes:
                    # Group changes by context key
                    changes_to_process = dict(self.pending_changes)
                    self.pending_changes.clear()
                    
                    for context_key, changes in changes_to_process.items():
                        if len(changes) > 0:
                            # Find all agents that need this context key
                            affected_agents = set()
                            for agent_id, subscribed_keys in self.sync_subscriptions.items():
                                if context_key in subscribed_keys:
                                    affected_agents.add(agent_id)
                            
                            if len(affected_agents) > 1:
                                # Perform batch sync
                                await self.sync_context_immediate(list(affected_agents), [context_key])
                
            except Exception as e:
                self.logger.error(f"Error in batch sync processor: {e}")
    
    async def _conflict_monitor(self) -> None:
        """Background task to monitor and resolve long-running conflicts"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                current_time = datetime.now()
                
                # Check for operations that have been in progress too long
                for operation_id, operation in list(self.active_sync_operations.items()):
                    if operation.status == "in_progress":
                        time_elapsed = (current_time - operation.created_at).total_seconds()
                        
                        if time_elapsed > self.conflict_timeout:
                            self.logger.warning(f"Sync operation {operation_id} timed out, marking as failed")
                            operation.status = "failed"
                
            except Exception as e:
                self.logger.error(f"Error in conflict monitor: {e}")
    
    async def _cleanup_completed_operations(self) -> None:
        """Background task to clean up completed operations"""
        while True:
            try:
                await asyncio.sleep(3600)  # Clean up every hour
                
                current_time = datetime.now()
                cutoff_time = current_time - timedelta(hours=24)  # Keep operations for 24 hours
                
                # Remove old completed operations
                operations_to_remove = []
                for operation_id, operation in self.active_sync_operations.items():
                    if (operation.status in ["completed", "failed"] and 
                        operation.completed_at and 
                        operation.completed_at < cutoff_time):
                        operations_to_remove.append(operation_id)
                
                for operation_id in operations_to_remove:
                    del self.active_sync_operations[operation_id]
                
                if operations_to_remove:
                    self.logger.info(f"Cleaned up {len(operations_to_remove)} old sync operations")
                
            except Exception as e:
                self.logger.error(f"Error in cleanup task: {e}")
    
    def get_sync_stats(self) -> Dict[str, Any]:
        """Get comprehensive synchronization statistics"""
        try:
            stats = {
                "active_operations": len(self.active_sync_operations),
                "pending_changes": sum(len(changes) for changes in self.pending_changes.values()),
                "subscriptions": {agent_id: list(keys) for agent_id, keys in self.sync_subscriptions.items()},
                "operations_by_status": defaultdict(int),
                "conflicts_detected": 0,
                "avg_sync_time": 0.0,
                "checkpoints_created": len(getattr(self, '_sync_checkpoints', {})),
                "conflict_resolution_methods": defaultdict(int),
                "agent_sync_activity": defaultdict(int)
            }
            
            # Analyze operations
            sync_times = []
            for operation in self.active_sync_operations.values():
                stats["operations_by_status"][operation.status] += 1
                stats["conflicts_detected"] += len(operation.conflicts_detected)
                
                # Track agent activity
                for agent_id in operation.agent_ids:
                    stats["agent_sync_activity"][agent_id] += 1
                
                # Track resolution methods
                if hasattr(operation, 'metadata') and operation.metadata:
                    method = operation.metadata.get("sync_method", "unknown")
                    stats["conflict_resolution_methods"][method] += 1
                
                if operation.completed_at:
                    sync_time = (operation.completed_at - operation.created_at).total_seconds()
                    sync_times.append(sync_time)
            
            if sync_times:
                stats["avg_sync_time"] = sum(sync_times) / len(sync_times)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting sync stats: {e}")
            return {"error": str(e)}
    
    async def apply_context_isolation_policy(self, agent_id: str, isolation_level: str) -> bool:
        """Apply context isolation policy to agent"""
        try:
            agent_type = agent_id.split('_')[0] if '_' in agent_id else agent_id
            
            isolation_policies = {
                "none": {
                    "real_time_sync": True,
                    "cross_agent_access": True,
                    "conflict_resolution_participation": True,
                    "context_encryption": False
                },
                "low": {
                    "real_time_sync": True,
                    "cross_agent_access": True,
                    "conflict_resolution_participation": True,
                    "context_encryption": False
                },
                "domain": {
                    "real_time_sync": True,
                    "cross_agent_access": "domain_only",
                    "conflict_resolution_participation": True,
                    "context_encryption": False
                },
                "high": {
                    "real_time_sync": False,
                    "cross_agent_access": False,
                    "conflict_resolution_participation": False,
                    "context_encryption": True
                }
            }
            
            policy = isolation_policies.get(isolation_level, isolation_policies["domain"])
            
            # Store isolation policy for agent
            if not hasattr(self, '_agent_isolation_policies'):
                self._agent_isolation_policies = {}
            
            self._agent_isolation_policies[agent_id] = {
                "level": isolation_level,
                "policy": policy,
                "applied_at": datetime.now().isoformat()
            }
            
            # Adjust sync subscriptions based on policy
            if not policy["real_time_sync"]:
                # Remove from real-time sync subscriptions
                if agent_id in self.sync_subscriptions:
                    self.sync_subscriptions[agent_id].clear()
            
            self.logger.info(f"Applied isolation policy '{isolation_level}' to agent {agent_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error applying isolation policy: {e}")
            return False
    
    async def validate_cross_agent_access(self, source_agent: str, target_agent: str, context_keys: List[str]) -> bool:
        """Validate if source agent can access target agent's context based on isolation policies"""
        try:
            # Get isolation policies for both agents
            source_policy = getattr(self, '_agent_isolation_policies', {}).get(source_agent, {})
            target_policy = getattr(self, '_agent_isolation_policies', {}).get(target_agent, {})
            
            # Check target agent's isolation level
            target_level = target_policy.get("level", "domain")
            if target_level == "high":
                # High isolation - no cross-agent access
                return False
            
            # Check source agent's permissions
            source_level = source_policy.get("level", "domain")
            if source_level == "high":
                # High isolation agents can't access others
                return False
            
            # Domain-level isolation - check if agents are in same domain
            if target_level == "domain":
                source_type = source_agent.split('_')[0] if '_' in source_agent else source_agent
                target_type = target_agent.split('_')[0] if '_' in target_agent else target_agent
                
                # Define domain relationships
                domain_relationships = {
                    "cost_management": ["forecasting", "resource_management"],
                    "resource_management": ["cost_management"],
                    "forecasting": ["cost_management"],
                    "orchestrator": ["*"],  # Orchestrator can access all
                    "approval": ["*"],      # Approval can access all
                    "alert_management": ["*"]  # Alert management can access all
                }
                
                allowed_types = domain_relationships.get(source_type, [])
                if "*" not in allowed_types and target_type not in allowed_types:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating cross-agent access: {e}")
            return False