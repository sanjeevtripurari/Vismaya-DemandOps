"""
Agent Testing Framework
Provides comprehensive testing utilities for agentic AI system components
"""

import asyncio
import pytest
from typing import Dict, Any, List, Optional, Type
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import json
import uuid
from dataclasses import dataclass, field

from src.agentic.core.interfaces import (
    IAgentCore, IOrchestrator, ISpecializedAgent, IApprovalAgent,
    IMCPServer, IStrandsFramework, IContextManager, IMemoryStore
)
from src.agentic.core.models import (
    AgentMessage, AgentState, DecisionProposal, WorkflowDefinition,
    SystemEvent, AgentCapability, MessageType, AgentStatus, DecisionStatus
)


@dataclass
class TestScenario:
    """Test scenario definition"""
    name: str
    description: str
    setup_data: Dict[str, Any] = field(default_factory=dict)
    input_data: Dict[str, Any] = field(default_factory=dict)
    expected_output: Dict[str, Any] = field(default_factory=dict)
    validation_rules: List[str] = field(default_factory=list)
    timeout_seconds: int = 30
    cleanup_required: bool = True


@dataclass
class TestResult:
    """Test execution result"""
    scenario_name: str
    success: bool
    execution_time_ms: float
    output_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    validation_results: Dict[str, bool] = field(default_factory=dict)


@dataclass
class TestResults:
    """Collection of test results"""
    results: List[TestResult] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    def add_result(self, scenario_name: str, result: TestResult):
        """Add test result"""
        result.scenario_name = scenario_name
        self.results.append(result)
    
    def get_success_rate(self) -> float:
        """Calculate success rate"""
        if not self.results:
            return 0.0
        successful = sum(1 for r in self.results if r.success)
        return (successful / len(self.results)) * 100.0
    
    def get_failed_tests(self) -> List[TestResult]:
        """Get failed test results"""
        return [r for r in self.results if not r.success]
    
    def finalize(self):
        """Finalize test results"""
        self.end_time = datetime.now()


