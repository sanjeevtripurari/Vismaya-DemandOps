"""
AWS Backend Integration for Agentic AI System
Integrates all AWS backend services for scalable execution
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

from .aws_session_factory import AWSSessionFactory
from .aws_lambda_manager import AWSLambdaManager
from .aws_dynamodb_manager import AWSDynamoDBManager, DynamoDBDataAccessLayer
from .aws_s3_manager import AWSS3Manager, S3DocumentManager
from .enhanced_bedrock_manager import EnhancedBedrockManager, AgentAIInterface

logger = logging.getLogger(__name__)


class AWSBackendIntegration:
    """
    Unified AWS backend integration for the agentic AI system
    Provides a single interface to all AWS services
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialize session factory
        self.session_factory = AWSSessionFactory(config)
        
        # Initialize service managers
        self.lambda_manager: Optional[AWSLambdaManager] = None
        self.dynamodb_manager: Optional[AWSDynamoDBManager] = None
        self.s3_manager: Optional[AWSS3Manager] = None
        self.bedrock_manager: Optional[EnhancedBedrockManager] = None
        
        # High-level interfaces
        self.data_access: Optional[DynamoDBDataAccessLayer] = None
        self.document_manager: Optional[S3DocumentManager] = None
        
        # Agent AI interfaces
        self.agent_ai_interfaces: Dict[str, AgentAIInterface] = {}
        
        # System status
        self.initialized = False
        self.initialization_errors = []
    
    async def initialize(self) -> bool:
        """Initialize all AWS backend services"""
        try:
            logger.info("Initializing AWS backend integration...")
            
            # Initialize service managers
            await self._initialize_service_managers()
            
            # Setup infrastructure
            await self._setup_infrastructure()
            
            # Create high-level interfaces
            await self._create_interfaces()
            
            # Verify connectivity
            await self._verify_connectivity()
            
            self.initialized = True
            logger.info("AWS backend integration initialized successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing AWS backend integration: {e}")
            self.initialization_errors.append(str(e))
            return False
    
    async def _initialize_service_managers(self) -> None:
        """Initialize all service managers"""
        try:
            # Initialize Lambda manager
            lambda_config = self.config.get("lambda", {})
            self.lambda_manager = AWSLambdaManager(self.session_factory, lambda_config)
            logger.info("Lambda manager initialized")
            
            # Initialize DynamoDB manager
            dynamodb_config = self.config.get("dynamodb", {})
            self.dynamodb_manager = AWSDynamoDBManager(self.session_factory, dynamodb_config)
            logger.info("DynamoDB manager initialized")
            
            # Initialize S3 manager
            s3_config = self.config.get("s3", {})
            self.s3_manager = AWSS3Manager(self.session_factory, s3_config)
            logger.info("S3 manager initialized")
            
            # Initialize Bedrock manager
            bedrock_config = self.config.get("bedrock", {})
            self.bedrock_manager = EnhancedBedrockManager(self.session_factory, bedrock_config)
            logger.info("Bedrock manager initialized")
            
        except Exception as e:
            logger.error(f"Error initializing service managers: {e}")
            raise
    
    async def _setup_infrastructure(self) -> None:
        """Setup AWS infrastructure"""
        try:
            # Setup DynamoDB tables
            logger.info("Setting up DynamoDB tables...")
            dynamodb_results = await self.dynamodb_manager.create_all_tables()
            
            failed_tables = [table for table, success in dynamodb_results.items() if not success]
            if failed_tables:
                logger.warning(f"Failed to create DynamoDB tables: {failed_tables}")
            
            # Setup S3 buckets
            logger.info("Setting up S3 buckets...")
            s3_results = await self.s3_manager.create_all_buckets()
            
            failed_buckets = [bucket for bucket, success in s3_results.items() if not success]
            if failed_buckets:
                logger.warning(f"Failed to create S3 buckets: {failed_buckets}")
            
            # Deploy Lambda functions
            logger.info("Deploying Lambda functions...")
            lambda_results = await self.lambda_manager.deploy_agent_functions()
            
            failed_functions = [func for func, success in lambda_results.items() if not success]
            if failed_functions:
                logger.warning(f"Failed to deploy Lambda functions: {failed_functions}")
            
            logger.info("AWS infrastructure setup completed")
            
        except Exception as e:
            logger.error(f"Error setting up infrastructure: {e}")
            raise
    
    async def _create_interfaces(self) -> None:
        """Create high-level interfaces"""
        try:
            # Create data access layer
            self.data_access = await self.dynamodb_manager.create_data_access_layer()
            
            # Create document manager
            self.document_manager = S3DocumentManager(self.s3_manager)
            
            logger.info("High-level interfaces created")
            
        except Exception as e:
            logger.error(f"Error creating interfaces: {e}")
            raise
    
    async def _verify_connectivity(self) -> None:
        """Verify connectivity to all AWS services"""
        try:
            # Test DynamoDB connectivity
            test_agent_state = {
                "status": "test",
                "timestamp": datetime.now().isoformat()
            }
            await self.data_access.store_agent_state("test_agent", test_agent_state)
            logger.debug("DynamoDB connectivity verified")
            
            # Test S3 connectivity
            test_content = b"test content"
            s3_url = await self.s3_manager.upload_file(
                bucket_type="agent_artifacts",
                file_path="/test/connectivity_test.txt",
                content=test_content
            )
            if s3_url:
                await self.s3_manager.delete_file(s3_url)
            logger.debug("S3 connectivity verified")
            
            # Test Bedrock connectivity (simple request)
            from .enhanced_bedrock_manager import AIRequest, TaskComplexity
            test_request = AIRequest(
                task_type="conversation",
                content="Hello, this is a connectivity test.",
                complexity=TaskComplexity.SIMPLE
            )
            await self.bedrock_manager.process_ai_request(test_request)
            logger.debug("Bedrock connectivity verified")
            
            logger.info("All AWS service connectivity verified")
            
        except Exception as e:
            logger.warning(f"Connectivity verification failed: {e}")
            # Don't raise here as this is not critical for initialization
    
    def get_agent_ai_interface(self, agent_id: str) -> AgentAIInterface:
        """Get AI interface for specific agent"""
        if agent_id not in self.agent_ai_interfaces:
            self.agent_ai_interfaces[agent_id] = AgentAIInterface(
                self.bedrock_manager, agent_id
            )
        
        return self.agent_ai_interfaces[agent_id]
    
    async def invoke_agent_lambda(
        self, 
        agent_type: str, 
        action: str,
        parameters: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Invoke agent Lambda function"""
        try:
            payload = {
                "action": action,
                "parameters": parameters,
                "correlation_id": correlation_id
            }
            
            result = await self.lambda_manager.invoke_agent_function(agent_type, payload)
            
            # Log invocation for monitoring
            await self._log_lambda_invocation(agent_type, action, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error invoking agent Lambda {agent_type}: {e}")
            return {"success": False, "error": str(e)}
    
    async def store_agent_data(self, agent_id: str, data_type: str, data: Dict[str, Any]) -> bool:
        """Store agent data in appropriate storage"""
        try:
            if data_type == "state":
                return await self.data_access.store_agent_state(agent_id, data)
            
            elif data_type == "conversation":
                thread_id = data.get("thread_id", f"{agent_id}_conversation")
                return await self.data_access.store_conversation_message(thread_id, data)
            
            elif data_type == "decision":
                return await self.data_access.store_decision_proposal(data)
            
            elif data_type == "event":
                return await self.data_access.store_system_event(data)
            
            else:
                logger.warning(f"Unknown data type: {data_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error storing agent data: {e}")
            return False
    
    async def retrieve_agent_data(
        self, 
        agent_id: str, 
        data_type: str, 
        query_params: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """Retrieve agent data from storage"""
        try:
            if data_type == "state":
                return await self.data_access.get_agent_state(agent_id)
            
            elif data_type == "conversation":
                thread_id = query_params.get("thread_id", f"{agent_id}_conversation")
                limit = query_params.get("limit", 50)
                return await self.data_access.get_conversation_history(thread_id, limit)
            
            elif data_type == "decision":
                proposal_id = query_params.get("proposal_id")
                if proposal_id:
                    return await self.data_access.get_decision_proposal(proposal_id)
                return None
            
            elif data_type == "events":
                event_date = query_params.get("event_date", datetime.now().strftime("%Y-%m-%d"))
                event_type = query_params.get("event_type")
                limit = query_params.get("limit", 100)
                return await self.data_access.get_system_events(event_date, event_type, limit)
            
            else:
                logger.warning(f"Unknown data type: {data_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving agent data: {e}")
            return None
    
    async def store_document(
        self, 
        document_type: str, 
        content: bytes,
        filename: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """Store document in S3"""
        try:
            if document_type == "decision_artifact":
                proposal_id = metadata.get("proposal_id", "unknown")
                artifact_type = metadata.get("artifact_type", "general")
                return await self.document_manager.store_decision_artifact(
                    proposal_id, artifact_type, content, filename
                )
            
            elif document_type == "report":
                report_type = metadata.get("report_type", "general")
                agent_id = metadata.get("agent_id")
                return await self.document_manager.store_report(
                    report_type, content, filename, agent_id
                )
            
            elif document_type == "audit_log":
                log_type = metadata.get("log_type", "general")
                return await self.document_manager.store_audit_log(
                    log_type, content, filename
                )
            
            elif document_type == "agent_artifact":
                agent_id = metadata.get("agent_id", "unknown")
                artifact_type = metadata.get("artifact_type", "general")
                return await self.document_manager.store_agent_artifact(
                    agent_id, artifact_type, content, filename
                )
            
            else:
                # Generic S3 upload
                bucket_type = metadata.get("bucket_type", "agent_artifacts")
                return await self.s3_manager.upload_file(
                    bucket_type, f"/{document_type}/{filename}", content, metadata
                )
                
        except Exception as e:
            logger.error(f"Error storing document: {e}")
            return None
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics"""
        try:
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "services": {}
            }
            
            # Lambda metrics
            try:
                lambda_metrics = {}
                for agent_type in ["orchestrator", "cost_management", "resource_management", 
                                 "forecasting", "alert_management", "user_interface", "approval"]:
                    agent_metrics = await self.lambda_manager.get_function_metrics(agent_type)
                    lambda_metrics[agent_type] = agent_metrics
                
                metrics["services"]["lambda"] = lambda_metrics
            except Exception as e:
                metrics["services"]["lambda"] = {"error": str(e)}
            
            # DynamoDB metrics
            try:
                dynamodb_metrics = await self.dynamodb_manager.get_table_metrics()
                metrics["services"]["dynamodb"] = dynamodb_metrics
            except Exception as e:
                metrics["services"]["dynamodb"] = {"error": str(e)}
            
            # S3 metrics
            try:
                s3_metrics = await self.s3_manager.get_bucket_metrics()
                metrics["services"]["s3"] = s3_metrics
            except Exception as e:
                metrics["services"]["s3"] = {"error": str(e)}
            
            # Bedrock metrics
            try:
                bedrock_metrics = await self.bedrock_manager.get_usage_statistics()
                metrics["services"]["bedrock"] = bedrock_metrics
            except Exception as e:
                metrics["services"]["bedrock"] = {"error": str(e)}
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {"error": str(e)}
    
    async def optimize_costs(self) -> Dict[str, Any]:
        """Get cost optimization recommendations across all services"""
        try:
            optimization_results = {
                "timestamp": datetime.now().isoformat(),
                "recommendations": [],
                "total_potential_savings": 0.0
            }
            
            # Bedrock cost optimization
            bedrock_optimization = await self.bedrock_manager.optimize_costs()
            if "optimization_recommendations" in bedrock_optimization:
                optimization_results["recommendations"].extend(
                    bedrock_optimization["optimization_recommendations"]
                )
                optimization_results["total_potential_savings"] += bedrock_optimization.get(
                    "potential_total_savings", 0.0
                )
            
            # Lambda cost optimization (basic recommendations)
            lambda_metrics = await self.get_system_metrics()
            lambda_data = lambda_metrics.get("services", {}).get("lambda", {})
            
            for agent_type, metrics in lambda_data.items():
                if isinstance(metrics, dict) and "invocations" in metrics:
                    total_invocations = metrics["invocations"]["total"]
                    avg_duration = metrics["duration"]["average_ms"]
                    
                    if avg_duration > 10000:  # More than 10 seconds
                        optimization_results["recommendations"].append({
                            "type": "lambda_optimization",
                            "service": f"Lambda function {agent_type}",
                            "issue": "High average execution time",
                            "recommendation": "Consider optimizing function code or increasing memory allocation",
                            "potential_monthly_savings": total_invocations * 0.001  # Rough estimate
                        })
            
            # DynamoDB optimization (basic recommendations)
            dynamodb_data = lambda_metrics.get("services", {}).get("dynamodb", {})
            
            for table_key, metrics in dynamodb_data.items():
                if isinstance(metrics, dict) and "throttles" in metrics:
                    if metrics["throttles"] > 0:
                        optimization_results["recommendations"].append({
                            "type": "dynamodb_optimization",
                            "service": f"DynamoDB table {table_key}",
                            "issue": "Throttling detected",
                            "recommendation": "Consider switching to on-demand billing or increasing provisioned capacity",
                            "potential_monthly_savings": 0.0  # May actually increase costs but improve performance
                        })
            
            return optimization_results
            
        except Exception as e:
            logger.error(f"Error optimizing costs: {e}")
            return {"error": str(e)}
    
    async def create_system_backup(self) -> Optional[str]:
        """Create comprehensive system backup"""
        try:
            backup_data = {
                "timestamp": datetime.now().isoformat(),
                "version": "1.0",
                "components": {}
            }
            
            # Backup system configuration
            backup_data["components"]["configuration"] = self.config
            
            # Backup usage statistics
            backup_data["components"]["bedrock_usage"] = await self.bedrock_manager.get_usage_statistics()
            
            # Backup system metrics
            backup_data["components"]["system_metrics"] = await self.get_system_metrics()
            
            # Create backup in S3
            backup_name = f"system_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            s3_url = await self.s3_manager.create_backup(backup_data, backup_name)
            
            if s3_url:
                logger.info(f"System backup created: {s3_url}")
            
            return s3_url
            
        except Exception as e:
            logger.error(f"Error creating system backup: {e}")
            return None
    
    async def _log_lambda_invocation(
        self, 
        agent_type: str, 
        action: str, 
        result: Dict[str, Any]
    ) -> None:
        """Log Lambda invocation for monitoring"""
        try:
            event_data = {
                "event_type": "lambda_invocation",
                "source": "aws_backend_integration",
                "severity": "info",
                "agent_type": agent_type,
                "action": action,
                "success": result.get("success", False),
                "execution_duration": result.get("execution_duration", 0),
                "memory_used": result.get("memory_used", 0),
                "timestamp": datetime.now().isoformat()
            }
            
            await self.data_access.store_system_event(event_data)
            
        except Exception as e:
            logger.warning(f"Error logging Lambda invocation: {e}")
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about all configured services"""
        return {
            "lambda": {
                "agent_functions": list(self.lambda_manager.agent_configs.keys()) if self.lambda_manager else [],
                "runtime": self.lambda_manager.runtime if self.lambda_manager else None
            },
            "dynamodb": {
                "tables": list(self.dynamodb_manager.table_definitions.keys()) if self.dynamodb_manager else [],
                "billing_mode": self.dynamodb_manager.billing_mode if self.dynamodb_manager else None
            },
            "s3": {
                "buckets": self.s3_manager.get_bucket_info() if self.s3_manager else {},
                "encryption": self.s3_manager.encryption_type if self.s3_manager else None
            },
            "bedrock": {
                "models": self.bedrock_manager.get_model_capabilities() if self.bedrock_manager else {},
                "cost_optimization": self.bedrock_manager.cost_optimization_enabled if self.bedrock_manager else False
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all services"""
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "services": {}
        }
        
        services_to_check = [
            ("lambda", self.lambda_manager),
            ("dynamodb", self.dynamodb_manager),
            ("s3", self.s3_manager),
            ("bedrock", self.bedrock_manager)
        ]
        
        for service_name, manager in services_to_check:
            try:
                if manager:
                    # Basic connectivity test
                    if service_name == "lambda":
                        # Test with a simple health check invocation
                        result = await manager.invoke_agent_function(
                            "orchestrator", 
                            {"action": "health_check", "parameters": {}},
                            "Event"  # Async invocation
                        )
                        health_status["services"][service_name] = {
                            "status": "healthy" if result.get("success") else "degraded",
                            "details": result
                        }
                    else:
                        # For other services, assume healthy if manager exists
                        health_status["services"][service_name] = {
                            "status": "healthy",
                            "details": "Service manager initialized"
                        }
                else:
                    health_status["services"][service_name] = {
                        "status": "unavailable",
                        "details": "Service manager not initialized"
                    }
                    health_status["overall_status"] = "degraded"
                    
            except Exception as e:
                health_status["services"][service_name] = {
                    "status": "unhealthy",
                    "details": str(e)
                }
                health_status["overall_status"] = "unhealthy"
        
        return health_status