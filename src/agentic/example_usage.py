"""
Example usage of the Agentic AI System
Demonstrates how to initialize and use the agentic infrastructure
"""

import asyncio
import logging
from typing import Dict, Any

from .system_factory import create_agentic_system, DEFAULT_CONFIG
from .core.models import AgentMessage, MessageType


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main example function"""
    try:
        logger.info("Starting Agentic AI System Example")
        
        # Create system configuration
        config = DEFAULT_CONFIG.copy()
        config.update({
            "aws_region": "us-east-1",
            "table_prefix": "vismaya-agentic-example"
        })
        
        # Initialize the agentic system
        logger.info("Initializing agentic system...")
        system = await create_agentic_system(config)
        
        # Get system status
        status = await system.get_system_status()
        logger.info(f"System status: {status}")
        
        # Test orchestrator functionality
        await test_orchestrator(system)
        
        # Test message routing
        await test_message_routing(system)
        
        # Test workflow coordination
        await test_workflow_coordination(system)
        
        # Keep system running for a bit
        logger.info("System running... (will shutdown in 30 seconds)")
        await asyncio.sleep(30)
        
        # Shutdown system
        logger.info("Shutting down system...")
        await system.shutdown_system()
        
        logger.info("Example completed successfully")
        
    except Exception as e:
        logger.error(f"Error in example: {e}")
        raise


async def test_orchestrator(system):
    """Test orchestrator functionality"""
    try:
        logger.info("Testing orchestrator functionality...")
        
        orchestrator = system.orchestrator
        
        # Test health monitoring
        health_status = await orchestrator.monitor_system_health()
        logger.info(f"System health: {health_status}")
        
        # Test agent registry
        registry = await orchestrator.get_agent_registry()
        logger.info(f"Agent registry: {list(registry.keys())}")
        
        # Test request routing
        routing_result = await orchestrator.route_request({
            "request_type": "cost_analysis",
            "content": {"query": "Show me AWS costs for last month"}
        })
        logger.info(f"Routing result: {routing_result}")
        
    except Exception as e:
        logger.error(f"Error testing orchestrator: {e}")


async def test_message_routing(system):
    """Test message routing through MCP server"""
    try:
        logger.info("Testing message routing...")
        
        mcp_server = system.mcp_server
        orchestrator = system.orchestrator
        
        # Create a test message
        test_message = AgentMessage(
            sender="test_client",
            recipient="orchestrator",
            message_type=MessageType.REQUEST,
            content={
                "request_type": "health_check",
                "parameters": {}
            }
        )
        
        # Route message through MCP server
        response = await mcp_server.route_message(test_message)
        logger.info(f"Message routing response: {response.content}")
        
    except Exception as e:
        logger.error(f"Error testing message routing: {e}")


async def test_workflow_coordination(system):
    """Test workflow coordination"""
    try:
        logger.info("Testing workflow coordination...")
        
        orchestrator = system.orchestrator
        
        # Define a simple workflow
        workflow_steps = [
            {
                "step_id": "step1",
                "agent_id": "orchestrator",
                "action": "health_check",
                "parameters": {}
            },
            {
                "step_id": "step2",
                "agent_id": "orchestrator",
                "action": "get_state",
                "parameters": {},
                "dependencies": ["step1"]
            }
        ]
        
        # Execute workflow
        workflow_result = await orchestrator.coordinate_workflow("test_workflow", workflow_steps)
        logger.info(f"Workflow result: {workflow_result}")
        
    except Exception as e:
        logger.error(f"Error testing workflow coordination: {e}")


async def test_strands_framework(system):
    """Test Strands framework functionality"""
    try:
        logger.info("Testing Strands framework...")
        
        strands = system.strands_framework
        
        # Test context management
        await strands.update_context("test_agent", {
            "test_key": "test_value",
            "timestamp": "2024-01-01T00:00:00"
        })
        
        # Get shared context
        context = await strands.get_shared_context(["test_key"])
        logger.info(f"Shared context: {context}")
        
        # Create conversation thread
        thread_id = await strands.create_conversation_thread(["agent1", "agent2"])
        logger.info(f"Created conversation thread: {thread_id}")
        
        # Store conversation message
        test_message = AgentMessage(
            sender="agent1",
            recipient="agent2",
            message_type=MessageType.NOTIFICATION,
            content={"message": "Hello from agent1"}
        )
        
        await strands.store_conversation_message(thread_id, test_message)
        
        # Get conversation history
        history = await strands.get_conversation_history(thread_id)
        logger.info(f"Conversation history: {len(history)} messages")
        
    except Exception as e:
        logger.error(f"Error testing Strands framework: {e}")


if __name__ == "__main__":
    asyncio.run(main())