class MockMCPServer:
    """Mock MCP server for testing"""
    
    def __init__(self):
        self.registered_agents = {}
        self.message_history = []
        self.system_events = []
        self.security_manager = MockSecurityManager()
    
    async def register_agent(self, agent_id: str, agent: IAgentCore) -> bool:
        """Register agent"""
        self.registered_agents[agent_id] = agent
        return True
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister agent"""
        if agent_id in self.registered_agents:
            del self.registered_agents[agent_id]
            return True
        return False
    
    async def route_message(self, message: AgentMessage) -> AgentMessage:
        """Route message between agents"""
        self.message_history.append(message)
        
        # Simulate message routing
        if message.recipient in self.registered_agents:
            target_agent = self.registered_agents[message.recipient]
            response = await target_agent.process_message(message)
            self.message_history.append(response)
            return response
        
        # Return error response for unknown recipient
        return AgentMessage(
            sender="mcp_server",
            recipient=message.sender,
            message_type=MessageType.ERROR,
            content={"error": f"Agent {message.recipient} not found"},
            correlation_id=message.correlation_id
        )
    
    async def broadcast_system_event(self, event: SystemEvent) -> List[AgentMessage]:
        """Broadcast system event"""
        self.system_events.append(event)
        responses = []
        
        for agent_id, agent in self.registered_agents.items():
            event_message = AgentMessage(
                sender="mcp_server",
                recipient=agent_id,
                message_type=MessageType.SYSTEM_EVENT,
                content=event.to_dict()
            )
            response = await agent.process_message(event_message)
            responses.append(response)
        
        return responses
    
    def get_message_history(self) -> List[AgentMessage]:
        """Get message history"""
        return self.message_history.copy()
    
    def clear_history(self):
        """Clear message history"""
        self.message_history.clear()
        self.system_events.clear()


class MockStrandsFramework:
    """Mock Strands framework for testing"""
    
    def __init__(self):
        self.contexts = {}
        self.memory_store = MockMemoryStore()
        self.context_manager = MockContextManager()
    
    async def create_context(self, context_id: str, context_data: Dict[str, Any]) -> bool:
        """Create context"""
        self.contexts[context_id] = {
            "id": context_id,
            "data": context_data,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        return True
    
    async def get_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        """Get context"""
        return self.contexts.get(context_id)
    
    async def update_context(self, context_id: str, updates: Dict[str, Any]) -> bool:
        """Update context"""
        if context_id in self.contexts:
            self.contexts[context_id]["data"].update(updates)
            self.contexts[context_id]["updated_at"] = datetime.now()
            return True
        return False
    
    async def store_conversation(self, thread_id: str, message: AgentMessage) -> bool:
        """Store conversation message"""
        return await self.memory_store.store_conversation(thread_id, message)
    
    async def get_conversation_history(self, thread_id: str, limit: int = 50) -> List[AgentMessage]:
        """Get conversation history"""
        return await self.memory_store.retrieve_conversation_history(thread_id, limit)


class MockMemoryStore:
    """Mock memory store for testing"""
    
    def __init__(self):
        self.conversations = {}
        self.decisions = {}
        self.agent_states = {}
    
    async def store_conversation(self, thread_id: str, message: AgentMessage) -> bool:
        """Store conversation message"""
        if thread_id not in self.conversations:
            self.conversations[thread_id] = []
        self.conversations[thread_id].append(message)
        return True
    
    async def retrieve_conversation_history(self, thread_id: str, limit: int = 50) -> List[AgentMessage]:
        """Retrieve conversation history"""
        messages = self.conversations.get(thread_id, [])
        return messages[-limit:] if limit > 0 else messages
    
    async def store_decision_history(self, decision: DecisionProposal) -> bool:
        """Store decision proposal"""
        self.decisions[decision.proposal_id] = decision
        return True
    
    async def query_similar_decisions(self, current_decision: DecisionProposal) -> List[DecisionProposal]:
        """Find similar past decisions"""
        similar = []
        for decision in self.decisions.values():
            if (decision.risk_level == current_decision.risk_level and
                abs(decision.estimated_cost_impact - current_decision.estimated_cost_impact) < 1000):
                similar.append(decision)
        return similar


class MockContextManager:
    """Mock context manager for testing"""
    
    def __init__(self):
        self.global_context = {}
        self.agent_contexts = {}
        self.conversation_threads = {}
    
    async def get_shared_context(self, context_keys: List[str]) -> Dict[str, Any]:
        """Get shared context"""
        return {key: self.global_context.get(key) for key in context_keys}
    
    async def update_context(self, agent_id: str, context_updates: Dict[str, Any]) -> bool:
        """Update agent context"""
        if agent_id not in self.agent_contexts:
            self.agent_contexts[agent_id] = {}
        self.agent_contexts[agent_id].update(context_updates)
        return True
    
    async def create_conversation_thread(self, participants: List[str]) -> str:
        """Create conversation thread"""
        thread_id = str(uuid.uuid4())
        self.conversation_threads[thread_id] = {
            "participants": participants,
            "created_at": datetime.now(),
            "messages": []
        }
        return thread_id


class MockSecurityManager:
    """Mock security manager for testing"""
    
    def __init__(self):
        self.permissions = {}
        self.communication_policies = {}
    
    async def validate_sender(self, sender: str, recipient: str) -> bool:
        """Validate sender authorization"""
        return True  # Allow all for testing
    
    async def validate_action(self, agent_id: str, action: str, context: Dict[str, Any]) -> bool:
        """Validate action authorization"""
        return True  # Allow all for testing
    
    async def encrypt_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock encryption (no-op for testing)"""
        return data


class TestDataGenerator:
    """Generate test data for various scenarios"""
    
    @staticmethod
    def create_test_message(sender: str = "test_sender", 
                          recipient: str = "test_recipient",
                          message_type: MessageType = MessageType.REQUEST,
                          content: Dict[str, Any] = None) -> AgentMessage:
        """Create test message"""
        return AgentMessage(
            sender=sender,
            recipient=recipient,
            message_type=message_type,
            content=content or {"test": "data"}
        )
    
    @staticmethod
    def create_test_proposal(title: str = "Test Proposal",
                           cost_impact: float = 1000.0,
                           risk_level: str = "medium") -> DecisionProposal:
        """Create test decision proposal"""
        return DecisionProposal(
            title=title,
            description=f"Test proposal: {title}",
            created_by="test_user",
            estimated_cost_impact=cost_impact,
            risk_level=risk_level,
            recommendations=["Test recommendation"]
        )
    
    @staticmethod
    def create_test_workflow(name: str = "Test Workflow") -> WorkflowDefinition:
        """Create test workflow"""
        from src.agentic.core.models import WorkflowStep
        
        steps = [
            WorkflowStep(
                step_id="step1",
                agent_id="agent1",
                action="test_action1"
            ),
            WorkflowStep(
                step_id="step2",
                agent_id="agent2",
                action="test_action2",
                dependencies=["step1"]
            )
        ]
        
        return WorkflowDefinition(
            name=name,
            steps=steps
        )
    
    @staticmethod
    def create_test_system_event(event_type: str = "test_event",
                               source: str = "test_source") -> SystemEvent:
        """Create test system event"""
        return SystemEvent(
            event_type=event_type,
            source=source,
            data={"test": "event_data"},
            severity="info"
        )


