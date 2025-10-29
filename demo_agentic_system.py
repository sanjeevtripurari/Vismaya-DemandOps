#!/usr/bin/env python3
"""
Demonstration of the Agentic AI System Core Infrastructure
Shows the basic functionality without requiring AWS credentials
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from src.agentic.core.base_agent import BaseAgent
from src.agentic.core.models import (
    AgentMessage, MessageType, AgentCapability, DecisionProposal, 
    RiskLevel, DecisionStatus
)
from src.agentic.agents.orchestrator_agent import OrchestratorAgent
from src.agentic.communication.mcp_server import MCPAgentServer
from src.agentic.communication.security_manager import SecurityManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DemoAgent(BaseAgent):
    """Demo agent for testing purposes"""
    
    def __init__(self, agent_id: str, agent_type: str):
        capabilities = [
            AgentCapability(
                name="demo_action",
                description="Demo action for testing",
                input_schema={"type": "object"},
                output_schema={"type": "object"}
            ),
            AgentCapability(
                name="process_request",
                description="Process demo requests",
                input_schema={
                    "type": "object",
                    "required": ["request_type"],
                    "properties": {
                        "request_type": {"type": "string"},
                        "data": {"type": "object"}
                    }
                },
                output_schema={"type": "object"}
            )
        ]
        
        super().__init__(
            agent_id=agent_id,
            agent_type=agent_type,
            capabilities=capabilities,
            config={"demo": True}
        )
    
    async def _agent_specific_initialization(self):
        """Demo agent initialization"""
        self.demo_data = {"initialized": True, "timestamp": datetime.now()}
        logger.info(f"Demo agent {self.agent_id} initialized")
    
    async def _handle_request(self, message: AgentMessage) -> AgentMessage:
        """Handle demo requests"""
        request_type = message.content.get("request_type", "unknown")
        
        if request_type == "demo_analysis":
            result = {
                "analysis_result": "Demo analysis completed",
                "agent_id": self.agent_id,
                "timestamp": datetime.now().isoformat(),
                "data": message.content.get("data", {})
            }
        else:
            result = {
                "message": f"Processed {request_type} request",
                "agent_id": self.agent_id,
                "timestamp": datetime.now().isoformat()
            }
        
        return AgentMessage(
            sender=self.agent_id,
            recipient=message.sender,
            message_type=MessageType.RESPONSE,
            content=result,
            correlation_id=message.correlation_id
        )


async def demo_basic_agent_functionality():
    """Demonstrate basic agent functionality"""
    logger.info("=== Demo: Basic Agent Functionality ===")
    
    # Create demo agent
    agent = DemoAgent("demo_agent_1", "demo")
    
    # Initialize agent
    await agent.initialize()
    logger.info(f"Agent {agent.agent_id} initialized successfully")
    
    # Test health check
    is_healthy = await agent.health_check()
    logger.info(f"Agent health check: {is_healthy}")
    
    # Test action execution
    result = await agent.execute_action("demo_action", {"test": "data"})
    logger.info(f"Action execution result: {result['success']}")
    
    # Test message processing
    test_message = AgentMessage(
        sender="demo_client",
        recipient=agent.agent_id,
        message_type=MessageType.REQUEST,
        content={
            "request_type": "demo_analysis",
            "data": {"sample": "data"}
        }
    )
    
    response = await agent.process_message(test_message)
    logger.info(f"Message processing response: {response.content['analysis_result']}")
    
    # Get agent state
    state = await agent.get_state()
    logger.info(f"Agent status: {state.status.value}")
    
    # Shutdown agent
    await agent.shutdown()
    logger.info("Agent shutdown completed")


async def demo_orchestrator_functionality():
    """Demonstrate orchestrator functionality"""
    logger.info("=== Demo: Orchestrator Functionality ===")
    
    # Create orchestrator
    orchestrator = OrchestratorAgent(
        config={"health_check_interval": 30},
        strands_framework=None,
        mcp_server=None
    )
    
    # Initialize orchestrator
    await orchestrator.initialize()
    logger.info("Orchestrator initialized successfully")
    
    # Test request routing
    try:
        target_agent = await orchestrator.route_request({
            "request_type": "cost_analysis",
            "content": {"query": "test"}
        })
        logger.info(f"Request routed to: {target_agent}")
    except ValueError as e:
        logger.info(f"Expected routing error (no agents registered): {e}")
    
    # Test system health monitoring
    health_status = await orchestrator.monitor_system_health()
    logger.info(f"System health status: {len(health_status)} agents monitored")
    
    # Test workflow coordination
    workflow_steps = [
        {
            "step_id": "step1",
            "agent_id": "orchestrator",
            "action": "health_check",
            "parameters": {}
        }
    ]
    
    workflow_result = await orchestrator.coordinate_workflow("demo_workflow", workflow_steps)
    logger.info(f"Workflow execution status: {workflow_result['status']}")
    
    # Shutdown orchestrator
    await orchestrator.shutdown()
    logger.info("Orchestrator shutdown completed")


async def demo_mcp_server_functionality():
    """Demonstrate MCP server functionality"""
    logger.info("=== Demo: MCP Server Functionality ===")
    
    # Create security manager and MCP server
    security_manager = SecurityManager({
        "jwt_secret": "demo_secret_key_for_testing",
        "jwt_algorithm": "HS256"
    })
    
    mcp_server = MCPAgentServer(security_manager)
    
    # Start MCP server
    await mcp_server.start_server(port=8002)  # Use different port for demo
    logger.info("MCP Server started successfully")
    
    # Create demo agents
    agent1 = DemoAgent("demo_agent_1", "demo")
    agent2 = DemoAgent("demo_agent_2", "demo")
    
    await agent1.initialize()
    await agent2.initialize()
    
    # Register agents with MCP server
    await mcp_server.register_agent(agent1)
    await mcp_server.register_agent(agent2)
    logger.info("Agents registered with MCP server")
    
    # Test message routing through MCP server
    test_message = AgentMessage(
        sender="demo_agent_1",
        recipient="demo_agent_2",
        message_type=MessageType.REQUEST,
        content={
            "request_type": "demo_analysis",
            "data": {"routed_through": "mcp_server"}
        }
    )
    
    response = await mcp_server.route_message(test_message)
    logger.info(f"MCP routed message response: {response.content.get('analysis_result', 'Success')}")
    
    # Get server stats
    stats = mcp_server.get_server_stats()
    logger.info(f"MCP Server stats - Messages: {stats['message_count']}, Agents: {stats['registered_agents']}")
    
    # Cleanup
    await agent1.shutdown()
    await agent2.shutdown()
    await mcp_server.stop_server()
    logger.info("MCP Server demo completed")


async def demo_decision_proposal_workflow():
    """Demonstrate decision proposal workflow"""
    logger.info("=== Demo: Decision Proposal Workflow ===")
    
    # Create decision proposal
    proposal = DecisionProposal(
        title="Demo Cost Optimization",
        description="Optimize AWS costs by rightsizing EC2 instances",
        required_approvers=["ceo", "cto"],
        estimated_cost_impact=5000.0,
        risk_level=RiskLevel.MEDIUM,
        recommendations=[
            "Downsize 3 EC2 instances from m5.large to m5.medium",
            "Schedule non-production instances to stop during off-hours",
            "Implement automated cost monitoring alerts"
        ]
    )
    
    logger.info(f"Created decision proposal: {proposal.title}")
    logger.info(f"Estimated cost impact: ${proposal.estimated_cost_impact}")
    logger.info(f"Risk level: {proposal.risk_level.value}")
    
    # Simulate approval workflow
    proposal.add_approval_response("ceo", "approved", "Good cost savings opportunity")
    logger.info("CEO approved the proposal")
    
    proposal.add_approval_response("cto", "approved", "Technical approach looks sound")
    logger.info("CTO approved the proposal")
    
    # Check approval status
    if proposal.is_approved():
        proposal.status = DecisionStatus.APPROVED
        logger.info("Decision proposal fully approved!")
        
        # Get approval summary
        summary = proposal.get_approval_summary()
        logger.info(f"Approval summary: {summary['approved']}/{summary['total_required']} approvals received")
    
    logger.info("Decision proposal workflow demo completed")


async def demo_security_functionality():
    """Demonstrate security functionality"""
    logger.info("=== Demo: Security Functionality ===")
    
    security_manager = SecurityManager({
        "jwt_secret": "demo_secret_key_for_testing",
        "jwt_algorithm": "HS256"
    })
    
    # Test agent permissions
    permissions = await security_manager.get_agent_permissions("orchestrator")
    logger.info(f"Orchestrator permissions: {permissions}")
    
    # Test communication validation
    is_valid = await security_manager.validate_sender("orchestrator", "cost_management")
    logger.info(f"Communication validation (orchestrator -> cost_management): {is_valid}")
    
    # Test action validation
    is_valid = await security_manager.validate_action("cost_management", "cost_analysis", {})
    logger.info(f"Action validation (cost_management.cost_analysis): {is_valid}")
    
    # Test token generation and validation
    token = await security_manager.generate_auth_token("demo_agent", ["demo_permission"])
    logger.info(f"Generated auth token: {token[:20]}...")
    
    validation_result = await security_manager.validate_auth_token(token)
    logger.info(f"Token validation result: {validation_result['valid']}")
    
    # Test data encryption
    sensitive_data = {
        "api_key": "secret_api_key_123",
        "password": "super_secret_password",
        "normal_field": "this is not sensitive"
    }
    
    encrypted_data = await security_manager.encrypt_sensitive_data(sensitive_data)
    logger.info("Sensitive data encrypted successfully")
    
    decrypted_data = await security_manager.decrypt_sensitive_data(encrypted_data)
    logger.info(f"Data decryption successful: {decrypted_data['normal_field']}")
    
    logger.info("Security functionality demo completed")


async def main():
    """Main demo function"""
    logger.info("Starting Agentic AI System Core Infrastructure Demo")
    logger.info("=" * 60)
    
    try:
        # Run all demos
        await demo_basic_agent_functionality()
        await asyncio.sleep(1)  # Brief pause between demos
        
        await demo_orchestrator_functionality()
        await asyncio.sleep(1)
        
        await demo_mcp_server_functionality()
        await asyncio.sleep(1)
        
        await demo_decision_proposal_workflow()
        await asyncio.sleep(1)
        
        await demo_security_functionality()
        
        logger.info("=" * 60)
        logger.info("All demos completed successfully!")
        logger.info("The agentic AI system core infrastructure is working correctly.")
        
    except Exception as e:
        logger.error(f"Demo failed with error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())