"""
Workflow execution engine for multi-step processes
Handles workflow definition, execution, and state management
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
import json

from .interfaces import IWorkflowEngine, IMCPServer, IStrandsFramework
from .models import (
    WorkflowDefinition, WorkflowStep, TaskResult, WorkflowStatus,
    AgentMessage, MessageType, SystemEvent
)


class WorkflowEngine(IWorkflowEngine):
    """
    Workflow execution engine for coordinating multi-agent processes
    Supports sequential, parallel, and conditional execution patterns
    """
    
    def __init__(
        self,
        mcp_server: IMCPServer,
        strands_framework: Optional[IStrandsFramework] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.mcp_server = mcp_server
        self.strands_framework = strands_framework
        self.config = config or {}
        
        # Initialize logging
        self.logger = logging.getLogger(f"{__name__}.WorkflowEngine")
        
        # Workflow state management
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.workflow_templates: Dict[str, WorkflowDefinition] = {}
        self.execution_history: Dict[str, TaskResult] = {}
        
        # Execution control
        self.max_concurrent_workflows = self.config.get("max_concurrent_workflows", 10)
        self.default_step_timeout = self.config.get("default_step_timeout", 300)  # 5 minutes
        self.workflow_cleanup_interval = self.config.get("workflow_cleanup_interval", 3600)  # 1 hour
        
        # Performance tracking
        self.execution_metrics = {
            "workflows_executed": 0,
            "workflows_successful": 0,
            "workflows_failed": 0,
            "average_execution_time": 0.0,
            "total_steps_executed": 0
        }
        
        # Start background cleanup task
        asyncio.create_task(self._cleanup_completed_workflows())
    
    async def execute_workflow(self, workflow: WorkflowDefinition) -> TaskResult:
        """Execute workflow definition"""
        try:
            self.logger.info(f"Starting workflow execution: {workflow.workflow_id}")
            
            # Check concurrent workflow limit
            if len(self.active_workflows) >= self.max_concurrent_workflows:
                raise Exception(f"Maximum concurrent workflows ({self.max_concurrent_workflows}) reached")
            
            # Initialize workflow execution state
            execution_state = {
                "workflow": workflow,
                "status": WorkflowStatus.RUNNING,
                "start_time": datetime.now(),
                "completed_steps": set(),
                "failed_steps": set(),
                "step_results": {},
                "current_parallel_steps": set(),
                "execution_log": []
            }
            
            self.active_workflows[workflow.workflow_id] = execution_state
            
            # Create task result
            result = TaskResult(
                task_id=workflow.workflow_id,
                status="running"
            )
            
            # Store workflow context in Strands
            if self.strands_framework:
                await self.strands_framework.update_context(
                    f"workflow_{workflow.workflow_id}",
                    {
                        "workflow_definition": workflow.name,
                        "start_time": execution_state["start_time"].isoformat(),
                        "status": WorkflowStatus.RUNNING.value
                    }
                )
            
            # Execute workflow steps
            await self._execute_workflow_steps(workflow, execution_state, result)
            
            # Finalize execution
            end_time = datetime.now()
            execution_time = (end_time - execution_state["start_time"]).total_seconds()
            
            # Determine final status
            if execution_state["failed_steps"]:
                if execution_state["completed_steps"]:
                    result.status = "partial"
                    execution_state["status"] = WorkflowStatus.FAILED
                else:
                    result.status = "failed"
                    execution_state["status"] = WorkflowStatus.FAILED
            else:
                result.status = "success"
                execution_state["status"] = WorkflowStatus.COMPLETED
            
            result.execution_time_seconds = execution_time
            result.completed_at = end_time
            result.results = execution_state["step_results"]
            
            # Update metrics
            self._update_execution_metrics(result)
            
            # Store final result
            self.execution_history[workflow.workflow_id] = result
            execution_state["end_time"] = end_time
            
            # Update Strands context
            if self.strands_framework:
                await self.strands_framework.update_context(
                    f"workflow_{workflow.workflow_id}",
                    {
                        "status": execution_state["status"].value,
                        "end_time": end_time.isoformat(),
                        "execution_time_seconds": execution_time,
                        "final_result": result.status
                    }
                )
            
            self.logger.info(f"Workflow {workflow.workflow_id} completed with status: {result.status}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing workflow {workflow.workflow_id}: {e}")
            
            # Update workflow state
            if workflow.workflow_id in self.active_workflows:
                self.active_workflows[workflow.workflow_id]["status"] = WorkflowStatus.FAILED
                self.active_workflows[workflow.workflow_id]["end_time"] = datetime.now()
            
            # Create error result
            result = TaskResult(
                task_id=workflow.workflow_id,
                status="failed",
                errors=[str(e)],
                completed_at=datetime.now()
            )
            
            self.execution_history[workflow.workflow_id] = result
            return result
    
    async def pause_workflow(self, workflow_id: str) -> bool:
        """Pause running workflow"""
        try:
            if workflow_id not in self.active_workflows:
                return False
            
            execution_state = self.active_workflows[workflow_id]
            if execution_state["status"] != WorkflowStatus.RUNNING:
                return False
            
            execution_state["status"] = WorkflowStatus.PAUSED
            execution_state["paused_at"] = datetime.now()
            
            self.logger.info(f"Workflow {workflow_id} paused")
            return True
            
        except Exception as e:
            self.logger.error(f"Error pausing workflow {workflow_id}: {e}")
            return False
    
    async def resume_workflow(self, workflow_id: str) -> bool:
        """Resume paused workflow"""
        try:
            if workflow_id not in self.active_workflows:
                return False
            
            execution_state = self.active_workflows[workflow_id]
            if execution_state["status"] != WorkflowStatus.PAUSED:
                return False
            
            execution_state["status"] = WorkflowStatus.RUNNING
            execution_state["resumed_at"] = datetime.now()
            
            # Continue execution
            workflow = execution_state["workflow"]
            result = TaskResult(task_id=workflow_id, status="running")
            
            asyncio.create_task(self._execute_workflow_steps(workflow, execution_state, result))
            
            self.logger.info(f"Workflow {workflow_id} resumed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error resuming workflow {workflow_id}: {e}")
            return False
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel running workflow"""
        try:
            if workflow_id not in self.active_workflows:
                return False
            
            execution_state = self.active_workflows[workflow_id]
            execution_state["status"] = WorkflowStatus.CANCELLED
            execution_state["cancelled_at"] = datetime.now()
            
            # Create cancelled result
            result = TaskResult(
                task_id=workflow_id,
                status="cancelled",
                completed_at=datetime.now()
            )
            
            self.execution_history[workflow_id] = result
            
            self.logger.info(f"Workflow {workflow_id} cancelled")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cancelling workflow {workflow_id}: {e}")
            return False
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get status of workflow execution"""
        try:
            if workflow_id in self.active_workflows:
                execution_state = self.active_workflows[workflow_id]
                workflow = execution_state["workflow"]
                
                return {
                    "workflow_id": workflow_id,
                    "name": workflow.name,
                    "status": execution_state["status"].value,
                    "start_time": execution_state["start_time"].isoformat(),
                    "completed_steps": len(execution_state["completed_steps"]),
                    "total_steps": len(workflow.steps),
                    "failed_steps": len(execution_state["failed_steps"]),
                    "current_parallel_steps": len(execution_state["current_parallel_steps"]),
                    "execution_log": execution_state["execution_log"][-10:]  # Last 10 entries
                }
            
            elif workflow_id in self.execution_history:
                result = self.execution_history[workflow_id]
                return {
                    "workflow_id": workflow_id,
                    "status": "completed",
                    "final_status": result.status,
                    "execution_time_seconds": result.execution_time_seconds,
                    "completed_at": result.completed_at.isoformat(),
                    "has_errors": result.has_errors(),
                    "error_count": len(result.errors)
                }
            
            else:
                return {"error": f"Workflow {workflow_id} not found"}
                
        except Exception as e:
            self.logger.error(f"Error getting workflow status: {e}")
            return {"error": str(e)}
    
    async def get_active_workflows(self) -> List[Dict[str, Any]]:
        """Get all active workflows"""
        try:
            active_workflows = []
            
            for workflow_id, execution_state in self.active_workflows.items():
                workflow = execution_state["workflow"]
                
                active_workflows.append({
                    "workflow_id": workflow_id,
                    "name": workflow.name,
                    "status": execution_state["status"].value,
                    "start_time": execution_state["start_time"].isoformat(),
                    "progress": {
                        "completed_steps": len(execution_state["completed_steps"]),
                        "total_steps": len(workflow.steps),
                        "progress_percentage": (len(execution_state["completed_steps"]) / len(workflow.steps)) * 100
                    }
                })
            
            return active_workflows
            
        except Exception as e:
            self.logger.error(f"Error getting active workflows: {e}")
            return []
    
    async def register_workflow_template(self, template: WorkflowDefinition) -> bool:
        """Register workflow template for reuse"""
        try:
            self.workflow_templates[template.workflow_id] = template
            
            self.logger.info(f"Registered workflow template: {template.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering workflow template: {e}")
            return False
    
    async def _execute_workflow_steps(
        self,
        workflow: WorkflowDefinition,
        execution_state: Dict[str, Any],
        result: TaskResult
    ) -> None:
        """Execute workflow steps with proper dependency handling"""
        try:
            while execution_state["status"] == WorkflowStatus.RUNNING:
                # Get next executable steps
                next_steps = self._get_next_executable_steps(workflow, execution_state)
                
                if not next_steps:
                    # No more steps to execute
                    break
                
                # Execute steps (parallel or sequential based on dependencies)
                await self._execute_step_batch(next_steps, execution_state, result)
                
                # Check for workflow timeout
                if self._is_workflow_timed_out(workflow, execution_state):
                    result.errors.append("Workflow execution timed out")
                    execution_state["status"] = WorkflowStatus.FAILED
                    break
                
                # Brief pause to allow for system responsiveness
                await asyncio.sleep(0.1)
                
        except Exception as e:
            self.logger.error(f"Error in workflow step execution: {e}")
            result.errors.append(str(e))
            execution_state["status"] = WorkflowStatus.FAILED
    
    def _get_next_executable_steps(
        self,
        workflow: WorkflowDefinition,
        execution_state: Dict[str, Any]
    ) -> List[WorkflowStep]:
        """Get steps that can be executed next"""
        completed_steps = execution_state["completed_steps"]
        failed_steps = execution_state["failed_steps"]
        current_parallel_steps = execution_state["current_parallel_steps"]
        
        executable_steps = []
        
        for step in workflow.steps:
            # Skip if already completed, failed, or currently executing
            if (step.step_id in completed_steps or 
                step.step_id in failed_steps or 
                step.step_id in current_parallel_steps):
                continue
            
            # Check if all dependencies are satisfied
            if step.can_execute(list(completed_steps)):
                executable_steps.append(step)
        
        return executable_steps
    
    async def _execute_step_batch(
        self,
        steps: List[WorkflowStep],
        execution_state: Dict[str, Any],
        result: TaskResult
    ) -> None:
        """Execute a batch of steps (potentially in parallel)"""
        if not steps:
            return
        
        # Add steps to current parallel execution set
        for step in steps:
            execution_state["current_parallel_steps"].add(step.step_id)
        
        # Execute steps concurrently
        step_tasks = []
        for step in steps:
            task = asyncio.create_task(self._execute_single_step(step, execution_state, result))
            step_tasks.append(task)
        
        # Wait for all steps to complete
        await asyncio.gather(*step_tasks, return_exceptions=True)
        
        # Remove steps from parallel execution set
        for step in steps:
            execution_state["current_parallel_steps"].discard(step.step_id)
    
    async def _execute_single_step(
        self,
        step: WorkflowStep,
        execution_state: Dict[str, Any],
        result: TaskResult
    ) -> None:
        """Execute a single workflow step"""
        try:
            self.logger.info(f"Executing step {step.step_id} on agent {step.agent_id}")
            
            # Log step execution
            execution_state["execution_log"].append({
                "step_id": step.step_id,
                "agent_id": step.agent_id,
                "action": step.action,
                "status": "started",
                "timestamp": datetime.now().isoformat()
            })
            
            # Create message for step execution
            message = AgentMessage(
                sender="workflow_engine",
                recipient=step.agent_id,
                message_type=MessageType.COMMAND,
                content={
                    "command": step.action,
                    "parameters": step.parameters,
                    "workflow_id": execution_state["workflow"].workflow_id,
                    "step_id": step.step_id
                },
                requires_response=True,
                response_timeout=step.timeout_seconds
            )
            
            # Execute step through MCP server
            start_time = datetime.now()
            response = await self.mcp_server.route_message(message)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Process response
            if response.message_type == MessageType.ERROR:
                error_msg = response.content.get("error", "Unknown error")
                self.logger.error(f"Step {step.step_id} failed: {error_msg}")
                
                execution_state["failed_steps"].add(step.step_id)
                result.errors.append(f"Step {step.step_id}: {error_msg}")
                
                # Log failure
                execution_state["execution_log"].append({
                    "step_id": step.step_id,
                    "status": "failed",
                    "error": error_msg,
                    "execution_time_seconds": execution_time,
                    "timestamp": datetime.now().isoformat()
                })
                
            else:
                self.logger.info(f"Step {step.step_id} completed successfully")
                
                execution_state["completed_steps"].add(step.step_id)
                execution_state["step_results"][step.step_id] = response.content
                result.agent_results[step.agent_id] = response.content
                
                # Log success
                execution_state["execution_log"].append({
                    "step_id": step.step_id,
                    "status": "completed",
                    "execution_time_seconds": execution_time,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Update metrics
            self.execution_metrics["total_steps_executed"] += 1
            
        except asyncio.TimeoutError:
            self.logger.error(f"Step {step.step_id} timed out")
            execution_state["failed_steps"].add(step.step_id)
            result.errors.append(f"Step {step.step_id} timed out after {step.timeout_seconds} seconds")
            
        except Exception as e:
            self.logger.error(f"Error executing step {step.step_id}: {e}")
            execution_state["failed_steps"].add(step.step_id)
            result.errors.append(f"Step {step.step_id}: {str(e)}")
    
    def _is_workflow_timed_out(
        self,
        workflow: WorkflowDefinition,
        execution_state: Dict[str, Any]
    ) -> bool:
        """Check if workflow has timed out"""
        start_time = execution_state["start_time"]
        timeout_minutes = workflow.timeout_minutes
        
        if timeout_minutes <= 0:
            return False
        
        elapsed_time = datetime.now() - start_time
        return elapsed_time > timedelta(minutes=timeout_minutes)
    
    def _update_execution_metrics(self, result: TaskResult) -> None:
        """Update workflow execution metrics"""
        self.execution_metrics["workflows_executed"] += 1
        
        if result.is_successful():
            self.execution_metrics["workflows_successful"] += 1
        else:
            self.execution_metrics["workflows_failed"] += 1
        
        # Update average execution time
        current_avg = self.execution_metrics["average_execution_time"]
        total_workflows = self.execution_metrics["workflows_executed"]
        
        new_avg = ((current_avg * (total_workflows - 1)) + result.execution_time_seconds) / total_workflows
        self.execution_metrics["average_execution_time"] = new_avg
    
    async def _cleanup_completed_workflows(self) -> None:
        """Background task to clean up completed workflows"""
        while True:
            try:
                await asyncio.sleep(self.workflow_cleanup_interval)
                
                current_time = datetime.now()
                workflows_to_remove = []
                
                for workflow_id, execution_state in self.active_workflows.items():
                    # Remove workflows that completed more than 1 hour ago
                    if execution_state["status"] in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]:
                        end_time = execution_state.get("end_time", current_time)
                        if (current_time - end_time).total_seconds() > 3600:  # 1 hour
                            workflows_to_remove.append(workflow_id)
                
                for workflow_id in workflows_to_remove:
                    del self.active_workflows[workflow_id]
                    self.logger.debug(f"Cleaned up completed workflow: {workflow_id}")
                
            except Exception as e:
                self.logger.error(f"Error in workflow cleanup: {e}")
    
    def get_execution_metrics(self) -> Dict[str, Any]:
        """Get workflow execution metrics"""
        return {
            **self.execution_metrics,
            "active_workflows": len(self.active_workflows),
            "workflow_templates": len(self.workflow_templates),
            "success_rate": (
                (self.execution_metrics["workflows_successful"] / 
                 max(self.execution_metrics["workflows_executed"], 1)) * 100
            )
        }