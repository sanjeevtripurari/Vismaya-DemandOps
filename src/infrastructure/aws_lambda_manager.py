"""
AWS Lambda Manager for Agentic AI System
Manages Lambda functions for serverless agent execution
"""

import json
import logging
import boto3
import zipfile
import os
import tempfile
from typing import Dict, List, Optional, Any
from datetime import datetime
import base64

# from ..core.interfaces import IAgentCore  # Not needed for Lambda manager
from .aws_session_factory import AWSSessionFactory

logger = logging.getLogger(__name__)


class AWSLambdaManager:
    """
    Manages AWS Lambda functions for serverless agent execution
    Handles deployment, invocation, and monitoring of agent Lambda functions
    """
    
    def __init__(self, aws_session_factory: AWSSessionFactory, config: Dict[str, Any]):
        self.session_factory = aws_session_factory
        self.config = config
        self.session = None
        self.lambda_client = None
        self.cloudwatch_client = None
        self.iam_client = None
        
        # Lambda configuration
        self.function_prefix = config.get("lambda_prefix", "vismaya-agent")
        self.runtime = config.get("runtime", "python3.11")
        self.timeout = config.get("timeout", 300)  # 5 minutes
        self.memory_size = config.get("memory_size", 512)  # MB
        self.environment_variables = config.get("environment_variables", {})
        
        # Agent function configurations
        self.agent_configs = {
            "orchestrator": {
                "memory_size": 1024,
                "timeout": 900,  # 15 minutes
                "environment": {"AGENT_TYPE": "orchestrator"}
            },
            "cost_management": {
                "memory_size": 512,
                "timeout": 300,
                "environment": {"AGENT_TYPE": "cost_management"}
            },
            "resource_management": {
                "memory_size": 512,
                "timeout": 300,
                "environment": {"AGENT_TYPE": "resource_management"}
            },
            "forecasting": {
                "memory_size": 1024,
                "timeout": 600,  # 10 minutes for ML operations
                "environment": {"AGENT_TYPE": "forecasting"}
            },
            "alert_management": {
                "memory_size": 256,
                "timeout": 180,
                "environment": {"AGENT_TYPE": "alert_management"}
            },
            "user_interface": {
                "memory_size": 512,
                "timeout": 300,
                "environment": {"AGENT_TYPE": "user_interface"}
            },
            "approval": {
                "memory_size": 256,
                "timeout": 300,
                "environment": {"AGENT_TYPE": "approval"}
            }
        }
        
        self._initialize_clients()
    
    def _initialize_clients(self) -> None:
        """Initialize AWS clients"""
        try:
            self.session = self.session_factory.get_session()
            self.lambda_client = self.session.client('lambda')
            self.cloudwatch_client = self.session.client('cloudwatch')
            self.iam_client = self.session.client('iam')
            logger.info("AWS Lambda clients initialized")
        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {e}")
            raise
    
    async def deploy_agent_functions(self) -> Dict[str, bool]:
        """Deploy Lambda functions for all agent types"""
        results = {}
        
        for agent_type, agent_config in self.agent_configs.items():
            try:
                function_name = f"{self.function_prefix}-{agent_type}"
                
                # Create deployment package
                deployment_package = await self._create_deployment_package(agent_type)
                
                # Deploy function
                success = await self._deploy_function(
                    function_name=function_name,
                    agent_type=agent_type,
                    deployment_package=deployment_package,
                    config=agent_config
                )
                
                results[agent_type] = success
                
                if success:
                    logger.info(f"Successfully deployed Lambda function for {agent_type}")
                else:
                    logger.error(f"Failed to deploy Lambda function for {agent_type}")
                    
            except Exception as e:
                logger.error(f"Error deploying {agent_type} agent function: {e}")
                results[agent_type] = False
        
        return results
    
    async def invoke_agent_function(
        self, 
        agent_type: str, 
        payload: Dict[str, Any],
        invocation_type: str = "RequestResponse"
    ) -> Dict[str, Any]:
        """Invoke agent Lambda function"""
        try:
            function_name = f"{self.function_prefix}-{agent_type}"
            
            # Prepare payload
            lambda_payload = {
                "agent_type": agent_type,
                "action": payload.get("action", "process_message"),
                "parameters": payload.get("parameters", {}),
                "timestamp": datetime.now().isoformat(),
                "correlation_id": payload.get("correlation_id")
            }
            
            # Invoke function
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType=invocation_type,
                Payload=json.dumps(lambda_payload)
            )
            
            # Process response
            if invocation_type == "RequestResponse":
                response_payload = json.loads(response['Payload'].read())
                
                # Check for errors
                if response.get('FunctionError'):
                    logger.error(f"Lambda function error for {agent_type}: {response_payload}")
                    return {
                        "success": False,
                        "error": response_payload.get("errorMessage", "Unknown error"),
                        "error_type": response_payload.get("errorType", "Unknown")
                    }
                
                return {
                    "success": True,
                    "result": response_payload,
                    "execution_duration": response.get('ExecutionDuration', 0),
                    "billed_duration": response.get('BilledDuration', 0),
                    "memory_used": response.get('MemoryUsed', 0)
                }
            else:
                # Asynchronous invocation
                return {
                    "success": True,
                    "invocation_type": "async",
                    "status_code": response['StatusCode']
                }
                
        except Exception as e:
            logger.error(f"Error invoking {agent_type} agent function: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_function_metrics(self, agent_type: str, hours: int = 24) -> Dict[str, Any]:
        """Get CloudWatch metrics for agent Lambda function"""
        try:
            function_name = f"{self.function_prefix}-{agent_type}"
            
            # Define time range
            end_time = datetime.now()
            start_time = datetime.now().replace(hour=end_time.hour - hours)
            
            # Get metrics
            metrics = {}
            
            # Invocation count
            invocations = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Invocations',
                Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour periods
                Statistics=['Sum']
            )
            
            # Duration
            duration = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Duration',
                Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average', 'Maximum']
            )
            
            # Errors
            errors = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Errors',
                Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            # Throttles
            throttles = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Throttles',
                Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            metrics = {
                "function_name": function_name,
                "time_range_hours": hours,
                "invocations": {
                    "total": sum(point['Sum'] for point in invocations['Datapoints']),
                    "datapoints": invocations['Datapoints']
                },
                "duration": {
                    "average_ms": sum(point['Average'] for point in duration['Datapoints']) / max(len(duration['Datapoints']), 1),
                    "max_ms": max((point['Maximum'] for point in duration['Datapoints']), default=0),
                    "datapoints": duration['Datapoints']
                },
                "errors": {
                    "total": sum(point['Sum'] for point in errors['Datapoints']),
                    "datapoints": errors['Datapoints']
                },
                "throttles": {
                    "total": sum(point['Sum'] for point in throttles['Datapoints']),
                    "datapoints": throttles['Datapoints']
                }
            }
            
            # Calculate success rate
            total_invocations = metrics["invocations"]["total"]
            total_errors = metrics["errors"]["total"]
            
            if total_invocations > 0:
                metrics["success_rate"] = (total_invocations - total_errors) / total_invocations * 100
            else:
                metrics["success_rate"] = 100.0
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting metrics for {agent_type}: {e}")
            return {"error": str(e)}
    
    async def update_function_configuration(
        self, 
        agent_type: str, 
        config_updates: Dict[str, Any]
    ) -> bool:
        """Update Lambda function configuration"""
        try:
            function_name = f"{self.function_prefix}-{agent_type}"
            
            # Prepare update parameters
            update_params = {"FunctionName": function_name}
            
            if "memory_size" in config_updates:
                update_params["MemorySize"] = config_updates["memory_size"]
            
            if "timeout" in config_updates:
                update_params["Timeout"] = config_updates["timeout"]
            
            if "environment_variables" in config_updates:
                current_env = self.environment_variables.copy()
                current_env.update(config_updates["environment_variables"])
                update_params["Environment"] = {"Variables": current_env}
            
            # Update function configuration
            response = self.lambda_client.update_function_configuration(**update_params)
            
            logger.info(f"Updated configuration for {agent_type} function")
            return True
            
        except Exception as e:
            logger.error(f"Error updating configuration for {agent_type}: {e}")
            return False
    
    async def setup_event_triggers(self, agent_type: str, triggers: List[Dict[str, Any]]) -> bool:
        """Setup event triggers for agent Lambda functions"""
        try:
            function_name = f"{self.function_prefix}-{agent_type}"
            
            for trigger in triggers:
                trigger_type = trigger.get("type")
                
                if trigger_type == "schedule":
                    # CloudWatch Events (EventBridge) schedule
                    await self._setup_schedule_trigger(function_name, trigger)
                
                elif trigger_type == "s3":
                    # S3 bucket event
                    await self._setup_s3_trigger(function_name, trigger)
                
                elif trigger_type == "dynamodb":
                    # DynamoDB stream
                    await self._setup_dynamodb_trigger(function_name, trigger)
                
                elif trigger_type == "sqs":
                    # SQS queue
                    await self._setup_sqs_trigger(function_name, trigger)
                
                else:
                    logger.warning(f"Unknown trigger type: {trigger_type}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting up triggers for {agent_type}: {e}")
            return False
    
    async def _create_deployment_package(self, agent_type: str) -> bytes:
        """Create deployment package for agent Lambda function"""
        try:
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = os.path.join(temp_dir, f"{agent_type}_agent.zip")
                
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    # Add Lambda handler
                    handler_code = self._generate_lambda_handler(agent_type)
                    zip_file.writestr("lambda_function.py", handler_code)
                    
                    # Add agent-specific code
                    agent_code = self._get_agent_code(agent_type)
                    if agent_code:
                        zip_file.writestr(f"{agent_type}_agent.py", agent_code)
                    
                    # Add common dependencies
                    self._add_common_dependencies(zip_file)
                
                # Read deployment package
                with open(zip_path, 'rb') as f:
                    return f.read()
                    
        except Exception as e:
            logger.error(f"Error creating deployment package for {agent_type}: {e}")
            raise
    
    def _generate_lambda_handler(self, agent_type: str) -> str:
        """Generate Lambda handler code for agent"""
        return f'''
import json
import logging
import os
from datetime import datetime
import boto3

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def lambda_handler(event, context):
    """
    Lambda handler for {agent_type} agent
    """
    try:
        logger.info(f"Processing {{agent_type}} agent request")
        logger.info(f"Event: {{json.dumps(event)}}")
        
        # Extract parameters
        agent_type = event.get("agent_type", "{agent_type}")
        action = event.get("action", "process_message")
        parameters = event.get("parameters", {{}})
        correlation_id = event.get("correlation_id")
        
        # Initialize agent (simplified for Lambda)
        agent_result = process_agent_action(agent_type, action, parameters)
        
        # Prepare response
        response = {{
            "success": True,
            "agent_type": agent_type,
            "action": action,
            "result": agent_result,
            "correlation_id": correlation_id,
            "timestamp": datetime.now().isoformat(),
            "execution_context": {{
                "function_name": context.function_name,
                "function_version": context.function_version,
                "request_id": context.aws_request_id,
                "memory_limit": context.memory_limit_in_mb,
                "remaining_time": context.get_remaining_time_in_millis()
            }}
        }}
        
        logger.info(f"Agent {{agent_type}} completed successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error in {{agent_type}} agent: {{str(e)}}")
        
        return {{
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "agent_type": agent_type,
            "correlation_id": correlation_id,
            "timestamp": datetime.now().isoformat()
        }}

def process_agent_action(agent_type, action, parameters):
    """
    Process agent action based on type
    """
    if agent_type == "{agent_type}":
        return process_{agent_type}_action(action, parameters)
    else:
        raise ValueError(f"Unknown agent type: {{agent_type}}")

def process_{agent_type}_action(action, parameters):
    """
    Process {agent_type} specific actions
    """
    if action == "health_check":
        return {{
            "status": "healthy",
            "agent_type": "{agent_type}",
            "timestamp": datetime.now().isoformat()
        }}
    
    elif action == "process_message":
        # Simulate message processing
        message = parameters.get("message", {{}})
        return {{
            "processed": True,
            "message_type": message.get("message_type", "unknown"),
            "response": f"Processed by {agent_type} agent"
        }}
    
    elif action == "execute_task":
        # Simulate task execution
        task = parameters.get("task", {{}})
        return {{
            "task_completed": True,
            "task_id": task.get("task_id"),
            "result": f"Task executed by {agent_type} agent"
        }}
    
    else:
        raise ValueError(f"Unknown action: {{action}}")
'''
    
    def _get_agent_code(self, agent_type: str) -> Optional[str]:
        """Get agent-specific code"""
        # This would contain agent-specific implementation
        # For now, return None as we're using simplified handlers
        return None
    
    def _add_common_dependencies(self, zip_file: zipfile.ZipFile) -> None:
        """Add common dependencies to deployment package"""
        # Add requirements.txt content as a string
        requirements = """
boto3>=1.26.0
botocore>=1.29.0
"""
        zip_file.writestr("requirements.txt", requirements)
    
    async def _deploy_function(
        self, 
        function_name: str, 
        agent_type: str,
        deployment_package: bytes,
        config: Dict[str, Any]
    ) -> bool:
        """Deploy Lambda function"""
        try:
            # Prepare environment variables
            env_vars = self.environment_variables.copy()
            env_vars.update(config.get("environment", {}))
            env_vars.update({
                "AWS_REGION": self.session.region_name,
                "AGENT_TYPE": agent_type,
                "FUNCTION_NAME": function_name
            })
            
            # Get or create IAM role
            role_arn = await self._get_or_create_lambda_role()
            
            try:
                # Try to update existing function
                self.lambda_client.update_function_code(
                    FunctionName=function_name,
                    ZipFile=deployment_package
                )
                
                # Update configuration
                self.lambda_client.update_function_configuration(
                    FunctionName=function_name,
                    Runtime=self.runtime,
                    Handler="lambda_function.lambda_handler",
                    Role=role_arn,
                    Timeout=config.get("timeout", self.timeout),
                    MemorySize=config.get("memory_size", self.memory_size),
                    Environment={"Variables": env_vars}
                )
                
                logger.info(f"Updated existing Lambda function: {function_name}")
                
            except self.lambda_client.exceptions.ResourceNotFoundException:
                # Create new function
                self.lambda_client.create_function(
                    FunctionName=function_name,
                    Runtime=self.runtime,
                    Role=role_arn,
                    Handler="lambda_function.lambda_handler",
                    Code={"ZipFile": deployment_package},
                    Description=f"Agentic AI {agent_type} agent",
                    Timeout=config.get("timeout", self.timeout),
                    MemorySize=config.get("memory_size", self.memory_size),
                    Environment={"Variables": env_vars},
                    Tags={
                        "Project": "Vismaya-DemandOps",
                        "Component": "Agentic-AI",
                        "AgentType": agent_type
                    }
                )
                
                logger.info(f"Created new Lambda function: {function_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deploying function {function_name}: {e}")
            return False
    
    async def _get_or_create_lambda_role(self) -> str:
        """Get or create IAM role for Lambda functions"""
        try:
            role_name = f"{self.function_prefix}-execution-role"
            
            try:
                # Try to get existing role
                response = self.iam_client.get_role(RoleName=role_name)
                return response['Role']['Arn']
                
            except self.iam_client.exceptions.NoSuchEntityException:
                # Create new role
                trust_policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"Service": "lambda.amazonaws.com"},
                            "Action": "sts:AssumeRole"
                        }
                    ]
                }
                
                # Create role
                response = self.iam_client.create_role(
                    RoleName=role_name,
                    AssumeRolePolicyDocument=json.dumps(trust_policy),
                    Description="Execution role for Vismaya agentic AI Lambda functions"
                )
                
                role_arn = response['Role']['Arn']
                
                # Attach basic Lambda execution policy
                self.iam_client.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
                )
                
                # Attach additional policies for agentic AI functionality
                additional_policies = [
                    "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess",
                    "arn:aws:iam::aws:policy/AmazonS3FullAccess",
                    "arn:aws:iam::aws:policy/AmazonBedrockFullAccess",
                    "arn:aws:iam::aws:policy/CloudWatchFullAccess"
                ]
                
                for policy_arn in additional_policies:
                    try:
                        self.iam_client.attach_role_policy(
                            RoleName=role_name,
                            PolicyArn=policy_arn
                        )
                    except Exception as e:
                        logger.warning(f"Could not attach policy {policy_arn}: {e}")
                
                logger.info(f"Created IAM role: {role_name}")
                return role_arn
                
        except Exception as e:
            logger.error(f"Error managing IAM role: {e}")
            raise
    
    async def _setup_schedule_trigger(self, function_name: str, trigger: Dict[str, Any]) -> None:
        """Setup CloudWatch Events schedule trigger"""
        try:
            events_client = self.session.client('events')
            
            rule_name = f"{function_name}-schedule"
            schedule_expression = trigger.get("schedule", "rate(1 hour)")
            
            # Create or update rule
            events_client.put_rule(
                Name=rule_name,
                ScheduleExpression=schedule_expression,
                Description=f"Schedule trigger for {function_name}",
                State='ENABLED'
            )
            
            # Add Lambda target
            events_client.put_targets(
                Rule=rule_name,
                Targets=[
                    {
                        'Id': '1',
                        'Arn': f"arn:aws:lambda:{self.session.region_name}:{self._get_account_id()}:function:{function_name}",
                        'Input': json.dumps(trigger.get("input", {}))
                    }
                ]
            )
            
            # Add permission for EventBridge to invoke Lambda
            try:
                self.lambda_client.add_permission(
                    FunctionName=function_name,
                    StatementId=f"{rule_name}-permission",
                    Action='lambda:InvokeFunction',
                    Principal='events.amazonaws.com',
                    SourceArn=f"arn:aws:events:{self.session.region_name}:{self._get_account_id()}:rule/{rule_name}"
                )
            except self.lambda_client.exceptions.ResourceConflictException:
                # Permission already exists
                pass
            
            logger.info(f"Setup schedule trigger for {function_name}")
            
        except Exception as e:
            logger.error(f"Error setting up schedule trigger: {e}")
            raise
    
    async def _setup_s3_trigger(self, function_name: str, trigger: Dict[str, Any]) -> None:
        """Setup S3 event trigger"""
        # Implementation for S3 triggers
        logger.info(f"S3 trigger setup for {function_name} - not implemented yet")
    
    async def _setup_dynamodb_trigger(self, function_name: str, trigger: Dict[str, Any]) -> None:
        """Setup DynamoDB stream trigger"""
        # Implementation for DynamoDB triggers
        logger.info(f"DynamoDB trigger setup for {function_name} - not implemented yet")
    
    async def _setup_sqs_trigger(self, function_name: str, trigger: Dict[str, Any]) -> None:
        """Setup SQS queue trigger"""
        # Implementation for SQS triggers
        logger.info(f"SQS trigger setup for {function_name} - not implemented yet")
    
    def _get_account_id(self) -> str:
        """Get AWS account ID"""
        try:
            sts_client = self.session.client('sts')
            return sts_client.get_caller_identity()['Account']
        except Exception as e:
            logger.error(f"Error getting account ID: {e}")
            return "123456789012"  # Fallback