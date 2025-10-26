"""
Integration tests for AWS Backend Integration
Tests the complete AWS backend services integration
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.infrastructure.aws_backend_integration import AWSBackendIntegration
from src.infrastructure.enhanced_bedrock_manager import AIRequest, TaskComplexity


class TestAWSBackendIntegration:
    """Test AWS backend integration functionality"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing"""
        return {
            "aws_region": "us-east-1",
            "table_prefix": "test-vismaya-agentic",
            "bucket_prefix": "test-vismaya-agentic",
            "lambda": {
                "function_prefix": "test-vismaya-agent",
                "runtime": "python3.11",
                "timeout": 300,
                "memory_size": 512
            },
            "dynamodb": {
                "billing_mode": "PAY_PER_REQUEST"
            },
            "s3": {
                "encryption_type": "AES256",
                "versioning_enabled": True
            },
            "bedrock": {
                "cost_optimization": True,
                "performance_tracking": True
            }
        }
    
    @pytest.fixture
    def backend_integration(self, mock_config):
        """Create backend integration instance"""
        return AWSBackendIntegration(mock_config)
    
    @patch('src.infrastructure.aws_session_factory.AWSSessionFactory')
    @patch('src.infrastructure.aws_lambda_manager.AWSLambdaManager')
    @patch('src.infrastructure.aws_dynamodb_manager.AWSDynamoDBManager')
    @patch('src.infrastructure.aws_s3_manager.AWSS3Manager')
    @patch('src.infrastructure.enhanced_bedrock_manager.EnhancedBedrockManager')
    async def test_initialization(
        self, 
        mock_bedrock, 
        mock_s3, 
        mock_dynamodb, 
        mock_lambda, 
        mock_session_factory,
        backend_integration
    ):
        """Test backend integration initialization"""
        # Mock service managers
        mock_lambda_instance = Mock()
        mock_lambda_instance.deploy_agent_functions = AsyncMock(return_value={
            "orchestrator": True,
            "cost_management": True
        })
        mock_lambda.return_value = mock_lambda_instance
        
        mock_dynamodb_instance = Mock()
        mock_dynamodb_instance.create_all_tables = AsyncMock(return_value={
            "agent_states": True,
            "conversations": True
        })
        mock_dynamodb_instance.create_data_access_layer = AsyncMock(return_value=Mock())
        mock_dynamodb.return_value = mock_dynamodb_instance
        
        mock_s3_instance = Mock()
        mock_s3_instance.create_all_buckets = AsyncMock(return_value={
            "decision_artifacts": True,
            "reports": True
        })
        mock_s3.return_value = mock_s3_instance
        
        mock_bedrock_instance = Mock()
        mock_bedrock_instance.process_ai_request = AsyncMock(return_value=Mock(content="Test response"))
        mock_bedrock.return_value = mock_bedrock_instance
        
        # Test initialization
        result = await backend_integration.initialize()
        
        assert result is True
        assert backend_integration.initialized is True
        assert backend_integration.lambda_manager is not None
        assert backend_integration.dynamodb_manager is not None
        assert backend_integration.s3_manager is not None
        assert backend_integration.bedrock_manager is not None
    
    async def test_agent_ai_interface_creation(self, backend_integration):
        """Test agent AI interface creation"""
        # Mock bedrock manager
        backend_integration.bedrock_manager = Mock()
        
        # Get AI interface for agent
        ai_interface = backend_integration.get_agent_ai_interface("test_agent")
        
        assert ai_interface is not None
        assert ai_interface.agent_id == "test_agent"
        
        # Test caching - should return same instance
        ai_interface2 = backend_integration.get_agent_ai_interface("test_agent")
        assert ai_interface is ai_interface2
    
    async def test_lambda_invocation(self, backend_integration):
        """Test Lambda function invocation"""
        # Mock lambda manager
        mock_lambda_manager = Mock()
        mock_lambda_manager.invoke_agent_function = AsyncMock(return_value={
            "success": True,
            "result": {"status": "completed"},
            "execution_duration": 1500,
            "memory_used": 128
        })
        backend_integration.lambda_manager = mock_lambda_manager
        
        # Mock data access for logging
        mock_data_access = Mock()
        mock_data_access.store_system_event = AsyncMock(return_value=True)
        backend_integration.data_access = mock_data_access
        
        # Test invocation
        result = await backend_integration.invoke_agent_lambda(
            "cost_management",
            "analyze_costs",
            {"data": "test"},
            "test-correlation-id"
        )
        
        assert result["success"] is True
        assert result["result"]["status"] == "completed"
        
        # Verify lambda manager was called correctly
        mock_lambda_manager.invoke_agent_function.assert_called_once()
        call_args = mock_lambda_manager.invoke_agent_function.call_args[0]
        assert call_args[0] == "cost_management"
        assert call_args[1]["action"] == "analyze_costs"
        assert call_args[1]["correlation_id"] == "test-correlation-id"
    
    async def test_data_storage_and_retrieval(self, backend_integration):
        """Test data storage and retrieval"""
        # Mock data access layer
        mock_data_access = Mock()
        mock_data_access.store_agent_state = AsyncMock(return_value=True)
        mock_data_access.get_agent_state = AsyncMock(return_value={
            "agent_id": "test_agent",
            "status": "active",
            "last_updated": datetime.now().isoformat()
        })
        backend_integration.data_access = mock_data_access
        
        # Test storing agent state
        test_data = {"status": "active", "task": "processing"}
        result = await backend_integration.store_agent_data("test_agent", "state", test_data)
        
        assert result is True
        mock_data_access.store_agent_state.assert_called_once_with("test_agent", test_data)
        
        # Test retrieving agent state
        retrieved_data = await backend_integration.retrieve_agent_data("test_agent", "state")
        
        assert retrieved_data is not None
        assert retrieved_data["agent_id"] == "test_agent"
        assert retrieved_data["status"] == "active"
        mock_data_access.get_agent_state.assert_called_once_with("test_agent")
    
    async def test_document_storage(self, backend_integration):
        """Test document storage"""
        # Mock document manager
        mock_document_manager = Mock()
        mock_document_manager.store_decision_artifact = AsyncMock(return_value="s3://test-bucket/test-file")
        backend_integration.document_manager = mock_document_manager
        
        # Test storing decision artifact
        test_content = b"test document content"
        metadata = {
            "proposal_id": "test-proposal-123",
            "artifact_type": "analysis_report"
        }
        
        result = await backend_integration.store_document(
            "decision_artifact",
            test_content,
            "test_report.pdf",
            metadata
        )
        
        assert result == "s3://test-bucket/test-file"
        mock_document_manager.store_decision_artifact.assert_called_once_with(
            "test-proposal-123",
            "analysis_report",
            test_content,
            "test_report.pdf"
        )
    
    async def test_system_metrics(self, backend_integration):
        """Test system metrics collection"""
        # Mock service managers
        mock_lambda_manager = Mock()
        mock_lambda_manager.get_function_metrics = AsyncMock(return_value={
            "function_name": "test-function",
            "invocations": {"total": 100},
            "duration": {"average_ms": 1500}
        })
        backend_integration.lambda_manager = mock_lambda_manager
        
        mock_dynamodb_manager = Mock()
        mock_dynamodb_manager.get_table_metrics = AsyncMock(return_value={
            "agent_states": {"read_capacity": {"total": 50}}
        })
        backend_integration.dynamodb_manager = mock_dynamodb_manager
        
        mock_s3_manager = Mock()
        mock_s3_manager.get_bucket_metrics = AsyncMock(return_value={
            "decision_artifacts": {"size_bytes": 1024000}
        })
        backend_integration.s3_manager = mock_s3_manager
        
        mock_bedrock_manager = Mock()
        mock_bedrock_manager.get_usage_statistics = AsyncMock(return_value={
            "total_requests": 50,
            "total_cost": 12.50
        })
        backend_integration.bedrock_manager = mock_bedrock_manager
        
        # Test metrics collection
        metrics = await backend_integration.get_system_metrics()
        
        assert "timestamp" in metrics
        assert "services" in metrics
        assert "lambda" in metrics["services"]
        assert "dynamodb" in metrics["services"]
        assert "s3" in metrics["services"]
        assert "bedrock" in metrics["services"]
    
    async def test_cost_optimization(self, backend_integration):
        """Test cost optimization recommendations"""
        # Mock bedrock manager
        mock_bedrock_manager = Mock()
        mock_bedrock_manager.optimize_costs = AsyncMock(return_value={
            "total_monthly_cost": 25.75,
            "optimization_recommendations": [
                {
                    "type": "model_substitution",
                    "current_model": "Claude 3 Opus",
                    "recommended_model": "Claude 3 Haiku",
                    "potential_monthly_savings": 15.50
                }
            ],
            "potential_total_savings": 15.50
        })
        backend_integration.bedrock_manager = mock_bedrock_manager
        
        # Mock get_system_metrics for Lambda optimization
        backend_integration.get_system_metrics = AsyncMock(return_value={
            "services": {
                "lambda": {
                    "cost_management": {
                        "invocations": {"total": 1000},
                        "duration": {"average_ms": 12000}  # High duration
                    }
                },
                "dynamodb": {
                    "agent_states": {
                        "throttles": 0
                    }
                }
            }
        })
        
        # Test cost optimization
        optimization = await backend_integration.optimize_costs()
        
        assert "timestamp" in optimization
        assert "recommendations" in optimization
        assert "total_potential_savings" in optimization
        assert len(optimization["recommendations"]) >= 1
        
        # Check for Bedrock optimization
        bedrock_rec = next(
            (r for r in optimization["recommendations"] if r["type"] == "model_substitution"), 
            None
        )
        assert bedrock_rec is not None
        assert bedrock_rec["potential_monthly_savings"] == 15.50
        
        # Check for Lambda optimization (high duration)
        lambda_rec = next(
            (r for r in optimization["recommendations"] if r["type"] == "lambda_optimization"), 
            None
        )
        assert lambda_rec is not None
        assert "High average execution time" in lambda_rec["issue"]
    
    async def test_system_backup(self, backend_integration):
        """Test system backup creation"""
        # Mock service managers
        mock_bedrock_manager = Mock()
        mock_bedrock_manager.get_usage_statistics = AsyncMock(return_value={
            "total_requests": 100,
            "total_cost": 25.50
        })
        backend_integration.bedrock_manager = mock_bedrock_manager
        
        mock_s3_manager = Mock()
        mock_s3_manager.create_backup = AsyncMock(return_value="s3://test-bucket/backup.json")
        backend_integration.s3_manager = mock_s3_manager
        
        # Mock get_system_metrics
        backend_integration.get_system_metrics = AsyncMock(return_value={
            "services": {"lambda": {}, "dynamodb": {}}
        })
        
        # Test backup creation
        backup_url = await backend_integration.create_system_backup()
        
        assert backup_url == "s3://test-bucket/backup.json"
        mock_s3_manager.create_backup.assert_called_once()
        
        # Verify backup data structure
        call_args = mock_s3_manager.create_backup.call_args[0]
        backup_data = call_args[0]
        
        assert "timestamp" in backup_data
        assert "version" in backup_data
        assert "components" in backup_data
        assert "configuration" in backup_data["components"]
        assert "bedrock_usage" in backup_data["components"]
        assert "system_metrics" in backup_data["components"]
    
    async def test_health_check(self, backend_integration):
        """Test system health check"""
        # Mock service managers
        mock_lambda_manager = Mock()
        mock_lambda_manager.invoke_agent_function = AsyncMock(return_value={
            "success": True,
            "status_code": 200
        })
        backend_integration.lambda_manager = mock_lambda_manager
        backend_integration.dynamodb_manager = Mock()
        backend_integration.s3_manager = Mock()
        backend_integration.bedrock_manager = Mock()
        
        # Test health check
        health_status = await backend_integration.health_check()
        
        assert "timestamp" in health_status
        assert "overall_status" in health_status
        assert "services" in health_status
        
        # Check individual service statuses
        assert "lambda" in health_status["services"]
        assert "dynamodb" in health_status["services"]
        assert "s3" in health_status["services"]
        assert "bedrock" in health_status["services"]
        
        # Lambda should be healthy (mocked successful invocation)
        assert health_status["services"]["lambda"]["status"] == "healthy"
        
        # Other services should be healthy (managers exist)
        assert health_status["services"]["dynamodb"]["status"] == "healthy"
        assert health_status["services"]["s3"]["status"] == "healthy"
        assert health_status["services"]["bedrock"]["status"] == "healthy"
    
    def test_service_info(self, backend_integration):
        """Test service information retrieval"""
        # Mock service managers with basic info
        mock_lambda_manager = Mock()
        mock_lambda_manager.agent_configs = {"orchestrator": {}, "cost_management": {}}
        mock_lambda_manager.runtime = "python3.11"
        backend_integration.lambda_manager = mock_lambda_manager
        
        mock_dynamodb_manager = Mock()
        mock_dynamodb_manager.table_definitions = {"agent_states": {}, "conversations": {}}
        mock_dynamodb_manager.billing_mode = "PAY_PER_REQUEST"
        backend_integration.dynamodb_manager = mock_dynamodb_manager
        
        mock_s3_manager = Mock()
        mock_s3_manager.get_bucket_info.return_value = {"decision_artifacts": {"purpose": "test"}}
        mock_s3_manager.encryption_type = "AES256"
        backend_integration.s3_manager = mock_s3_manager
        
        mock_bedrock_manager = Mock()
        mock_bedrock_manager.get_model_capabilities.return_value = {"claude-3-sonnet": {"name": "Claude 3 Sonnet"}}
        mock_bedrock_manager.cost_optimization_enabled = True
        backend_integration.bedrock_manager = mock_bedrock_manager
        
        # Test service info
        service_info = backend_integration.get_service_info()
        
        assert "lambda" in service_info
        assert "dynamodb" in service_info
        assert "s3" in service_info
        assert "bedrock" in service_info
        
        # Check Lambda info
        assert service_info["lambda"]["runtime"] == "python3.11"
        assert len(service_info["lambda"]["agent_functions"]) == 2
        
        # Check DynamoDB info
        assert service_info["dynamodb"]["billing_mode"] == "PAY_PER_REQUEST"
        assert len(service_info["dynamodb"]["tables"]) == 2
        
        # Check S3 info
        assert service_info["s3"]["encryption"] == "AES256"
        
        # Check Bedrock info
        assert service_info["bedrock"]["cost_optimization"] is True


if __name__ == "__main__":
    pytest.main([__file__])