class AgentTestFramework:
    """Main testing framework for agents"""
    
    def __init__(self):
        self.mock_mcp_server = MockMCPServer()
        self.mock_strands = MockStrandsFramework()
        self.test_data_generator = TestDataGenerator()
        self.test_environments = {}
        self.performance_metrics = {}
        self.test_execution_history = []
    
    async def setup_test_environment(self, scenario: TestScenario) -> bool:
        """Setup test environment for scenario"""
        try:
            # Create test environment
            env_id = f"test_env_{scenario.name}_{uuid.uuid4().hex[:8]}"
            
            # Setup mock services
            await self._setup_mock_services(scenario.setup_data)
            
            # Store environment reference
            self.test_environments[env_id] = {
                "scenario": scenario,
                "created_at": datetime.now(),
                "mcp_server": self.mock_mcp_server,
                "strands": self.mock_strands
            }
            
            return True
        except Exception as e:
            print(f"Failed to setup test environment: {e}")
            return False
    
    async def cleanup_test_environment(self, scenario: TestScenario) -> bool:
        """Cleanup test environment"""
        try:
            # Clear mock data
            self.mock_mcp_server.clear_history()
            self.mock_strands.contexts.clear()
            self.mock_strands.memory_store.conversations.clear()
            
            # Remove test environments for this scenario
            to_remove = [env_id for env_id, env in self.test_environments.items() 
                        if env["scenario"].name == scenario.name]
            
            for env_id in to_remove:
                del self.test_environments[env_id]
            
            return True
        except Exception as e:
            print(f"Failed to cleanup test environment: {e}")
            return False
    
    async def _setup_mock_services(self, setup_data: Dict[str, Any]):
        """Setup mock services based on scenario data"""
        # Setup mock contexts if specified
        if "contexts" in setup_data:
            for context_id, context_data in setup_data["contexts"].items():
                await self.mock_strands.create_context(context_id, context_data)
        
        # Setup mock conversations if specified
        if "conversations" in setup_data:
            for thread_id, messages in setup_data["conversations"].items():
                for msg_data in messages:
                    message = AgentMessage.from_dict(msg_data)
                    await self.mock_strands.store_conversation(thread_id, message)
    
    async def test_agent_behavior(self, agent: IAgentCore, test_scenarios: List[TestScenario]) -> TestResults:
        """Test agent behavior across multiple scenarios"""
        results = TestResults()
        
        for scenario in test_scenarios:
            start_time = datetime.now()
            
            try:
                # Setup test environment
                setup_success = await self.setup_test_environment(scenario)
                if not setup_success:
                    result = TestResult(
                        scenario_name=scenario.name,
                        success=False,
                        execution_time_ms=0,
                        error_message="Failed to setup test environment"
                    )
                    results.add_result(scenario.name, result)
                    continue
                
                # Register agent with mock MCP server
                await self.mock_mcp_server.register_agent(agent.agent_id, agent)
                
                # Execute test scenario
                result = await self._execute_test_scenario(agent, scenario)
                
                # Calculate execution time
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                result.execution_time_ms = execution_time
                
                results.add_result(scenario.name, result)
                
                # Cleanup if required
                if scenario.cleanup_required:
                    await self.cleanup_test_environment(scenario)
                    
            except Exception as e:
                result = TestResult(
                    scenario_name=scenario.name,
                    success=False,
                    execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                    error_message=str(e)
                )
                results.add_result(scenario.name, result)
        
        results.finalize()
        return results
    
    async def _execute_test_scenario(self, agent: IAgentCore, scenario: TestScenario) -> TestResult:
        """Execute individual test scenario"""
        try:
            # Execute based on scenario input
            if "message" in scenario.input_data:
                # Test message processing
                message_data = scenario.input_data["message"]
                message = AgentMessage.from_dict(message_data)
                response = await agent.process_message(message)
                output_data = {"response": response.to_dict()}
                
            elif "action" in scenario.input_data:
                # Test action execution
                action = scenario.input_data["action"]
                parameters = scenario.input_data.get("parameters", {})
                result = await agent.execute_action(action, parameters)
                output_data = {"result": result}
                
            else:
                # Test health check by default
                health = await agent.health_check()
                state = await agent.get_state()
                output_data = {"health": health, "state": state.to_dict()}
            
            # Validate results
            validation_results = await self._validate_results(output_data, scenario)
            
            # Determine success
            success = all(validation_results.values()) if validation_results else True
            
            return TestResult(
                scenario_name=scenario.name,
                success=success,
                execution_time_ms=0,  # Will be set by caller
                output_data=output_data,
                validation_results=validation_results
            )
            
        except Exception as e:
            return TestResult(
                scenario_name=scenario.name,
                success=False,
                execution_time_ms=0,
                error_message=str(e)
            )
    
    async def _validate_results(self, output_data: Dict[str, Any], scenario: TestScenario) -> Dict[str, bool]:
        """Validate test results against expected output"""
        validation_results = {}
        
        # Check expected output matches
        if scenario.expected_output:
            for key, expected_value in scenario.expected_output.items():
                actual_value = self._get_nested_value(output_data, key)
                validation_results[f"expected_{key}"] = actual_value == expected_value
        
        # Apply validation rules
        for rule in scenario.validation_rules:
            validation_results[rule] = await self._apply_validation_rule(rule, output_data)
        
        return validation_results
    
    def _get_nested_value(self, data: Dict[str, Any], key_path: str) -> Any:
        """Get nested value from dictionary using dot notation"""
        keys = key_path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    async def _apply_validation_rule(self, rule: str, output_data: Dict[str, Any]) -> bool:
        """Apply validation rule to output data"""
        # Simple validation rules
        if rule == "has_response":
            return "response" in output_data
        elif rule == "response_success":
            # Check both response.success and result.success for different test types
            response_success = output_data.get("response", {}).get("success", False)
            result_success = output_data.get("result", {}).get("success", False)
            return response_success or result_success
        elif rule == "agent_healthy":
            return output_data.get("health", False)
        elif rule == "state_active":
            state = output_data.get("state", {})
            return state.get("status") == "active"
        
        # Default to True for unknown rules
        return True
    
    async def test_multi_agent_workflow(self, workflow: WorkflowDefinition, agents: Dict[str, IAgentCore]) -> Dict[str, Any]:
        """Test complete multi-agent workflows"""
        try:
            # Register all agents
            for agent_id, agent in agents.items():
                await self.mock_mcp_server.register_agent(agent_id, agent)
            
            # Execute workflow steps
            workflow_results = {
                "workflow_id": workflow.workflow_id,
                "workflow_name": workflow.name,
                "steps_executed": [],
                "success": True,
                "error": None
            }
            
            completed_steps = set()
            
            # Execute steps in dependency order
            while len(completed_steps) < len(workflow.steps):
                # Find steps that can be executed (dependencies met)
                executable_steps = [
                    step for step in workflow.steps
                    if step.step_id not in completed_steps and
                    all(dep in completed_steps for dep in step.dependencies)
                ]
                
                if not executable_steps:
                    workflow_results["success"] = False
                    workflow_results["error"] = "Circular dependency or missing steps"
                    break
                
                # Execute steps
                for step in executable_steps:
                    try:
                        agent = agents.get(step.agent_id)
                        if not agent:
                            raise Exception(f"Agent {step.agent_id} not found")
                        
                        result = await agent.execute_action(step.action, step.parameters)
                        
                        step_result = {
                            "step_id": step.step_id,
                            "agent_id": step.agent_id,
                            "action": step.action,
                            "success": result.get("success", True),
                            "result": result
                        }
                        
                        workflow_results["steps_executed"].append(step_result)
                        completed_steps.add(step.step_id)
                        
                    except Exception as e:
                        workflow_results["success"] = False
                        workflow_results["error"] = f"Step {step.step_id} failed: {str(e)}"
                        break
                
                if not workflow_results["success"]:
                    break
            
            return workflow_results
            
        except Exception as e:
            return {
                "workflow_id": workflow.workflow_id,
                "success": False,
                "error": str(e)
            }
    
    async def test_approval_workflow(self, proposal: DecisionProposal, approval_agent: IApprovalAgent) -> Dict[str, Any]:
        """Test approval workflow end-to-end"""
        try:
            # Register approval agent
            await self.mock_mcp_server.register_agent(approval_agent.agent_id, approval_agent)
            
            # Create proposal
            created_proposal = await approval_agent.create_proposal(proposal.to_dict())
            
            # Send approval request
            approval_sent = await approval_agent.send_approval_request(created_proposal)
            
            # Simulate approval response
            approval_response = await approval_agent.process_approval_response(
                proposal_id=created_proposal.proposal_id,
                approver="test_approver",
                decision="approved"
            )
            
            # Get final status
            final_status = await approval_agent.get_proposal_status(created_proposal.proposal_id)
            
            return {
                "proposal_id": created_proposal.proposal_id,
                "creation_success": created_proposal is not None,
                "approval_sent": approval_sent,
                "approval_processed": approval_response,
                "final_status": final_status,
                "success": all([
                    created_proposal is not None,
                    approval_sent,
                    approval_response,
                    final_status.get("status") == "approved"
                ])
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_agent_communication(self, sender_agent: IAgentCore, recipient_agent: IAgentCore, 
                                     message_content: Dict[str, Any]) -> Dict[str, Any]:
        """Test communication between two agents"""
        try:
            # Register both agents
            await self.mock_mcp_server.register_agent(sender_agent.agent_id, sender_agent)
            await self.mock_mcp_server.register_agent(recipient_agent.agent_id, recipient_agent)
            
            # Create test message
            message = AgentMessage(
                sender=sender_agent.agent_id,
                recipient=recipient_agent.agent_id,
                message_type=MessageType.REQUEST,
                content=message_content
            )
            
            # Send message through MCP server
            response = await self.mock_mcp_server.route_message(message)
            
            # Verify response
            return {
                "success": True,
                "message_sent": message.to_dict(),
                "response_received": response.to_dict(),
                "communication_successful": response.sender == recipient_agent.agent_id,
                "response_time_ms": 0  # Would be calculated in real implementation
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_agent_error_handling(self, agent: IAgentCore, error_scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test agent error handling capabilities"""
        results = []
        
        for scenario in error_scenarios:
            try:
                scenario_name = scenario.get("name", "unknown")
                error_type = scenario.get("error_type", "generic")
                
                # Simulate error condition
                if error_type == "invalid_message":
                    # Send malformed message
                    invalid_message = AgentMessage(
                        sender="test",
                        recipient=agent.agent_id,
                        message_type="invalid_type",
                        content=scenario.get("content", {})
                    )
                    response = await agent.process_message(invalid_message)
                    
                elif error_type == "invalid_action":
                    # Execute invalid action
                    result = await agent.execute_action("invalid_action", {})
                    
                elif error_type == "timeout":
                    # Simulate timeout (would need actual timeout implementation)
                    result = await agent.execute_action("health_check", {})
                
                results.append({
                    "scenario": scenario_name,
                    "success": True,
                    "handled_gracefully": True
                })
                
            except Exception as e:
                results.append({
                    "scenario": scenario.get("name", "unknown"),
                    "success": False,
                    "error": str(e),
                    "handled_gracefully": False
                })
        
        return {
            "total_scenarios": len(error_scenarios),
            "successful_handling": sum(1 for r in results if r["handled_gracefully"]),
            "results": results
        }
    
    async def test_agent_performance(self, agent: IAgentCore, performance_tests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test agent performance under various conditions"""
        performance_results = []
        
        for test in performance_tests:
            test_name = test.get("name", "performance_test")
            iterations = test.get("iterations", 10)
            action = test.get("action", "health_check")
            parameters = test.get("parameters", {})
            
            # Measure performance
            start_time = datetime.now()
            successful_executions = 0
            
            for i in range(iterations):
                try:
                    result = await agent.execute_action(action, parameters)
                    if result.get("success", False):
                        successful_executions += 1
                except Exception:
                    pass
            
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            
            performance_results.append({
                "test_name": test_name,
                "iterations": iterations,
                "successful_executions": successful_executions,
                "total_time_seconds": total_time,
                "average_time_per_execution": total_time / iterations,
                "success_rate": (successful_executions / iterations) * 100
            })
        
        return {
            "performance_tests": performance_results,
            "overall_success_rate": sum(r["success_rate"] for r in performance_results) / len(performance_results)
        }
    
    async def test_agent_state_management(self, agent: IAgentCore) -> Dict[str, Any]:
        """Test agent state management and transitions"""
        try:
            # Test initial state
            initial_state = await agent.get_state()
            
            # Test health check
            health_before = await agent.health_check()
            
            # Execute some actions to change state
            await agent.execute_action("health_check", {})
            
            # Test state after actions
            final_state = await agent.get_state()
            health_after = await agent.health_check()
            
            return {
                "success": True,
                "initial_state": initial_state.to_dict(),
                "final_state": final_state.to_dict(),
                "health_before": health_before,
                "health_after": health_after,
                "state_changed": initial_state.last_updated != final_state.last_updated
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_comprehensive_test_report(self, test_results: List[TestResults]) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = sum(len(results.results) for results in test_results)
        total_successful = sum(len([r for r in results.results if r.success]) for results in test_results)
        
        # Calculate performance metrics
        avg_execution_time = 0
        if total_tests > 0:
            total_execution_time = sum(
                sum(r.execution_time_ms for r in results.results) 
                for results in test_results
            )
            avg_execution_time = total_execution_time / total_tests
        
        # Identify common failure patterns
        failure_patterns = {}
        for results in test_results:
            for result in results.get_failed_tests():
                error_type = type(result.error_message).__name__ if result.error_message else "Unknown"
                failure_patterns[error_type] = failure_patterns.get(error_type, 0) + 1
        
        return {
            "summary": {
                "total_tests": total_tests,
                "successful_tests": total_successful,
                "failed_tests": total_tests - total_successful,
                "success_rate": (total_successful / total_tests * 100) if total_tests > 0 else 0,
                "average_execution_time_ms": avg_execution_time
            },
            "failure_analysis": {
                "common_failure_patterns": failure_patterns,
                "failed_test_details": [
                    {
                        "test_name": result.scenario_name,
                        "error": result.error_message,
                        "execution_time": result.execution_time_ms
                    }
                    for results in test_results
                    for result in results.get_failed_tests()
                ]
            },
            "performance_analysis": {
                "fastest_test": min(
                    (result.execution_time_ms for results in test_results for result in results.results),
                    default=0
                ),
                "slowest_test": max(
                    (result.execution_time_ms for results in test_results for result in results.results),
                    default=0
                )
            },
            "recommendations": self._generate_test_recommendations(test_results)
        }
    
    def _generate_test_recommendations(self, test_results: List[TestResults]) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Calculate overall success rate
        total_tests = sum(len(results.results) for results in test_results)
        total_successful = sum(len([r for r in results.results if r.success]) for results in test_results)
        success_rate = (total_successful / total_tests * 100) if total_tests > 0 else 0
        
        if success_rate < 90:
            recommendations.append("Consider improving error handling - success rate is below 90%")
        
        if success_rate < 70:
            recommendations.append("Critical: Success rate is below 70% - review agent implementations")
        
        # Check for performance issues
        slow_tests = [
            result for results in test_results 
            for result in results.results 
            if result.execution_time_ms > 1000
        ]
        
        if slow_tests:
            recommendations.append(f"Performance concern: {len(slow_tests)} tests took longer than 1 second")
        
        # Check for common error patterns
        error_counts = {}
        for results in test_results:
            for result in results.get_failed_tests():
                if result.error_message:
                    error_type = result.error_message.split(':')[0] if ':' in result.error_message else result.error_message
                    error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        for error_type, count in error_counts.items():
            if count > 3:
                recommendations.append(f"Recurring issue: '{error_type}' occurred {count} times")
        
        if not recommendations:
            recommendations.append("All tests passed successfully - system is performing well")
        
        return recommendations


# Convenience functions for common test scenarios
def create_message_processing_scenario(agent_id: str, message_content: Dict[str, Any]) -> TestScenario:
    """Create message processing test scenario"""
    return TestScenario(
        name=f"message_processing_{agent_id}",
        description=f"Test message processing for {agent_id}",
        input_data={
            "message": {
                "sender": "test_sender",
                "recipient": agent_id,
                "message_type": "request",
                "content": message_content,
                "timestamp": datetime.now().isoformat(),
                "correlation_id": str(uuid.uuid4())
            }
        },
        expected_output={
            "response.message_type": "response",
            "response.sender": agent_id
        },
        validation_rules=["has_response"]
    )


def create_action_execution_scenario(action: str, parameters: Dict[str, Any]) -> TestScenario:
    """Create action execution test scenario"""
    return TestScenario(
        name=f"action_{action}",
        description=f"Test {action} action execution",
        input_data={
            "action": action,
            "parameters": parameters
        },
        validation_rules=["response_success"]
    )


def create_health_check_scenario(agent_id: str) -> TestScenario:
    """Create health check test scenario"""
    return TestScenario(
        name=f"health_check_{agent_id}",
        description=f"Test health check for {agent_id}",
        validation_rules=["agent_healthy", "state_active"]
    )