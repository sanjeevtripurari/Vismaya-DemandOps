"""
Test script for context synchronization functionality
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from .framework import StrandsFramework, ContextManager
from .memory_store import DynamoDBMemoryStore
from .context_synchronizer import ContextSynchronizer, SyncStrategy, ConflictResolution


# Mock memory store for testing
class MockMemoryStore:
    def __init__(self):
        self.conversations = {}
        self.agent_states = {}
        self.decisions = {}
        self.system_events = []
    
    async def store_conversation(self, thread_id: str, message) -> bool:
        if thread_id not in self.conversations:
            self.conversations[thread_id] = []
        self.conversations[thread_id].append(message)
        return True
    
    async def retrieve_conversation_history(self, thread_id: str, limit: int = 50):
        return self.conversations.get(thread_id, [])[:limit]
    
    async def store_agent_state(self, agent_id: str, state) -> bool:
        self.agent_states[agent_id] = state
        return True
    
    async def retrieve_agent_state(self, agent_id: str):
        return self.agent_states.get(agent_id)
    
    async def store_decision_proposal(self, proposal) -> bool:
        self.decisions[proposal.proposal_id] = proposal
        return True
    
    async def retrieve_decision_proposal(self, proposal_id: str):
        return self.decisions.get(proposal_id)
    
    async def query_decisions_by_criteria(self, criteria: Dict[str, Any]):
        return list(self.decisions.values())
    
    async def store_system_event(self, event) -> bool:
        self.system_events.append(event)
        return True
    
    async def get_system_events(self, event_type=None, limit=100):
        events = self.system_events
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[:limit]


async def test_context_synchronization():
    """Test context synchronization functionality"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Create mock memory store
    memory_store = MockMemoryStore()
    
    # Configuration
    config = {
        "sync_interval_seconds": 30,
        "batch_sync_interval": 2.0,
        "agent_priorities": {
            "orchestrator": 100,
            "cost_management": 80,
            "resource_management": 80,
            "user_interface": 50
        }
    }
    
    # Initialize Strands framework
    strands = StrandsFramework(memory_store, config)
    await strands.initialize(config)
    
    logger.info("Strands framework initialized")
    
    # Test 1: Subscribe agents to context changes
    logger.info("Test 1: Subscribing agents to context changes")
    
    await strands.subscribe_agent_to_context("orchestrator_1", ["system_status", "budget_alerts"])
    await strands.subscribe_agent_to_context("cost_management_1", ["budget_alerts", "cost_thresholds"])
    await strands.subscribe_agent_to_context("user_interface_1", ["system_status", "user_notifications"])
    
    # Test 2: Update context and trigger synchronization
    logger.info("Test 2: Updating context to trigger synchronization")
    
    # Update context for orchestrator
    await strands.update_context("orchestrator_1", {
        "system_status": {
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "priority": "normal"
        }
    })
    
    # Wait a moment for synchronization
    await asyncio.sleep(1)
    
    # Update context for cost management with conflicting data
    await strands.update_context("cost_management_1", {
        "budget_alerts": {
            "alert_level": "warning",
            "threshold_exceeded": True,
            "timestamp": datetime.now().isoformat()
        }
    })
    
    # Test 3: Check for conflicts
    logger.info("Test 3: Checking for context conflicts")
    
    conflicts = await strands.get_context_conflicts(
        ["orchestrator_1", "cost_management_1", "user_interface_1"],
        ["system_status", "budget_alerts"]
    )
    
    logger.info(f"Detected conflicts: {conflicts}")
    
    # Test 4: Perform immediate synchronization with conflict resolution
    logger.info("Test 4: Performing immediate synchronization")
    
    sync_result = await strands.sync_context_with_strategy(
        ["orchestrator_1", "cost_management_1", "user_interface_1"],
        ["system_status", "budget_alerts"],
        strategy="immediate",
        conflict_resolution="last_writer_wins"
    )
    
    logger.info(f"Synchronization result: {sync_result}")
    
    # Test 5: Check final context state
    logger.info("Test 5: Checking final context state")
    
    for agent_id in ["orchestrator_1", "cost_management_1", "user_interface_1"]:
        context = await strands.context_manager.get_agent_context(agent_id)
        logger.info(f"Agent {agent_id} context: {context}")
    
    # Test 6: Get framework statistics
    logger.info("Test 6: Getting framework statistics")
    
    stats = strands.get_framework_stats()
    logger.info(f"Framework stats: {stats}")
    
    logger.info("All tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_context_synchronization())