"""
Comprehensive test runner for the entire agentic AI system
Executes all agent tests and generates detailed reports
"""

import pytest
import asyncio
import sys
import time
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

from tests.framework.agent_test_framework import AgentTestFramework, TestResults
from tests.unit.test_comprehensive_agent_framework import TestComprehensiveAgentFramework
from tests.unit.test_mcp_server_integration import TestMCPServerIntegration
from tests.unit.test_strands_framework_integration import TestStrandsFrameworkIntegration


class ComprehensiveTestRunner:
    """Comprehensive test runner for the agentic AI system"""
    
    def __init__(self):
        self.test_framework = AgentTestFramework()
        self.test_results = []
        self.start_time = None
        self.end_time = None
        self.test_summary = {}
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all comprehensive tests and generate report"""
        self.start_time = datetime.now()
        print(f"Starting comprehensive agentic AI system tests at {self.start_time}")
        
        # Test categories to run
        test_categories = [
            ("Core Agent Framework", self._run_core_agent_tests),
            ("MCP Server Integration", self._run_mcp_server_tests),
            ("Strands Framework Integration", self._run_strands_framework_tests),
            ("System Integration", self._run_system_integration_tests),
            ("Performance Tests", self._run_performance_tests),
            ("Error Handling Tests", self._run_error_handling_tests)
        ]
        
        category_results = {}
        
        for category_name, test_function in test_categories:
            print(f"\n{'='*60}")
            print(f"Running {category_name} Tests")
            print(f"{'='*60}")
            
            try:
                category_result = await test_function()
                category_results[category_name] = category_result
                
                success_rate = category_result.get("success_rate", 0)
                total_tests = category_result.get("total_tests", 0)
                
                print(f"✓ {category_name}: {success_rate:.1f}% success rate ({total_tests} tests)")
                
            except Exception as e:
                print(f"✗ {category_name}: Failed with error: {e}")
                category_results[category_name] = {
                    "success_rate": 0,
                    "total_tests": 0,
                    "error": str(e)
                }
        
        self.end_time = datetime.now()
        
        # Generate comprehensive report
        comprehensive_report = self._generate_comprehensive_report(category_results)
        
        # Print summary
        self._print_test_summary(comprehensive_report)
        
        return comprehensive_report
    
    async def _run_core_agent_tests(self) -> Dict[str, Any]:
        """Run core agent framework tests"""
        from tests.unit.test_comprehensive_agent_framework import TestAgentCore
        
        # Create test agent
        test_agent = TestAgentCore()
        await test_agent.initialize()
        
        # Run basic functionality tests
        from tests.framework.agent_test_framework import (
            create_health_check_scenario, create_action_execution_scenario,
            create_message_processing_scenario
        )
        
        scenarios = [
            create_health_check_scenario(test_agent.agent_id),
            create_action_execution_scenario("test_action", {"test_param": "core_test"}),
            create_action_execution_scenario("complex_action", {"complexity": 2}),
            create_message_processing_scenario(test_agent.agent_id, {"action": "test_action"})
        ]
        
        results = await self.test_framework.test_agent_behavior(test_agent, scenarios)
        
        # Test agent communication
        agent2 = TestAgentCore("agent2")
        await agent2.initialize()
        
        comm_result = await self.test_framework.test_agent_communication(
            test_agent, agent2, {"test": "communication"}
        )
        
        # Test error handling
        error_scenarios = [
            {"name": "invalid_action", "error_type": "invalid_action"},
            {"name": "malformed_message", "error_type": "invalid_message"}
        ]
        
        error_result = await self.test_framework.test_agent_error_handling(test_agent, error_scenarios)
        
        # Test performance
        perf_tests = [
            {"name": "basic_performance", "action": "test_action", "iterations": 20},
            {"name": "complex_performance", "action": "complex_action", "iterations": 10}
        ]
        
        perf_result = await self.test_framework.test_agent_performance(test_agent, perf_tests)
        
        return {
            "success_rate": results.get_success_rate(),
            "total_tests": len(results.results),
            "communication_success": comm_result["success"],
            "error_handling_success": error_result["successful_handling"] / error_result["total_scenarios"] * 100,
            "performance_success": perf_result["overall_success_rate"],
            "details": {
                "behavior_tests": results,
                "communication_test": comm_result,
                "error_handling_test": error_result,
                "performance_test": perf_result
            }
        }
    
    async def _run_mcp_server_tests(self) -> Dict[str, Any]:
        """Run MCP server integration tests"""
        from tests.unit.test_mcp_server_integration import MockTestAgent
        
        # Create mock agents
        agents = {
            "mcp_agent1": MockTestAgent("mcp_agent1", "cost_management"),
            "mcp_agent2": MockTestAgent("mcp_agent2", "resource_management"),
            "mcp_agent3": MockTestAgent("mcp_agent3", "forecasting")
        }
        
        # Initialize agents
        for agent in agents.values():
            await agent.initialize()
        
        # Create mock MCP server
        from tests.framework.agent_test_framework import MockMCPServer
        mcp_server = MockMCPServer()
        
        # Register agents
        for agent_id, agent in agents.items():
            await mcp_server.register_agent(agent_id, agent)
        
        test_results = []
        
        # Test message routing
        from src.agentic.core.models import AgentMessage, MessageType
        
        message = AgentMessage(
            sender="mcp_agent1",
            recipient="mcp_agent2",
            message_type=MessageType.REQUEST,
            content={"test": "mcp_routing"}
        )
        
        response = await mcp_server.route_message(message)
        routing_success = response.sender == "mcp_agent2"
        test_results.append(routing_success)
        
        # Test system event broadcasting
        from src.agentic.core.models import SystemEvent
        
        event = SystemEvent(
            event_type="test_event",
            source="test_runner",
            data={"test": "broadcast"},
            severity="info"
        )
        
        responses = await mcp_server.broadcast_system_event(event)
        broadcast_success = len(responses) == 3
        test_results.append(broadcast_success)
        
        # Test concurrent message routing
        concurrent_messages = [
            AgentMessage(
                sender="mcp_agent1",
                recipient="mcp_agent2",
                message_type=MessageType.REQUEST,
                content={"concurrent_test": i}
            )
            for i in range(5)
        ]
        
        concurrent_responses = await asyncio.gather(
            *[mcp_server.route_message(msg) for msg in concurrent_messages]
        )
        
        concurrent_success = len(concurrent_responses) == 5
        test_results.append(concurrent_success)
        
        success_rate = (sum(test_results) / len(test_results)) * 100
        
        return {
            "success_rate": success_rate,
            "total_tests": len(test_results),
            "routing_success": routing_success,
            "broadcast_success": broadcast_success,
            "concurrent_success": concurrent_success
        }
    
    async def _run_strands_framework_tests(self) -> Dict[str, Any]:
        """Run Strands framework integration tests"""
        from tests.unit.test_strands_framework_integration import MockStrandsFramework
        
        strands = MockStrandsFramework()
        await strands.initialize({})
        
        test_results = []
        
        # Test context management
        context_success = await strands.update_context("test_agent", {"test": "context"})
        shared_context = await strands.get_shared_context(["test"])
        context_test_success = context_success and shared_context.get("test") == "context"
        test_results.append(context_test_success)
        
        # Test conversation management
        thread_id = await strands.create_conversation_thread(["agent1", "agent2"])
        
        from tests.framework.agent_test_framework import TestDataGenerator
        from src.agentic.core.models import MessageType
        
        generator = TestDataGenerator()
        message = generator.create_test_message("agent1", "agent2", MessageType.REQUEST, {"test": "conversation"})
        
        store_success = await strands.store_conversation_message(thread_id, message)
        history = await strands.get_conversation_history(thread_id)
        conversation_test_success = store_success and len(history) == 1
        test_results.append(conversation_test_success)
        
        # Test decision management
        proposal = generator.create_test_proposal("Strands Test", 1000.0, "medium")
        decision_success = await strands.store_decision_history(proposal)
        decision_context = await strands.get_decision_context(proposal.proposal_id)
        decision_test_success = decision_success and decision_context is not None
        test_results.append(decision_test_success)
        
        success_rate = (sum(test_results) / len(test_results)) * 100
        
        return {
            "success_rate": success_rate,
            "total_tests": len(test_results),
            "context_management": context_test_success,
            "conversation_management": conversation_test_success,
            "decision_management": decision_test_success
        }
    
    async def _run_system_integration_tests(self) -> Dict[str, Any]:
        """Run system integration tests"""
        from tests.unit.test_comprehensive_agent_framework import TestAgentCore
        from src.agentic.core.models import WorkflowDefinition, WorkflowStep
        
        # Create agents for integration test
        agents = {
            "integration_agent1": TestAgentCore("integration_agent1"),
            "integration_agent2": TestAgentCore("integration_agent2")
        }
        
        for agent in agents.values():
            await agent.initialize()
        
        # Test multi-agent workflow
        workflow = WorkflowDefinition(
            name="Integration Test Workflow",
            steps=[
                WorkflowStep(
                    step_id="step1",
                    agent_id="integration_agent1",
                    action="test_action",
                    parameters={"test_param": "integration_step1"}
                ),
                WorkflowStep(
                    step_id="step2",
                    agent_id="integration_agent2",
                    action="test_action",
                    parameters={"test_param": "integration_step2"},
                    dependencies=["step1"]
                )
            ]
        )
        
        workflow_result = await self.test_framework.test_multi_agent_workflow(workflow, agents)
        
        # Test system state management
        state_results = []
        for agent in agents.values():
            state_result = await self.test_framework.test_agent_state_management(agent)
            state_results.append(state_result["success"])
        
        state_success_rate = (sum(state_results) / len(state_results)) * 100
        
        return {
            "success_rate": (workflow_result["success"] + state_success_rate) / 2,
            "total_tests": 3,  # workflow + 2 state tests
            "workflow_success": workflow_result["success"],
            "state_management_success": state_success_rate,
            "workflow_details": workflow_result
        }
    
    async def _run_performance_tests(self) -> Dict[str, Any]:
        """Run performance tests"""
        from tests.unit.test_comprehensive_agent_framework import TestAgentCore
        
        # Create agent for performance testing
        perf_agent = TestAgentCore("performance_agent")
        await perf_agent.initialize()
        
        # High-load performance tests
        performance_tests = [
            {
                "name": "high_frequency_actions",
                "action": "test_action",
                "parameters": {"test_param": "performance"},
                "iterations": 100
            },
            {
                "name": "complex_action_load",
                "action": "complex_action",
                "parameters": {"complexity": 5},
                "iterations": 50
            },
            {
                "name": "health_check_frequency",
                "action": "health_check",
                "parameters": {},
                "iterations": 200
            }
        ]
        
        perf_result = await self.test_framework.test_agent_performance(perf_agent, performance_tests)
        
        # Concurrent agent performance
        concurrent_agents = [TestAgentCore(f"concurrent_perf_agent_{i}") for i in range(10)]
        
        # Initialize all agents concurrently
        await asyncio.gather(*[agent.initialize() for agent in concurrent_agents])
        
        # Run concurrent operations
        concurrent_tasks = []
        for agent in concurrent_agents:
            task = agent.execute_action("test_action", {"concurrent": True})
            concurrent_tasks.append(task)
        
        start_time = time.time()
        concurrent_results = await asyncio.gather(*concurrent_tasks)
        end_time = time.time()
        
        concurrent_success = all(result.get("success", False) for result in concurrent_results)
        concurrent_time = end_time - start_time
        
        return {
            "success_rate": perf_result["overall_success_rate"],
            "total_tests": len(performance_tests) + 1,  # +1 for concurrent test
            "individual_performance": perf_result,
            "concurrent_success": concurrent_success,
            "concurrent_time_seconds": concurrent_time,
            "concurrent_agents": len(concurrent_agents)
        }
    
    async def _run_error_handling_tests(self) -> Dict[str, Any]:
        """Run error handling and resilience tests"""
        from tests.unit.test_comprehensive_agent_framework import TestAgentCore
        
        # Create agents for error testing
        normal_agent = TestAgentCore("normal_agent")
        failing_agent = TestAgentCore("failing_agent", fail_health_check=True)
        
        await normal_agent.initialize()
        await failing_agent.initialize()
        
        # Test error scenarios
        error_scenarios = [
            {"name": "invalid_action", "error_type": "invalid_action"},
            {"name": "invalid_message", "error_type": "invalid_message"},
            {"name": "timeout_simulation", "error_type": "timeout"},
            {"name": "malformed_parameters", "error_type": "invalid_action"}
        ]
        
        # Test normal agent error handling
        normal_error_result = await self.test_framework.test_agent_error_handling(normal_agent, error_scenarios)
        
        # Test failing agent behavior
        failing_scenarios = [
            {"name": "health_check_failure", "error_type": "health_check"}
        ]
        
        failing_error_result = await self.test_framework.test_agent_error_handling(failing_agent, failing_scenarios)
        
        # Test recovery scenarios
        recovery_tests = []
        
        # Simulate agent recovery
        failing_agent.fail_health_check = False  # "Fix" the agent
        recovery_health = await failing_agent.health_check()
        recovery_tests.append(recovery_health)
        
        # Test system resilience with multiple failing agents
        mixed_agents = [normal_agent, failing_agent]
        resilience_results = []
        
        for agent in mixed_agents:
            try:
                result = await agent.execute_action("health_check", {})
                resilience_results.append(result.get("success", False))
            except Exception:
                resilience_results.append(False)
        
        system_resilience = sum(resilience_results) / len(resilience_results) * 100
        
        overall_error_handling = (
            normal_error_result["successful_handling"] / normal_error_result["total_scenarios"] * 100 +
            system_resilience
        ) / 2
        
        return {
            "success_rate": overall_error_handling,
            "total_tests": len(error_scenarios) + len(failing_scenarios) + len(recovery_tests) + len(resilience_results),
            "normal_agent_error_handling": normal_error_result,
            "failing_agent_behavior": failing_error_result,
            "recovery_success": sum(recovery_tests) / len(recovery_tests) * 100 if recovery_tests else 0,
            "system_resilience": system_resilience
        }
    
    def _generate_comprehensive_report(self, category_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_duration = (self.end_time - self.start_time).total_seconds()
        
        # Calculate overall metrics
        total_tests = sum(result.get("total_tests", 0) for result in category_results.values())
        overall_success_rate = sum(
            result.get("success_rate", 0) for result in category_results.values()
        ) / len(category_results) if category_results else 0
        
        # Identify problem areas
        problem_areas = []
        for category, result in category_results.items():
            if result.get("success_rate", 0) < 90:
                problem_areas.append({
                    "category": category,
                    "success_rate": result.get("success_rate", 0),
                    "issues": result.get("error", "Low success rate")
                })
        
        # Generate recommendations
        recommendations = self._generate_recommendations(category_results, overall_success_rate)
        
        return {
            "test_execution": {
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
                "duration_seconds": total_duration,
                "categories_tested": len(category_results)
            },
            "overall_metrics": {
                "total_tests": total_tests,
                "overall_success_rate": overall_success_rate,
                "categories_passed": len([r for r in category_results.values() if r.get("success_rate", 0) >= 90]),
                "categories_failed": len([r for r in category_results.values() if r.get("success_rate", 0) < 90])
            },
            "category_results": category_results,
            "problem_areas": problem_areas,
            "recommendations": recommendations,
            "system_health_assessment": self._assess_system_health(overall_success_rate, problem_areas)
        }
    
    def _generate_recommendations(self, category_results: Dict[str, Any], overall_success_rate: float) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        if overall_success_rate >= 95:
            recommendations.append("✓ Excellent: System is performing exceptionally well across all categories")
        elif overall_success_rate >= 90:
            recommendations.append("✓ Good: System is performing well with minor areas for improvement")
        elif overall_success_rate >= 80:
            recommendations.append("⚠ Warning: System has some performance issues that should be addressed")
        else:
            recommendations.append("✗ Critical: System has significant issues requiring immediate attention")
        
        # Category-specific recommendations
        for category, result in category_results.items():
            success_rate = result.get("success_rate", 0)
            
            if success_rate < 80:
                recommendations.append(f"• {category}: Requires immediate attention (success rate: {success_rate:.1f}%)")
            elif success_rate < 90:
                recommendations.append(f"• {category}: Consider optimization (success rate: {success_rate:.1f}%)")
        
        # Performance recommendations
        perf_result = category_results.get("Performance Tests", {})
        if perf_result.get("concurrent_time_seconds", 0) > 5:
            recommendations.append("• Consider optimizing concurrent operation performance")
        
        # Error handling recommendations
        error_result = category_results.get("Error Handling Tests", {})
        if error_result.get("success_rate", 0) < 85:
            recommendations.append("• Improve error handling and recovery mechanisms")
        
        return recommendations
    
    def _assess_system_health(self, overall_success_rate: float, problem_areas: List[Dict]) -> str:
        """Assess overall system health"""
        if overall_success_rate >= 95 and not problem_areas:
            return "EXCELLENT - System is ready for production"
        elif overall_success_rate >= 90 and len(problem_areas) <= 1:
            return "GOOD - System is stable with minor issues"
        elif overall_success_rate >= 80:
            return "FAIR - System needs improvement before production"
        elif overall_success_rate >= 70:
            return "POOR - System has significant issues"
        else:
            return "CRITICAL - System requires major fixes"
    
    def _print_test_summary(self, report: Dict[str, Any]):
        """Print comprehensive test summary"""
        print(f"\n{'='*80}")
        print("COMPREHENSIVE AGENTIC AI SYSTEM TEST REPORT")
        print(f"{'='*80}")
        
        # Execution summary
        execution = report["test_execution"]
        print(f"Execution Time: {execution['duration_seconds']:.2f} seconds")
        print(f"Categories Tested: {execution['categories_tested']}")
        
        # Overall metrics
        metrics = report["overall_metrics"]
        print(f"\nOverall Results:")
        print(f"  Total Tests: {metrics['total_tests']}")
        print(f"  Success Rate: {metrics['overall_success_rate']:.1f}%")
        print(f"  Categories Passed: {metrics['categories_passed']}/{execution['categories_tested']}")
        
        # Category breakdown
        print(f"\nCategory Breakdown:")
        for category, result in report["category_results"].items():
            success_rate = result.get("success_rate", 0)
            total_tests = result.get("total_tests", 0)
            status = "✓" if success_rate >= 90 else "⚠" if success_rate >= 80 else "✗"
            print(f"  {status} {category}: {success_rate:.1f}% ({total_tests} tests)")
        
        # Problem areas
        if report["problem_areas"]:
            print(f"\nProblem Areas:")
            for problem in report["problem_areas"]:
                print(f"  ✗ {problem['category']}: {problem['success_rate']:.1f}% - {problem['issues']}")
        
        # Recommendations
        print(f"\nRecommendations:")
        for rec in report["recommendations"]:
            print(f"  {rec}")
        
        # System health assessment
        print(f"\nSystem Health Assessment: {report['system_health_assessment']}")
        
        print(f"{'='*80}")


async def run_comprehensive_tests():
    """Main function to run comprehensive tests"""
    runner = ComprehensiveTestRunner()
    
    try:
        report = await runner.run_all_tests()
        
        # Save report to file
        import json
        report_file = Path("test_reports") / f"comprehensive_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_file.parent.mkdir(exist_ok=True)
        
        # Convert datetime objects to strings for JSON serialization
        json_report = json.loads(json.dumps(report, default=str))
        
        with open(report_file, 'w') as f:
            json.dump(json_report, f, indent=2)
        
        print(f"\nDetailed report saved to: {report_file}")
        
        return report
        
    except Exception as e:
        print(f"Error running comprehensive tests: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Run comprehensive tests
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    report = asyncio.run(run_comprehensive_tests())
    
    if report:
        overall_success = report["overall_metrics"]["overall_success_rate"]
        sys.exit(0 if overall_success >= 80 else 1)
    else:
        sys.exit(1)