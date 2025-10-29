"""
Strands Framework implementation
Context and memory management for multi-agent systems
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict

from ..core.interfaces import IStrandsFramework, IContextManager, IMemoryStore
from ..core.models import (
    AgentMessage, DecisionProposal, ConversationContext, DecisionContext,
    ContextSynchronizationError, MemoryStoreError
)
from .context_synchronizer import ContextSynchronizer, SyncStrategy, ConflictResolution


class StrandsFramework(IStrandsFramework):
    """
    Strands Framework for context and memory management
    Provides persistent state and cross-agent communication capabilities
    """
    
    def __init__(self, memory_store: IMemoryStore, config: Dict[str, Any]):
        self.memory_store = memory_store
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize context manager
        self.context_manager = ContextManager(memory_store, config)
        self.context_manager.set_framework_reference(self)
        
        # Initialize context synchronizer
        self.context_synchronizer = ContextSynchronizer(self.context_manager, config)
        
        # Framework state
        self.initialized = False
        self.conversation_threads: Dict[str, ConversationContext] = {}
        self.decision_contexts: Dict[str, DecisionContext] = {}
        
        # Performance tracking
        self.context_access_count = 0
        self.memory_operations_count = 0
        self.sync_operations_count = 0
        
        # Context sharing policies
        self.context_sharing_policies = self._initialize_sharing_policies()
        
        # Real-time synchronization
        self.sync_lock = asyncio.Lock()
        self.pending_sync_operations = set()
        
        # Context versioning
        self.context_versions: Dict[str, int] = defaultdict(int)
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize Strands framework"""
        try:
            # Update configuration
            self.config.update(config)
            
            # Initialize context manager
            await self.context_manager.initialize()
            
            # Load existing conversation threads
            await self._load_conversation_threads()
            
            # Load existing decision contexts
            await self._load_decision_contexts()
            
            self.initialized = True
            self.logger.info("Strands Framework initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing Strands Framework: {e}")
            return False
    
    async def get_shared_context(self, context_keys: List[str]) -> Dict[str, Any]:
        """Retrieve shared context across agents"""
        try:
            self.context_access_count += 1
            
            shared_context = {}
            
            # Get global context
            global_context = await self.context_manager.get_global_context()
            
            for key in context_keys:
                if key in global_context:
                    shared_context[key] = global_context[key]
                else:
                    # Try to get from agent-specific contexts
                    agent_contexts = await self._get_all_agent_contexts()
                    for agent_id, context in agent_contexts.items():
                        if key in context:
                            shared_context[key] = context[key]
                            break
            
            return shared_context
            
        except Exception as e:
            self.logger.error(f"Error getting shared context: {e}")
            raise ContextSynchronizationError(f"Failed to get shared context: {e}")
    
    async def update_context(self, agent_id: str, context_updates: Dict[str, Any]) -> bool:
        """Update agent-specific context"""
        try:
            self.context_access_count += 1
            
            # Update agent context
            success = await self.context_manager.update_agent_context(agent_id, context_updates)
            
            if success:
                # Check if any updates should be propagated to global context
                await self._propagate_context_updates(agent_id, context_updates)
                
                # Notify other agents of context changes if needed
                await self._notify_context_changes(agent_id, context_updates)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error updating context for agent {agent_id}: {e}")
            return False
    
    async def create_conversation_thread(self, participants: List[str]) -> str:
        """Create new conversation thread between agents"""
        try:
            # Create conversation context
            conversation = ConversationContext(
                participants=participants,
                topic=f"Multi-agent conversation: {', '.join(participants)}"
            )
            
            # Store conversation thread
            self.conversation_threads[conversation.thread_id] = conversation
            
            # Persist to memory store
            await self.memory_store.store_conversation(
                conversation.thread_id,
                AgentMessage(
                    sender="strands_framework",
                    recipient="system",
                    message_type="notification",
                    content={
                        "event": "conversation_created",
                        "participants": participants,
                        "thread_id": conversation.thread_id
                    }
                )
            )
            
            self.logger.info(f"Created conversation thread {conversation.thread_id} with participants: {participants}")
            return conversation.thread_id
            
        except Exception as e:
            self.logger.error(f"Error creating conversation thread: {e}")
            raise MemoryStoreError(f"Failed to create conversation thread: {e}")
    
    async def get_conversation_history(self, thread_id: str, limit: int = 50) -> List[AgentMessage]:
        """Get conversation history for context"""
        try:
            self.memory_operations_count += 1
            
            # Get conversation history from memory store
            history = await self.memory_store.retrieve_conversation_history(thread_id, limit)
            
            # Update conversation activity
            if thread_id in self.conversation_threads:
                self.conversation_threads[thread_id].update_activity()
            
            return history
            
        except Exception as e:
            self.logger.error(f"Error getting conversation history: {e}")
            return []
    
    async def store_conversation_message(self, thread_id: str, message: AgentMessage) -> bool:
        """Store conversation message with full context"""
        try:
            self.memory_operations_count += 1
            
            # Add context information to message
            if thread_id in self.conversation_threads:
                conversation = self.conversation_threads[thread_id]
                message.metadata.update({
                    "thread_id": thread_id,
                    "participants": conversation.participants,
                    "conversation_topic": conversation.topic
                })
                
                # Update conversation activity
                conversation.update_activity()
            
            # Store message in memory store
            success = await self.memory_store.store_conversation(thread_id, message)
            
            if success:
                # Update context based on message content
                await self._update_context_from_message(message)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error storing conversation message: {e}")
            return False
    
    async def get_decision_context(self, decision_id: str) -> DecisionContext:
        """Get context for specific decision proposal"""
        try:
            self.context_access_count += 1
            
            if decision_id in self.decision_contexts:
                return self.decision_contexts[decision_id]
            
            # Create new decision context
            decision_context = DecisionContext(decision_id=decision_id)
            
            # Load related context information
            await self._load_decision_context_data(decision_context)
            
            # Store decision context
            self.decision_contexts[decision_id] = decision_context
            
            return decision_context
            
        except Exception as e:
            self.logger.error(f"Error getting decision context: {e}")
            return DecisionContext(decision_id=decision_id)
    
    async def store_decision_history(self, decision: DecisionProposal) -> bool:
        """Store decision proposal and approval history"""
        try:
            self.memory_operations_count += 1
            
            # Store decision in memory store
            success = await self.memory_store.store_decision_proposal(decision)
            
            if success:
                # Update decision context
                decision_context = await self.get_decision_context(decision.proposal_id)
                decision_context.business_context.update({
                    "cost_impact": decision.estimated_cost_impact,
                    "risk_level": decision.risk_level.value,
                    "created_by": decision.created_by
                })
                
                # Store context updates
                await self._persist_decision_context(decision_context)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error storing decision history: {e}")
            return False
    
    async def query_similar_decisions(self, current_decision: DecisionProposal) -> List[DecisionProposal]:
        """Find similar past decisions for context"""
        try:
            self.memory_operations_count += 1
            
            # Define similarity criteria
            criteria = {
                "cost_range": {
                    "min": current_decision.estimated_cost_impact * 0.5,
                    "max": current_decision.estimated_cost_impact * 2.0
                },
                "risk_level": current_decision.risk_level.value,
                "created_by": current_decision.created_by
            }
            
            # Query memory store for similar decisions
            similar_decisions = await self.memory_store.query_decisions_by_criteria(criteria)
            
            # Sort by similarity score
            scored_decisions = []
            for decision in similar_decisions:
                similarity_score = self._calculate_decision_similarity(current_decision, decision)
                scored_decisions.append((similarity_score, decision))
            
            # Return top similar decisions
            scored_decisions.sort(key=lambda x: x[0], reverse=True)
            return [decision for _, decision in scored_decisions[:5]]
            
        except Exception as e:
            self.logger.error(f"Error querying similar decisions: {e}")
            return []
    
    async def _load_conversation_threads(self) -> None:
        """Load existing conversation threads from memory store"""
        try:
            # Get recent system events for conversation creation
            events = await self.memory_store.get_system_events("conversation_created", limit=100)
            
            for event in events:
                if event.event_type == "conversation_created":
                    thread_id = event.data.get("thread_id")
                    participants = event.data.get("participants", [])
                    
                    if thread_id and participants:
                        conversation = ConversationContext(
                            thread_id=thread_id,
                            participants=participants,
                            created_at=event.timestamp
                        )
                        self.conversation_threads[thread_id] = conversation
            
        except Exception as e:
            self.logger.error(f"Error loading conversation threads: {e}")
    
    async def _load_decision_contexts(self) -> None:
        """Load existing decision contexts from memory store"""
        try:
            # Get recent decisions
            recent_decisions = await self.memory_store.query_decisions_by_criteria({
                "created_after": (datetime.now() - timedelta(days=30)).isoformat()
            })
            
            for decision in recent_decisions:
                decision_context = DecisionContext(decision_id=decision.proposal_id)
                await self._load_decision_context_data(decision_context)
                self.decision_contexts[decision.proposal_id] = decision_context
            
        except Exception as e:
            self.logger.error(f"Error loading decision contexts: {e}")
    
    async def _get_all_agent_contexts(self) -> Dict[str, Dict[str, Any]]:
        """Get contexts for all agents"""
        try:
            # Get all agent contexts from the context manager
            all_contexts = {}
            
            # Get agent contexts from the context manager's internal storage
            if hasattr(self.context_manager, 'agent_contexts'):
                for agent_id, context in self.context_manager.agent_contexts.items():
                    all_contexts[agent_id] = context.copy()
            
            # Also check for any additional agent contexts from recent system events
            try:
                events = await self.memory_store.get_system_events("agent_context_updated", limit=50)
                for event in events:
                    agent_id = event.data.get("agent_id")
                    context = event.data.get("context", {})
                    
                    if agent_id and context:
                        # Merge with existing context or create new
                        if agent_id in all_contexts:
                            all_contexts[agent_id].update(context)
                        else:
                            all_contexts[agent_id] = context
            except Exception as e:
                self.logger.warning(f"Could not load agent contexts from events: {e}")
            
            return all_contexts
            
        except Exception as e:
            self.logger.error(f"Error getting all agent contexts: {e}")
            return {}
    
    async def _propagate_context_updates(self, agent_id: str, context_updates: Dict[str, Any]) -> None:
        """Propagate context updates to global context if needed"""
        try:
            # Define keys that should be propagated to global context
            global_keys = ["system_status", "budget_alerts", "critical_events"]
            
            global_updates = {}
            for key, value in context_updates.items():
                if key in global_keys:
                    global_updates[f"{agent_id}_{key}"] = value
            
            if global_updates:
                await self.context_manager.update_global_context(global_updates)
            
        except Exception as e:
            self.logger.error(f"Error propagating context updates: {e}")
    
    async def _notify_context_changes(self, agent_id: str, context_updates: Dict[str, Any]) -> None:
        """Notify other agents of context changes if needed"""
        try:
            # Define keys that should trigger notifications
            notification_keys = ["budget_threshold_exceeded", "system_alert", "critical_decision"]
            
            should_notify = any(key in context_updates for key in notification_keys)
            
            if should_notify:
                # Create system event for context change
                from ..core.models import SystemEvent
                
                event = SystemEvent(
                    event_type="context_updated",
                    source=agent_id,
                    data={
                        "updated_keys": list(context_updates.keys()),
                        "requires_attention": True
                    },
                    severity="info"
                )
                
                # Store event (would typically broadcast to other agents)
                await self.memory_store.store_system_event(event)
            
        except Exception as e:
            self.logger.error(f"Error notifying context changes: {e}")
    
    async def _update_context_from_message(self, message: AgentMessage) -> None:
        """Update context based on message content"""
        try:
            # Extract context updates from message
            context_updates = {}
            
            # Check for specific message types that should update context
            if message.message_type.value == "event":
                event_type = message.content.get("event_type")
                if event_type in ["budget_alert", "cost_anomaly", "decision_approved"]:
                    context_updates[f"last_{event_type}"] = {
                        "timestamp": message.timestamp.isoformat(),
                        "data": message.content
                    }
            
            # Update sender's context
            if context_updates:
                await self.context_manager.update_agent_context(message.sender, context_updates)
            
        except Exception as e:
            self.logger.error(f"Error updating context from message: {e}")
    
    async def _load_decision_context_data(self, decision_context: DecisionContext) -> None:
        """Load context data for decision"""
        try:
            # Load related decisions
            related_decisions = await self.memory_store.query_decisions_by_criteria({
                "created_by": decision_context.decision_id,  # This would be more sophisticated
                "limit": 5
            })
            
            decision_context.related_decisions = [d.proposal_id for d in related_decisions]
            
            # Load historical context
            decision_context.historical_context = {
                "similar_decisions_count": len(related_decisions),
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error loading decision context data: {e}")
    
    async def _persist_decision_context(self, decision_context: DecisionContext) -> None:
        """Persist decision context to memory store"""
        try:
            # Create a system event to track decision context
            from ..core.models import SystemEvent
            
            event = SystemEvent(
                event_type="decision_context_updated",
                source="strands_framework",
                data={
                    "decision_id": decision_context.decision_id,
                    "context_data": {
                        "related_decisions": decision_context.related_decisions,
                        "business_context": decision_context.business_context
                    }
                }
            )
            
            await self.memory_store.store_system_event(event)
            
        except Exception as e:
            self.logger.error(f"Error persisting decision context: {e}")
    
    def _calculate_decision_similarity(self, decision1: DecisionProposal, decision2: DecisionProposal) -> float:
        """Calculate similarity score between two decisions"""
        similarity_score = 0.0
        
        # Cost similarity (40% weight)
        cost_diff = abs(decision1.estimated_cost_impact - decision2.estimated_cost_impact)
        max_cost = max(decision1.estimated_cost_impact, decision2.estimated_cost_impact)
        if max_cost > 0:
            cost_similarity = 1 - (cost_diff / max_cost)
            similarity_score += cost_similarity * 0.4
        
        # Risk level similarity (30% weight)
        if decision1.risk_level == decision2.risk_level:
            similarity_score += 0.3
        
        # Creator similarity (20% weight)
        if decision1.created_by == decision2.created_by:
            similarity_score += 0.2
        
        # Title/description similarity (10% weight)
        title_similarity = self._calculate_text_similarity(decision1.title, decision2.title)
        similarity_score += title_similarity * 0.1
        
        return similarity_score
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity (simplified implementation)"""
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def _initialize_sharing_policies(self) -> Dict[str, Dict[str, Any]]:
        """Initialize context sharing policies for different agent types with enhanced granular control"""
        return {
            "orchestrator": {
                "can_access": ["global", "all_agents"],
                "can_modify": ["global", "orchestrator"],
                "isolation_level": "none",
                "sync_priority": 100,
                "allowed_context_keys": ["*"],  # All keys
                "restricted_context_keys": [],
                "real_time_sync": True,
                "conflict_resolution_authority": True,
                "cross_domain_access": True
            },
            "cost_management": {
                "can_access": ["global", "cost_management", "forecasting", "resource_management"],
                "can_modify": ["cost_management"],
                "isolation_level": "domain",
                "sync_priority": 80,
                "allowed_context_keys": [
                    "budget_*", "cost_*", "spending_*", "threshold_*", 
                    "forecast_*", "resource_cost_*", "optimization_*"
                ],
                "restricted_context_keys": ["user_credentials", "system_secrets"],
                "real_time_sync": True,
                "conflict_resolution_authority": False,
                "cross_domain_access": True
            },
            "resource_management": {
                "can_access": ["global", "resource_management", "cost_management"],
                "can_modify": ["resource_management"],
                "isolation_level": "domain",
                "sync_priority": 80,
                "allowed_context_keys": [
                    "resource_*", "instance_*", "utilization_*", "capacity_*",
                    "cost_*", "optimization_*", "lifecycle_*"
                ],
                "restricted_context_keys": ["user_credentials", "system_secrets"],
                "real_time_sync": True,
                "conflict_resolution_authority": False,
                "cross_domain_access": True
            },
            "forecasting": {
                "can_access": ["global", "forecasting", "cost_management"],
                "can_modify": ["forecasting"],
                "isolation_level": "domain",
                "sync_priority": 70,
                "allowed_context_keys": [
                    "forecast_*", "prediction_*", "trend_*", "model_*",
                    "cost_*", "budget_*", "historical_*"
                ],
                "restricted_context_keys": ["user_credentials", "system_secrets"],
                "real_time_sync": False,  # Batch sync for performance
                "conflict_resolution_authority": False,
                "cross_domain_access": True
            },
            "alert_management": {
                "can_access": ["global", "alert_management", "all_agents"],
                "can_modify": ["alert_management"],
                "isolation_level": "low",
                "sync_priority": 90,
                "allowed_context_keys": [
                    "alert_*", "threshold_*", "notification_*", "escalation_*",
                    "system_status", "critical_*", "emergency_*"
                ],
                "restricted_context_keys": ["user_credentials"],
                "real_time_sync": True,
                "conflict_resolution_authority": True,  # For critical alerts
                "cross_domain_access": True
            },
            "user_interface": {
                "can_access": ["global", "user_interface"],
                "can_modify": ["user_interface"],
                "isolation_level": "high",
                "sync_priority": 50,
                "allowed_context_keys": [
                    "ui_*", "user_preferences", "session_*", "display_*",
                    "dashboard_*", "view_*"
                ],
                "restricted_context_keys": [
                    "system_secrets", "agent_internal_*", "security_*"
                ],
                "real_time_sync": False,
                "conflict_resolution_authority": False,
                "cross_domain_access": False
            },
            "approval": {
                "can_access": ["global", "approval", "all_agents"],
                "can_modify": ["approval"],
                "isolation_level": "low",
                "sync_priority": 95,
                "allowed_context_keys": [
                    "approval_*", "decision_*", "proposal_*", "workflow_*",
                    "stakeholder_*", "notification_*"
                ],
                "restricted_context_keys": ["user_credentials"],
                "real_time_sync": True,
                "conflict_resolution_authority": True,
                "cross_domain_access": True
            }
        }
    
    async def synchronize_context_real_time(self, agent_ids: List[str], context_keys: List[str]) -> bool:
        """Real-time context synchronization between agents with enhanced conflict resolution"""
        async with self.sync_lock:
            try:
                self.sync_operations_count += 1
                
                # Check if synchronization is already in progress
                sync_key = f"{'-'.join(sorted(agent_ids))}:{'-'.join(sorted(context_keys))}"
                if sync_key in self.pending_sync_operations:
                    return True
                
                self.pending_sync_operations.add(sync_key)
                
                try:
                    # Use the context synchronizer for enhanced real-time sync
                    operation = await self.context_synchronizer.sync_context_immediate(agent_ids, context_keys)
                    
                    # Log synchronization results
                    if operation.conflicts_detected:
                        self.logger.info(f"Real-time sync completed with {len(operation.conflicts_detected)} conflicts resolved")
                    
                    return operation.status == "completed"
                    
                finally:
                    self.pending_sync_operations.discard(sync_key)
                    
            except Exception as e:
                self.logger.error(f"Error in real-time context synchronization: {e}")
                return False
    
    async def resolve_context_conflicts(self, agent_id: str, conflicted_keys: List[str]) -> Dict[str, Any]:
        """Resolve context conflicts using enhanced conflict resolution strategies"""
        try:
            resolved_context = {}
            
            for key in conflicted_keys:
                # Get all versions of the context key from all relevant agents
                versions = []
                
                # Global context version
                global_context = await self.context_manager.get_global_context()
                if key in global_context:
                    versions.append({
                        "source": "global",
                        "value": global_context[key],
                        "timestamp": global_context.get(f"{key}_timestamp", datetime.now().isoformat()),
                        "version": global_context.get(f"{key}_version", 0),
                        "priority": 100  # Global context has highest priority
                    })
                
                # Get all agent contexts that might have this key
                all_agent_contexts = await self._get_all_agent_contexts()
                for source_agent_id, context in all_agent_contexts.items():
                    if key in context:
                        agent_type = source_agent_id.split('_')[0] if '_' in source_agent_id else source_agent_id
                        policy = self.context_sharing_policies.get(agent_type, {})
                        
                        versions.append({
                            "source": source_agent_id,
                            "value": context[key],
                            "timestamp": context.get(f"{key}_timestamp", datetime.now().isoformat()),
                            "version": context.get(f"{key}_version", 0),
                            "priority": policy.get("sync_priority", 50),
                            "has_authority": policy.get("conflict_resolution_authority", False)
                        })
                
                # Apply enhanced conflict resolution strategy
                if versions:
                    resolved_value = await self._resolve_conflict_with_strategy(key, versions, agent_id)
                    resolved_context[key] = resolved_value
                    
                    # Update context version
                    self.context_versions[key] += 1
                    resolved_context[f"{key}_version"] = self.context_versions[key]
                    resolved_context[f"{key}_resolved_at"] = datetime.now().isoformat()
            
            return resolved_context
            
        except Exception as e:
            self.logger.error(f"Error resolving context conflicts: {e}")
            return {}
    
    async def _resolve_conflict_with_strategy(self, key: str, versions: List[Dict[str, Any]], requesting_agent: str) -> Any:
        """Resolve conflict using multiple strategies based on context and agent policies"""
        try:
            if len(versions) <= 1:
                return versions[0]["value"] if versions else None
            
            # Strategy 1: Authority-based resolution
            authority_versions = [v for v in versions if v.get("has_authority", False)]
            if authority_versions:
                # Use highest priority authority
                authority_version = max(authority_versions, key=lambda x: x["priority"])
                self.logger.info(f"Conflict resolved for '{key}' using authority: {authority_version['source']}")
                return authority_version["value"]
            
            # Strategy 2: Priority-based resolution
            if self._is_critical_context_key(key):
                highest_priority = max(versions, key=lambda x: x["priority"])
                self.logger.info(f"Conflict resolved for critical key '{key}' using priority: {highest_priority['source']}")
                return highest_priority["value"]
            
            # Strategy 3: Version-based resolution (most recent version)
            latest_version = max(versions, key=lambda x: x.get("version", 0))
            if latest_version["version"] > 0:
                self.logger.info(f"Conflict resolved for '{key}' using latest version: {latest_version['source']}")
                return latest_version["value"]
            
            # Strategy 4: Timestamp-based resolution (Last Writer Wins)
            latest_timestamp = max(versions, key=lambda x: x["timestamp"])
            self.logger.info(f"Conflict resolved for '{key}' using timestamp: {latest_timestamp['source']}")
            return latest_timestamp["value"]
            
        except Exception as e:
            self.logger.error(f"Error in conflict resolution strategy: {e}")
            # Fallback to first available value
            return versions[0]["value"] if versions else None
    
    def _is_critical_context_key(self, key: str) -> bool:
        """Determine if a context key is critical and requires priority-based resolution"""
        critical_patterns = [
            "system_alert*", "emergency_*", "critical_*", "security_*",
            "budget_threshold_exceeded", "cost_anomaly_*", "approval_required*"
        ]
        return self._key_matches_patterns(key, critical_patterns)
    
    async def create_context_version_checkpoint(self, agent_ids: List[str], context_keys: List[str]) -> str:
        """Create a versioned checkpoint of context state for rollback purposes"""
        try:
            checkpoint_id = f"checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            checkpoint_data = {
                "checkpoint_id": checkpoint_id,
                "created_at": datetime.now().isoformat(),
                "agent_ids": agent_ids,
                "context_keys": context_keys,
                "context_versions": {},
                "context_data": {}
            }
            
            # Capture current context state and versions
            for agent_id in agent_ids:
                agent_context = await self.context_manager.get_agent_context(agent_id)
                checkpoint_data["context_data"][agent_id] = {}
                checkpoint_data["context_versions"][agent_id] = {}
                
                for key in context_keys:
                    if key in agent_context:
                        checkpoint_data["context_data"][agent_id][key] = agent_context[key]
                        checkpoint_data["context_versions"][agent_id][key] = agent_context.get(f"{key}_version", 0)
            
            # Store checkpoint in memory
            self.context_snapshots[checkpoint_id] = checkpoint_data
            
            # Persist checkpoint to memory store
            from ..core.models import SystemEvent
            event = SystemEvent(
                event_type="context_checkpoint_created",
                source="strands_framework",
                data=checkpoint_data
            )
            await self.memory_store.store_system_event(event)
            
            self.logger.info(f"Created context version checkpoint: {checkpoint_id}")
            return checkpoint_id
            
        except Exception as e:
            self.logger.error(f"Error creating context version checkpoint: {e}")
            return ""
    
    async def rollback_to_context_checkpoint(self, checkpoint_id: str) -> bool:
        """Rollback context to a previous versioned checkpoint"""
        try:
            if checkpoint_id not in self.context_snapshots:
                # Try to load from memory store
                events = await self.memory_store.get_system_events("context_checkpoint_created", limit=100)
                for event in events:
                    if event.data.get("checkpoint_id") == checkpoint_id:
                        self.context_snapshots[checkpoint_id] = event.data
                        break
                
                if checkpoint_id not in self.context_snapshots:
                    self.logger.error(f"Checkpoint {checkpoint_id} not found")
                    return False
            
            checkpoint_data = self.context_snapshots[checkpoint_id]
            
            # Restore context data and versions
            for agent_id, context_data in checkpoint_data["context_data"].items():
                # Update agent context
                await self.context_manager.update_agent_context(agent_id, context_data)
                
                # Restore context versions
                if agent_id in checkpoint_data["context_versions"]:
                    for key, version in checkpoint_data["context_versions"][agent_id].items():
                        self.context_versions[key] = version
                        await self.context_manager.update_agent_context(
                            agent_id, 
                            {f"{key}_version": version, f"{key}_rollback_timestamp": datetime.now().isoformat()}
                        )
            
            self.logger.info(f"Successfully rolled back to checkpoint: {checkpoint_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error rolling back to checkpoint: {e}")
            return False
    
    async def _can_agent_access_context(self, agent_id: str, context_keys: List[str]) -> bool:
        """Check if agent can access specified context keys based on enhanced sharing policies"""
        try:
            # Extract agent type from agent_id (assuming format: type_instance)
            agent_type = agent_id.split('_')[0] if '_' in agent_id else agent_id
            
            policy = self.context_sharing_policies.get(agent_type, {})
            can_access = policy.get("can_access", [])
            allowed_keys = policy.get("allowed_context_keys", [])
            restricted_keys = policy.get("restricted_context_keys", [])
            cross_domain_access = policy.get("cross_domain_access", False)
            
            # Check each context key individually
            for key in context_keys:
                # First check if key is explicitly restricted
                if self._key_matches_patterns(key, restricted_keys):
                    self.logger.warning(f"Agent {agent_id} denied access to restricted key: {key}")
                    return False
                
                # Check if key is explicitly allowed
                if self._key_matches_patterns(key, allowed_keys):
                    continue
                
                # Check general access permissions
                access_granted = False
                
                # Check if key is globally accessible
                if "global" in can_access:
                    access_granted = True
                
                # Check if agent can access all agents' context
                elif "all_agents" in can_access:
                    access_granted = True
                
                # Check if agent can access its own type's context
                elif agent_type in can_access:
                    access_granted = True
                
                # Check cross-domain access for domain-specific keys
                elif cross_domain_access and self._is_cross_domain_key(key, agent_type):
                    access_granted = True
                
                if not access_granted:
                    self.logger.warning(f"Agent {agent_id} denied access to key: {key}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking context access permissions: {e}")
            return False
    
    def _key_matches_patterns(self, key: str, patterns: List[str]) -> bool:
        """Check if a context key matches any of the given patterns"""
        import fnmatch
        
        for pattern in patterns:
            if pattern == "*":  # Wildcard for all keys
                return True
            if fnmatch.fnmatch(key, pattern):
                return True
        return False
    
    def _is_cross_domain_key(self, key: str, agent_type: str) -> bool:
        """Check if a key is relevant for cross-domain access"""
        cross_domain_keys = {
            "cost_management": ["resource_*", "forecast_*"],
            "resource_management": ["cost_*", "budget_*"],
            "forecasting": ["cost_*", "resource_*"],
            "alert_management": ["*"],  # Alerts can access most contexts
            "approval": ["*"]  # Approval needs broad access
        }
        
        allowed_patterns = cross_domain_keys.get(agent_type, [])
        return self._key_matches_patterns(key, allowed_patterns)
    
    async def subscribe_agent_to_context(self, agent_id: str, context_keys: List[str]) -> bool:
        """Subscribe agent to context changes for real-time synchronization"""
        try:
            return await self.context_synchronizer.subscribe_to_context(agent_id, context_keys)
        except Exception as e:
            self.logger.error(f"Error subscribing agent to context: {e}")
            return False
    
    async def unsubscribe_agent_from_context(self, agent_id: str, context_keys: List[str]) -> bool:
        """Unsubscribe agent from context changes"""
        try:
            return await self.context_synchronizer.unsubscribe_from_context(agent_id, context_keys)
        except Exception as e:
            self.logger.error(f"Error unsubscribing agent from context: {e}")
            return False
    
    async def sync_context_with_strategy(self, agent_ids: List[str], context_keys: List[str], 
                                        strategy: str = "immediate", 
                                        conflict_resolution: str = "last_writer_wins") -> Dict[str, Any]:
        """Synchronize context between agents with specific strategy"""
        try:
            sync_strategy = SyncStrategy(strategy)
            resolution_strategy = ConflictResolution(conflict_resolution)
            
            if sync_strategy == SyncStrategy.IMMEDIATE:
                operation = await self.context_synchronizer.sync_context_immediate(agent_ids, context_keys)
            else:
                operation = await self.context_synchronizer.sync_context_with_conflict_resolution(
                    agent_ids, context_keys, resolution_strategy
                )
            
            return {
                "operation_id": operation.operation_id,
                "status": operation.status,
                "conflicts_detected": operation.conflicts_detected,
                "resolution_applied": operation.resolution_applied
            }
            
        except Exception as e:
            self.logger.error(f"Error synchronizing context with strategy: {e}")
            return {"error": str(e)}
    
    async def get_context_conflicts(self, agent_ids: List[str], context_keys: List[str]) -> Dict[str, Any]:
        """Detect context conflicts between agents without resolving them"""
        try:
            conflicts = {}
            
            for key in context_keys:
                values = []
                for agent_id in agent_ids:
                    agent_context = await self.context_manager.get_agent_context(agent_id)
                    if key in agent_context:
                        values.append({
                            "agent_id": agent_id,
                            "value": agent_context[key],
                            "timestamp": agent_context.get(f"{key}_timestamp", datetime.now().isoformat())
                        })
                
                if len(values) > 1:
                    # Check if values are different
                    unique_values = set(str(v["value"]) for v in values)
                    if len(unique_values) > 1:
                        conflicts[key] = {
                            "conflict_detected": True,
                            "values": values,
                            "unique_values_count": len(unique_values)
                        }
                    else:
                        conflicts[key] = {
                            "conflict_detected": False,
                            "values": values,
                            "note": "Same values across agents"
                        }
            
            return conflicts
            
        except Exception as e:
            self.logger.error(f"Error detecting context conflicts: {e}")
            return {"error": str(e)}
    
    def get_framework_stats(self) -> Dict[str, Any]:
        """Get framework statistics"""
        base_stats = {
            "initialized": self.initialized,
            "active_conversations": len(self.conversation_threads),
            "active_decision_contexts": len(self.decision_contexts),
            "context_access_count": self.context_access_count,
            "memory_operations_count": self.memory_operations_count,
            "sync_operations_count": self.sync_operations_count,
            "pending_sync_operations": len(self.pending_sync_operations),
            "context_versions": dict(self.context_versions),
            "sharing_policies": self.context_sharing_policies
        }
        
        # Add synchronizer stats
        try:
            sync_stats = self.context_synchronizer.get_sync_stats()
            base_stats["synchronization"] = sync_stats
        except Exception as e:
            base_stats["synchronization"] = {"error": str(e)}
        
        return base_stats


class ContextManager(IContextManager):
    """
    Context manager for the Strands framework
    Handles global and agent-specific context management
    """
    
    def __init__(self, memory_store: IMemoryStore, config: Dict[str, Any]):
        self.memory_store = memory_store
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Context storage
        self.global_context: Dict[str, Any] = {}
        self.agent_contexts: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.context_snapshots: Dict[str, Dict[str, Any]] = {}
        
        # Synchronization tracking
        self.last_sync_time = datetime.now()
        self.sync_interval_seconds = config.get("sync_interval_seconds", 60)
        self.sync_operations_count = 0
        
        # Context versioning and isolation
        self.context_versions: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.isolation_policies = self._load_isolation_policies()
        
        # Reference to parent framework for advanced features
        self.framework = None
    
    async def initialize(self) -> None:
        """Initialize context manager"""
        try:
            # Load global context from memory store
            await self._load_global_context()
            
            # Load agent contexts
            await self._load_agent_contexts()
            
            # Start periodic synchronization
            asyncio.create_task(self._periodic_sync())
            
            self.logger.info("Context Manager initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing context manager: {e}")
            raise
    
    async def get_global_context(self) -> Dict[str, Any]:
        """Get global system context"""
        return self.global_context.copy()
    
    async def get_agent_context(self, agent_id: str) -> Dict[str, Any]:
        """Get agent-specific context"""
        return self.agent_contexts[agent_id].copy()
    
    async def update_global_context(self, updates: Dict[str, Any]) -> bool:
        """Update global system context"""
        try:
            self.global_context.update(updates)
            self.global_context["last_updated"] = datetime.now().isoformat()
            
            # Persist to memory store
            await self._persist_global_context()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating global context: {e}")
            return False
    
    async def update_agent_context(self, agent_id: str, updates: Dict[str, Any]) -> bool:
        """Update agent-specific context"""
        try:
            # Store old values for change notification
            old_values = {}
            for key in updates.keys():
                old_values[key] = self.agent_contexts[agent_id].get(key)
            
            # Update context
            self.agent_contexts[agent_id].update(updates)
            self.agent_contexts[agent_id]["last_updated"] = datetime.now().isoformat()
            
            # Notify synchronizer of changes
            if self.framework and hasattr(self.framework, 'context_synchronizer'):
                for key, new_value in updates.items():
                    old_value = old_values.get(key)
                    if old_value != new_value:
                        await self.framework.context_synchronizer.notify_context_change(
                            agent_id, key, old_value, new_value
                        )
            
            # Persist to memory store
            await self._persist_agent_context(agent_id)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating agent context: {e}")
            return False
    
    async def create_context_snapshot(self, context_id: str) -> str:
        """Create snapshot of current context state"""
        try:
            snapshot = {
                "global_context": self.global_context.copy(),
                "agent_contexts": {k: v.copy() for k, v in self.agent_contexts.items()},
                "timestamp": datetime.now().isoformat()
            }
            
            snapshot_id = f"{context_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.context_snapshots[snapshot_id] = snapshot
            
            return snapshot_id
            
        except Exception as e:
            self.logger.error(f"Error creating context snapshot: {e}")
            return ""
    
    async def restore_context_snapshot(self, snapshot_id: str) -> bool:
        """Restore context from snapshot"""
        try:
            if snapshot_id not in self.context_snapshots:
                return False
            
            snapshot = self.context_snapshots[snapshot_id]
            
            self.global_context = snapshot["global_context"].copy()
            self.agent_contexts = defaultdict(dict)
            for agent_id, context in snapshot["agent_contexts"].items():
                self.agent_contexts[agent_id] = context.copy()
            
            # Persist restored context
            await self._persist_global_context()
            for agent_id in self.agent_contexts:
                await self._persist_agent_context(agent_id)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring context snapshot: {e}")
            return False
    
    async def synchronize_context(self, agent_ids: List[str]) -> bool:
        """Synchronize context between specified agents"""
        try:
            # Use the framework's real-time synchronization
            if hasattr(self, 'framework'):
                shared_keys = set()
                for agent_id in agent_ids:
                    shared_keys.update(self.agent_contexts[agent_id].keys())
                
                return await self.framework.synchronize_context_real_time(agent_ids, list(shared_keys))
            
            # Fallback to basic synchronization
            self.sync_operations_count += 1
            
            # Get shared context keys
            shared_keys = set()
            for agent_id in agent_ids:
                shared_keys.update(self.agent_contexts[agent_id].keys())
            
            # Synchronize shared keys with conflict resolution
            for key in shared_keys:
                latest_value = None
                latest_timestamp = None
                conflict_detected = False
                
                # Find the most recent value and detect conflicts
                values_by_timestamp = []
                for agent_id in agent_ids:
                    if key in self.agent_contexts[agent_id]:
                        value = self.agent_contexts[agent_id][key]
                        if isinstance(value, dict) and "timestamp" in value:
                            timestamp = datetime.fromisoformat(value["timestamp"])
                            values_by_timestamp.append((timestamp, value, agent_id))
                
                if values_by_timestamp:
                    # Sort by timestamp
                    values_by_timestamp.sort(key=lambda x: x[0], reverse=True)
                    
                    # Check for conflicts (multiple values with same timestamp)
                    if len(values_by_timestamp) > 1:
                        latest_time = values_by_timestamp[0][0]
                        same_time_values = [v for t, v, a in values_by_timestamp if t == latest_time]
                        if len(same_time_values) > 1:
                            conflict_detected = True
                            self.logger.warning(f"Context conflict detected for key '{key}' among agents: {agent_ids}")
                    
                    # Use the most recent value
                    latest_timestamp, latest_value, source_agent = values_by_timestamp[0]
                    
                    # Update all agents with latest value
                    for agent_id in agent_ids:
                        if key not in self.agent_contexts[agent_id] or self.agent_contexts[agent_id][key] != latest_value:
                            self.agent_contexts[agent_id][key] = latest_value
                            self.agent_contexts[agent_id][f"{key}_sync_timestamp"] = datetime.now().isoformat()
                            self.agent_contexts[agent_id][f"{key}_source"] = source_agent
                            
                            if conflict_detected:
                                self.agent_contexts[agent_id][f"{key}_conflict_resolved"] = True
            
            # Persist synchronized contexts
            for agent_id in agent_ids:
                await self._persist_agent_context(agent_id)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error synchronizing context: {e}")
            return False
    
    async def _load_global_context(self) -> None:
        """Load global context from memory store"""
        try:
            # Get recent system events that contain global context
            events = await self.memory_store.get_system_events("global_context_updated", limit=1)
            
            if events:
                latest_event = events[0]
                self.global_context = latest_event.data.get("context", {})
            
        except Exception as e:
            self.logger.error(f"Error loading global context: {e}")
    
    async def _load_agent_contexts(self) -> None:
        """Load agent contexts from memory store"""
        try:
            # Get recent agent state updates
            events = await self.memory_store.get_system_events("agent_context_updated", limit=100)
            
            for event in events:
                agent_id = event.data.get("agent_id")
                context = event.data.get("context", {})
                
                if agent_id and context:
                    self.agent_contexts[agent_id] = context
            
        except Exception as e:
            self.logger.error(f"Error loading agent contexts: {e}")
    
    async def _persist_global_context(self) -> None:
        """Persist global context to memory store"""
        try:
            from ..core.models import SystemEvent
            
            event = SystemEvent(
                event_type="global_context_updated",
                source="context_manager",
                data={"context": self.global_context}
            )
            
            await self.memory_store.store_system_event(event)
            
        except Exception as e:
            self.logger.error(f"Error persisting global context: {e}")
    
    async def _persist_agent_context(self, agent_id: str) -> None:
        """Persist agent context to memory store"""
        try:
            from ..core.models import SystemEvent
            
            event = SystemEvent(
                event_type="agent_context_updated",
                source="context_manager",
                data={
                    "agent_id": agent_id,
                    "context": self.agent_contexts[agent_id]
                }
            )
            
            await self.memory_store.store_system_event(event)
            
        except Exception as e:
            self.logger.error(f"Error persisting agent context: {e}")
    
    async def _periodic_sync(self) -> None:
        """Periodic context synchronization"""
        while True:
            try:
                await asyncio.sleep(self.sync_interval_seconds)
                
                # Perform periodic maintenance
                current_time = datetime.now()
                
                # Clean up old snapshots (keep last 10)
                if len(self.context_snapshots) > 10:
                    sorted_snapshots = sorted(
                        self.context_snapshots.items(),
                        key=lambda x: x[1]["timestamp"],
                        reverse=True
                    )
                    
                    # Keep only the 10 most recent
                    self.context_snapshots = dict(sorted_snapshots[:10])
                
                self.last_sync_time = current_time
                
            except Exception as e:
                self.logger.error(f"Error in periodic sync: {e}")
    
    def _load_isolation_policies(self) -> Dict[str, Dict[str, Any]]:
        """Load context isolation policies for different agent types"""
        return {
            "high": {
                "allow_cross_agent_access": False,
                "allow_global_context_write": False,
                "context_encryption": True
            },
            "medium": {
                "allow_cross_agent_access": True,
                "allow_global_context_write": False,
                "context_encryption": False
            },
            "low": {
                "allow_cross_agent_access": True,
                "allow_global_context_write": True,
                "context_encryption": False
            },
            "none": {
                "allow_cross_agent_access": True,
                "allow_global_context_write": True,
                "context_encryption": False
            }
        }
    
    async def create_context_version(self, agent_id: str, context_key: str) -> int:
        """Create new version of context key for agent"""
        try:
            current_version = self.context_versions[agent_id][context_key]
            new_version = current_version + 1
            self.context_versions[agent_id][context_key] = new_version
            
            # Store version metadata
            version_key = f"{context_key}_version"
            self.agent_contexts[agent_id][version_key] = new_version
            self.agent_contexts[agent_id][f"{context_key}_version_timestamp"] = datetime.now().isoformat()
            
            return new_version
            
        except Exception as e:
            self.logger.error(f"Error creating context version: {e}")
            return 0
    
    async def get_context_version(self, agent_id: str, context_key: str) -> int:
        """Get current version of context key for agent"""
        return self.context_versions[agent_id][context_key]
    
    async def apply_isolation_policy(self, agent_id: str, isolation_level: str) -> bool:
        """Apply isolation policy to agent context"""
        try:
            policy = self.isolation_policies.get(isolation_level, self.isolation_policies["medium"])
            
            # Store isolation policy in agent context
            self.agent_contexts[agent_id]["_isolation_policy"] = policy
            self.agent_contexts[agent_id]["_isolation_level"] = isolation_level
            
            # Apply encryption if required
            if policy.get("context_encryption", False):
                await self._encrypt_agent_context(agent_id)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error applying isolation policy: {e}")
            return False
    
    async def _encrypt_agent_context(self, agent_id: str) -> None:
        """Encrypt sensitive context data for agent"""
        try:
            # This is a placeholder for actual encryption implementation
            # In a real implementation, you would use proper encryption libraries
            context = self.agent_contexts[agent_id]
            
            # Mark sensitive keys for encryption
            sensitive_keys = ["credentials", "tokens", "private_data", "user_data"]
            
            for key in sensitive_keys:
                if key in context:
                    # Placeholder encryption (in real implementation, use proper encryption)
                    context[f"{key}_encrypted"] = True
                    context[f"{key}_encryption_timestamp"] = datetime.now().isoformat()
            
        except Exception as e:
            self.logger.error(f"Error encrypting agent context: {e}")
    
    def set_framework_reference(self, framework) -> None:
        """Set reference to parent framework for advanced features"""
        self.framework = framework