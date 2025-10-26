"""
Tests for intelligent request routing and load balancing functionality
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from src.agentic.agents.orchestrator_agent import OrchestratorAgent
from src.agentic.core.models import AgentConfiguration, AgentCapability, AgentMetrics


class TestIntelligentRouting:
    """Test intelligent request routing and load balancing"""
    
    @pytest.fixture
    def orchestrator_config(self):
        """Configuration for orchestrator agent"""
        return {
            "health_check_interval": 30,
            "performance_monitoring_interval": 60,
            "routing_strategy": "least_loaded",
            "failover_enabled": True,
            "max_agent_failures": 3,
            "max_agent_load": 100
        }
    
    @pytest.fixture
    def orchestrator(self, orchestrator_config):
        """Create orchestrator agent for testing"""
        orchestrator = OrchestratorAgent(
            config=orchestrator_config,
            strands_framework=None,
            mcp_server=None
        )
        
        # Register some test agents
        test_agents = [
            ("cost_management", "cost_management"),
            ("resource_management", "resource_management"),
            ("forecasting", "forecasting"),
            ("user_interface", "user_interface"),
            ("approval", "approval")
        ]
        
        for agent_id, agent_type in test_agents:
            config = AgentConfiguration(
                agent_id=agent_id,
                agent_type=agent_type,
                capabilities=[
                    AgentCapability(
                        name=f"{agent_type}_capability",
                        description=f"Capability for {agent_type}",
                        input_schema={},
                        output_schema={},
                        required_permissions=[]
                    )
                ]
            )
            orchestrator.agent_registry[agent_id] = config
            orchestrator.agent_health_status[agent_id] = True
            orchestrator.load_balancing_state[agent_id] = 0
            orchestrator.agent_failure_counts[agent_id] = 0
        
        return orchestrator
    
    @pytest.mark.asyncio
    async def test_request_analysis(self, orchestrator):
        """Test intelligent request analysis"""
        # Test simple cost request
        analysis = await orchestrator._analyze_request_for_routing(
            "cost_analysis",
            {"query": "show me cost breakdown"},
            {}
        )
        
        assert analysis["complexity"] in ["low", "medium", "high"]
        assert any(domain == "cost" for domain, _ in analysis["domain_keywords"])
        assert analysis["cross_domain"] is False
        
        # Test complex cross-domain request
        analysis = await orchestrator._analyze_request_for_routing(
            "comprehensive_analysis",
            {"query": "analyze cost trends and resource utilization for forecasting"},
            {"priority": "high"}
        )
        
        assert analysis["complexity"] == "high"
        assert analysis["cross_domain"] is True
        domains = set(domain for domain, _ in analysis["domain_keywords"])
        assert len(domains) > 1
    
    @pytest.mark.asyncio
    async def test_candidate_agent_determination(self, orchestrator):
        """Test candidate agent determination based on analysis"""
        # Test cost analysis request
        routing_analysis = {
            "domain_keywords": [("cost", "cost"), ("cost", "budget")],
            "complexity": "medium",
            "cross_domain": False
        }
        
        candidates = orchestrator._determine_candidate_agents(
            "cost_analysis",
            {"query": "cost breakdown"},
            routing_analysis
        )
        
        assert "cost_management" in candidates
        assert "forecasting" in candidates
        assert "user_interface" in candidates  # fallback