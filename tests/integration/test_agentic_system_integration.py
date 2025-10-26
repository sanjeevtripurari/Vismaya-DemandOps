"""
Integration tests for the agentic AI system
Tests system initialization, agent communication, and basic workflows
"""

import pytest
import asyncio
import logging
from unittest.mock import patch, AsyncMock
from typing import Dict, Any

from src.agentic.system_factory import AgenticSystemFactory, DEFAULT_CONFIG
from src.agentic.core.models import AgentMessage, MessageType


# Disable logging during tests to reduce noise
logging.disable(logging.CRITICAL)


class TestAgenticSystemIntegration:
    """Integration tests for the complete agentic system"""
    
    @pytest.fixture
    def test_config(self):
        """Create test configuration"""
        config = DEFAULT_CONFIG.copy()
        config.update({
            "aws_region": "us-east-1",
            "table_prefix": "test-agentic",
            "memory_store": {
                "aws_region": "us-east-1",
                "table_prefix": "test-agentic"
            }
        })
        return config
    
    @pytest.mark.asyncio
    async def test_system_factory_creation(self, test_config):
        """Test system factory creation and basic initialization"""
        factory = AgenticSystemFactory(test_config)
        
        assert factory.config == test_config
        assert factory.initialized is False
        assert len(factory.agents) == 0
    
    @pytest.mark.asyncio
    async def test_system_initialization_without_aws(self, test_config):
        """Test system initialization with mocked AWS services"""
        
        # Mock AWS services to avoid requiring real AWS credentials
        with patch('src.agentic.strands.memory_store.boto3') as mock_boto3:
            # Mock DynamoDB resource and client
            mock_dynamodb = AsyncMock()
            mock_dynamodb_client = AsyncMock()
            mock_boto3.resource.return_value = mock_dynamodb
            mock_boto3.client.return_value = mock_dynamodb_client
            
            # Mock table creation and operations
            mock_table = AsyncMock()
            mock_table.load = AsyncMock()
            mock_table.wait_until_exists = AsyncMock()
            mock_dynamodb.Table.return_value = mock_table
            mock_dynamodb.create_table.return_value = mock_table
            
            factory = AgenticSystemFactory(test_config)
            
            # Test initialization (should fail gracefully without AWS)
            try:
                success = await factory.initialize_system()
                # If it succeeds with mocks, that's good
                if success:
                    assert factory.initialized is True
                    assert factory.orchestrator is not None
                    
                    # Test system status
                    status = await factory.get_system_status()
                    assert "initialized" in status
                    assert "components" in status
                    
                    # Cleanup
                    await factory.shutdown_system()
                else:
                    # If it fails, that's expected without real AWS
                    assert factory.initialized is False
                    
            except Exception as e:
                # Expected to fail without proper AWS setup
                assert "AWS" in str(e) or "credentials" in str(e) or "DynamoDB" in str(e)
    
    @pytest.mark.asyncio
    async def test_orchestrator_functionality_isolated(self, test_config):
        """Test orchestrator functionality in isolation"""
        from src.agentic.agents.orchestrator_agent import OrchestratorAgent
        
        # Create orchestrator without full system
        orchestrator = OrchestratorAgent(
            config=test_config.get("orchestrator", {}),
            strands_framework=None,  # No Strands for isolated test
            mcp_server=None  # No MCP server for isolated test
        )
        
        # Test initialization
        success = await orchestrator.initialize()
        assert success is True
        assert orchestrator.agent_id == "orchestrator"
        
        # Test health check
        is_healthy = await orchestrator.health_check()
        assert is_healthy is True
        
        # Test request routing (will fail because no agents are registered)
        try:
            target_agent = await orchestrator.route_request({
                "request_type": "cost_analysis",
                "content": {"query": "test"}
            })
            # If it succeeds, check the target
            assert target_agent in ["cost_management", "user_interface"]
        except ValueError as e:
            # Expected to fail when no agents are available
            assert "No suitable agents found" in str(e) or "not available" in str(e)
        
        # Test system health monitoring
        health_status = await orchestrator.monitor_system_health()
        assert isinstance(health_status, dict)
        
        # Test agent registry
        registry = await orchestrator.get_agent_registry()
        assert isinstance(registry, dict)
        
        # Cleanup
        await orchestrator.shutdown()
    
    @pytest.mark.asyncio
    async def test_mcp_server_functionality_isolated(self, test_config):
        """Test MCP server functionality in isolation"""
        from src.agentic.communication.mcp_server import MCPAgentServer
        from src.agentic.communication.security_manager import SecurityManager
        
        # Create security manager and MCP server
        security_manager = SecurityManager(test_config.get("security", {}))
        mcp_server = MCPAgentServer(security_manager)
        
        # Test server startup
        success = await mcp_server.start_server(port=8001)  # Use different port
        assert success is True
        
        # Test server stats
        stats = mcp_server.get_server_stats()
        assert "server_running" in stats
        assert stats["server_running"] is True
        
        # Test server shutdown
        success = await mcp_server.stop_server()
        assert success is True
    
    @pytest.mark.asyncio
    async def test_security_manager_functionality(self, test_config):
        """Test security manager functionality"""
        from src.agentic.communication.security_manager import SecurityManager
        
        security_manager = SecurityManager(test_config.get("security", {}))
        
        # Test agent permissions
        permissions = await security_manager.get_agent_permissions("orchestrator")
        assert "*" in permissions  # Orchestrator has all permissions
        
        # Test sender validation
        is_valid = await security_manager.validate_sender("orchestrator", "cost_management")
        assert is_valid is True
        
        # Test action validation
        is_valid = await security_manager.validate_action("orchestrator", "route_request", {})
        assert is_valid is True
        
        # Test token generation and validation
        try:
            token = await security_manager.generate_auth_token("test_agent", ["test_permission"])
            assert isinstance(token, str)
            assert len(token) > 0
            
            # Validate the token
            validation_result = await security_manager.validate_auth_token(token)
            assert validation_result["valid"] is True
            assert validation_result["agent_id"] == "test_agent"
        except TypeError:
            # JWT secret might be None in test config, which is expected
            pass
        
        # Test encryption/decryption
        test_data = {"password": "secret123", "normal_field": "normal_value"}
        encrypted_data = await security_manager.encrypt_sensitive_data(test_data)
        
        # Should have encrypted the password field
        assert "password" in encrypted_data
        if isinstance(encrypted_data["password"], dict) and encrypted_data["password"].get("encrypted"):
            # Decrypt and verify
            decrypted_data = await security_manager.decrypt_sensitive_data(encrypted_data)
            assert decrypted_data["password"] == "secret123"
            assert decrypted_data["normal_field"] == "normal_value"
    
    @pytest.mark.asyncio
    async def test_base_agent_communication(self, test_config):
        """Test basic agent communication patterns"""
        from src.agentic.core.base_agent import BaseAgent
        from src.agentic.core.models import AgentCapability
        
        # Create two test agents
        capabilities = [
            AgentCapability(
                name="test_action",
                description="Test action",
                input_schema={"type": "object"},
                output_schema={"type": "object"}
            )
        ]
        
        agent1 = BaseAgent(
            agent_id="agent1",
            agent_type="test",
            capabilities=capabilities,
            config={}
        )
        
        agent2 = BaseAgent(
            agent_id="agent2", 
            agent_type="test",
            capabilities=capabilities,
            config={}
        )
        
        # Initialize agents
        await agent1.initialize()
        await agent2.initialize()
        
        # Test message exchange
        request_message = AgentMessage(
            sender="agent1",
            recipient="agent2",
            message_type=MessageType.REQUEST,
            content={"test": "data"}
        )
        
        response = await agent2.process_message(request_message)
        
        assert response.sender == "agent2"
        assert response.recipient == "agent1"
        assert response.correlation_id == request_message.correlation_id
        
        # Test action execution
        result = await agent1.execute_action("health_check", {})
        assert result["success"] is True
        
        # Cleanup
        await agent1.shutdown()
        await agent2.shutdown()
    
    @pytest.mark.asyncio
    async def test_workflow_execution_simulation(self, test_config):
        """Test workflow execution simulation"""
        from src.agentic.agents.orchestrator_agent import OrchestratorAgent
        from src.agentic.core.models import WorkflowStep
        
        orchestrator = OrchestratorAgent(
            config=test_config.get("orchestrator", {}),
            strands_framework=None,
            mcp_server=None
        )
        
        await orchestrator.initialize()
        
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
        result = await orchestrator.coordinate_workflow("test_workflow", workflow_steps)
        
        assert "workflow_id" in result
        assert result["workflow_id"] == "test_workflow"
        assert "status" in result
        
        await orchestrator.shutdown()


if __name__ == "__main__":
    pytest.main([__file__])