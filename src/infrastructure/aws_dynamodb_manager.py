"""
AWS DynamoDB Manager for Agentic AI System
Manages DynamoDB tables for persistent data storage
"""

import logging
import boto3
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from .aws_session_factory import AWSSessionFactory

logger = logging.getLogger(__name__)


class AWSDynamoDBManager:
    """
    Manages DynamoDB tables for agentic AI system data storage
    Handles table creation, configuration, and data access patterns
    """
    
    def __init__(self, aws_session_factory: AWSSessionFactory, config: Dict[str, Any]):
        self.session_factory = aws_session_factory
        self.config = config
        self.session = None
        self.dynamodb_client = None
        self.dynamodb_resource = None
        
        # Table configuration
        self.table_prefix = config.get("table_prefix", "vismaya-agentic")
        self.region = config.get("aws_region", "us-east-1")
        self.billing_mode = config.get("billing_mode", "PAY_PER_REQUEST")
        
        # Table definitions
        self.table_definitions = {
            "agent_states": {
                "table_name": f"{self.table_prefix}-agent-states",
                "partition_key": "agent_id",
                "sort_key": None,
                "attributes": [
                    {"AttributeName": "agent_id", "AttributeType": "S"},
                    {"AttributeName": "status", "AttributeType": "S"},
                    {"AttributeName": "last_updated", "AttributeType": "S"}
                ],
                "global_secondary_indexes": [
                    {
                        "IndexName": "status-index",
                        "Keys": [
                            {"AttributeName": "status", "KeyType": "HASH"},
                            {"AttributeName": "last_updated", "KeyType": "RANGE"}
                        ],
                        "Projection": {"ProjectionType": "ALL"}
                    }
                ]
            },
            "conversations": {
                "table_name": f"{self.table_prefix}-conversations",
                "partition_key": "thread_id",
                "sort_key": "timestamp",
                "attributes": [
                    {"AttributeName": "thread_id", "AttributeType": "S"},
                    {"AttributeName": "timestamp", "AttributeType": "S"},
                    {"AttributeName": "sender", "AttributeType": "S"},
                    {"AttributeName": "message_type", "AttributeType": "S"}
                ],
                "global_secondary_indexes": [
                    {
                        "IndexName": "sender-timestamp-index",
                        "Keys": [
                            {"AttributeName": "sender", "KeyType": "HASH"},
                            {"AttributeName": "timestamp", "KeyType": "RANGE"}
                        ],
                        "Projection": {"ProjectionType": "ALL"}
                    }
                ]
            },
            "decisions": {
                "table_name": f"{self.table_prefix}-decisions",
                "partition_key": "proposal_id",
                "sort_key": None,
                "attributes": [
                    {"AttributeName": "proposal_id", "AttributeType": "S"},
                    {"AttributeName": "status", "AttributeType": "S"},
                    {"AttributeName": "created_at", "AttributeType": "S"},
                    {"AttributeName": "created_by", "AttributeType": "S"},
                    {"AttributeName": "category", "AttributeType": "S"}
                ],
                "global_secondary_indexes": [
                    {
                        "IndexName": "status-created-index",
                        "Keys": [
                            {"AttributeName": "status", "KeyType": "HASH"},
                            {"AttributeName": "created_at", "KeyType": "RANGE"}
                        ],
                        "Projection": {"ProjectionType": "ALL"}
                    },
                    {
                        "IndexName": "category-created-index",
                        "Keys": [
                            {"AttributeName": "category", "KeyType": "HASH"},
                            {"AttributeName": "created_at", "KeyType": "RANGE"}
                        ],
                        "Projection": {"ProjectionType": "ALL"}
                    }
                ]
            },
            "system_events": {
                "table_name": f"{self.table_prefix}-system-events",
                "partition_key": "event_date",
                "sort_key": "timestamp",
                "attributes": [
                    {"AttributeName": "event_date", "AttributeType": "S"},
                    {"AttributeName": "timestamp", "AttributeType": "S"},
                    {"AttributeName": "event_type", "AttributeType": "S"},
                    {"AttributeName": "source", "AttributeType": "S"},
                    {"AttributeName": "severity", "AttributeType": "S"}
                ],
                "global_secondary_indexes": [
                    {
                        "IndexName": "event-type-timestamp-index",
                        "Keys": [
                            {"AttributeName": "event_type", "KeyType": "HASH"},
                            {"AttributeName": "timestamp", "KeyType": "RANGE"}
                        ],
                        "Projection": {"ProjectionType": "ALL"}
                    },
                    {
                        "IndexName": "severity-timestamp-index",
                        "Keys": [
                            {"AttributeName": "severity", "KeyType": "HASH"},
                            {"AttributeName": "timestamp", "KeyType": "RANGE"}
                        ],
                        "Projection": {"ProjectionType": "ALL"}
                    }
                ]
            },
            "context_data": {
                "table_name": f"{self.table_prefix}-context-data",
                "partition_key": "context_id",
                "sort_key": "version",
                "attributes": [
                    {"AttributeName": "context_id", "AttributeType": "S"},
                    {"AttributeName": "version", "AttributeType": "N"},
                    {"AttributeName": "agent_id", "AttributeType": "S"},
                    {"AttributeName": "last_updated", "AttributeType": "S"}
                ],
                "global_secondary_indexes": [
                    {
                        "IndexName": "agent-updated-index",
                        "Keys": [
                            {"AttributeName": "agent_id", "KeyType": "HASH"},
                            {"AttributeName": "last_updated", "KeyType": "RANGE"}
                        ],
                        "Projection": {"ProjectionType": "ALL"}
                    }
                ]
            },
            "workflow_executions": {
                "table_name": f"{self.table_prefix}-workflow-executions",
                "partition_key": "workflow_id",
                "sort_key": "execution_id",
                "attributes": [
                    {"AttributeName": "workflow_id", "AttributeType": "S"},
                    {"AttributeName": "execution_id", "AttributeType": "S"},
                    {"AttributeName": "status", "AttributeType": "S"},
                    {"AttributeName": "started_at", "AttributeType": "S"},
                    {"AttributeName": "completed_at", "AttributeType": "S"}
                ],
                "global_secondary_indexes": [
                    {
                        "IndexName": "status-started-index",
                        "Keys": [
                            {"AttributeName": "status", "KeyType": "HASH"},
                            {"AttributeName": "started_at", "KeyType": "RANGE"}
                        ],
                        "Projection": {"ProjectionType": "ALL"}
                    }
                ]
            }
        }
        
        self._initialize_clients()
    
    def _initialize_clients(self) -> None:
        """Initialize DynamoDB clients"""
        try:
            self.session = self.session_factory.get_session()
            self.dynamodb_client = self.session.client('dynamodb')
            self.dynamodb_resource = self.session.resource('dynamodb')
            logger.info("DynamoDB clients initialized")
        except Exception as e:
            logger.error(f"Failed to initialize DynamoDB clients: {e}")
            raise
    
    async def create_all_tables(self) -> Dict[str, bool]:
        """Create all required DynamoDB tables"""
        results = {}
        
        for table_key, table_def in self.table_definitions.items():
            try:
                success = await self._create_table(table_def)
                results[table_key] = success
                
                if success:
                    logger.info(f"Successfully created/verified table: {table_def['table_name']}")
                else:
                    logger.error(f"Failed to create table: {table_def['table_name']}")
                    
            except Exception as e:
                logger.error(f"Error creating table {table_key}: {e}")
                results[table_key] = False
        
        return results
    
    async def _create_table(self, table_def: Dict[str, Any]) -> bool:
        """Create individual DynamoDB table"""
        try:
            table_name = table_def["table_name"]
            
            # Check if table already exists
            try:
                table = self.dynamodb_resource.Table(table_name)
                table.load()
                logger.info(f"Table {table_name} already exists")
                
                # Verify table configuration
                await self._verify_table_configuration(table, table_def)
                return True
                
            except self.dynamodb_client.exceptions.ResourceNotFoundException:
                # Table doesn't exist, create it
                pass
            
            # Prepare table creation parameters
            key_schema = [
                {
                    "AttributeName": table_def["partition_key"],
                    "KeyType": "HASH"
                }
            ]
            
            if table_def.get("sort_key"):
                key_schema.append({
                    "AttributeName": table_def["sort_key"],
                    "KeyType": "RANGE"
                })
            
            # Prepare attribute definitions
            attribute_definitions = table_def["attributes"]
            
            # Create table parameters
            create_params = {
                "TableName": table_name,
                "KeySchema": key_schema,
                "AttributeDefinitions": attribute_definitions,
                "BillingMode": self.billing_mode
            }
            
            # Add Global Secondary Indexes if defined
            if table_def.get("global_secondary_indexes"):
                gsi_list = []
                
                for gsi in table_def["global_secondary_indexes"]:
                    gsi_key_schema = []
                    for key in gsi["Keys"]:
                        gsi_key_schema.append({
                            "AttributeName": key["AttributeName"],
                            "KeyType": key["KeyType"]
                        })
                    
                    gsi_def = {
                        "IndexName": gsi["IndexName"],
                        "KeySchema": gsi_key_schema,
                        "Projection": gsi["Projection"]
                    }
                    
                    if self.billing_mode == "PROVISIONED":
                        gsi_def["ProvisionedThroughput"] = {
                            "ReadCapacityUnits": 5,
                            "WriteCapacityUnits": 5
                        }
                    
                    gsi_list.append(gsi_def)
                
                create_params["GlobalSecondaryIndexes"] = gsi_list
            
            # Add provisioned throughput if using provisioned billing
            if self.billing_mode == "PROVISIONED":
                create_params["ProvisionedThroughput"] = {
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5
                }
            
            # Create table
            response = self.dynamodb_client.create_table(**create_params)
            
            # Wait for table to be active
            waiter = self.dynamodb_client.get_waiter('table_exists')
            waiter.wait(
                TableName=table_name,
                WaiterConfig={
                    'Delay': 5,
                    'MaxAttempts': 60
                }
            )
            
            logger.info(f"Created table: {table_name}")
            
            # Enable point-in-time recovery
            await self._enable_point_in_time_recovery(table_name)
            
            # Add tags
            await self._tag_table(table_name)
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating table {table_def['table_name']}: {e}")
            return False
    
    async def _verify_table_configuration(self, table, table_def: Dict[str, Any]) -> None:
        """Verify existing table configuration matches requirements"""
        try:
            # Check if point-in-time recovery is enabled
            table_name = table_def["table_name"]
            
            backup_response = self.dynamodb_client.describe_continuous_backups(
                TableName=table_name
            )
            
            pitr_enabled = backup_response['ContinuousBackupsDescription']['PointInTimeRecoveryDescription']['PointInTimeRecoveryStatus'] == 'ENABLED'
            
            if not pitr_enabled:
                await self._enable_point_in_time_recovery(table_name)
            
            logger.debug(f"Verified configuration for table: {table_name}")
            
        except Exception as e:
            logger.warning(f"Error verifying table configuration: {e}")
    
    async def _enable_point_in_time_recovery(self, table_name: str) -> None:
        """Enable point-in-time recovery for table"""
        try:
            self.dynamodb_client.update_continuous_backups(
                TableName=table_name,
                PointInTimeRecoverySpecification={
                    'PointInTimeRecoveryEnabled': True
                }
            )
            logger.info(f"Enabled point-in-time recovery for {table_name}")
            
        except Exception as e:
            logger.warning(f"Could not enable point-in-time recovery for {table_name}: {e}")
    
    async def _tag_table(self, table_name: str) -> None:
        """Add tags to DynamoDB table"""
        try:
            # Get table ARN
            table_description = self.dynamodb_client.describe_table(TableName=table_name)
            table_arn = table_description['Table']['TableArn']
            
            # Add tags
            self.dynamodb_client.tag_resource(
                ResourceArn=table_arn,
                Tags=[
                    {'Key': 'Project', 'Value': 'Vismaya-DemandOps'},
                    {'Key': 'Component', 'Value': 'Agentic-AI'},
                    {'Key': 'Environment', 'Value': self.config.get('environment', 'development')},
                    {'Key': 'CreatedBy', 'Value': 'AWSDynamoDBManager'},
                    {'Key': 'CreatedAt', 'Value': datetime.now().isoformat()}
                ]
            )
            
            logger.debug(f"Tagged table: {table_name}")
            
        except Exception as e:
            logger.warning(f"Could not tag table {table_name}: {e}")
    
    async def setup_backup_and_recovery(self) -> Dict[str, bool]:
        """Setup backup and recovery mechanisms"""
        results = {}
        
        for table_key, table_def in self.table_definitions.items():
            table_name = table_def["table_name"]
            
            try:
                # Create on-demand backup
                backup_name = f"{table_name}-initial-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                
                backup_response = self.dynamodb_client.create_backup(
                    TableName=table_name,
                    BackupName=backup_name
                )
                
                logger.info(f"Created backup for {table_name}: {backup_name}")
                results[table_key] = True
                
            except Exception as e:
                logger.error(f"Error creating backup for {table_name}: {e}")
                results[table_key] = False
        
        return results
    
    def get_table_access_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Get optimized data access patterns for each table"""
        return {
            "agent_states": {
                "primary_access": "Query by agent_id",
                "secondary_access": "Query by status using GSI",
                "write_pattern": "Update agent state frequently",
                "read_pattern": "Read agent state for health checks and status updates"
            },
            "conversations": {
                "primary_access": "Query by thread_id with timestamp range",
                "secondary_access": "Query by sender using GSI",
                "write_pattern": "Append new messages to conversation threads",
                "read_pattern": "Read conversation history for context"
            },
            "decisions": {
                "primary_access": "Get decision by proposal_id",
                "secondary_access": "Query by status or category using GSI",
                "write_pattern": "Create proposals and update approval status",
                "read_pattern": "Read pending decisions and approval history"
            },
            "system_events": {
                "primary_access": "Query by event_date with timestamp range",
                "secondary_access": "Query by event_type or severity using GSI",
                "write_pattern": "Append system events as they occur",
                "read_pattern": "Read events for monitoring and debugging"
            },
            "context_data": {
                "primary_access": "Get latest context by context_id",
                "secondary_access": "Query by agent_id using GSI",
                "write_pattern": "Update context data with versioning",
                "read_pattern": "Read context for agent coordination"
            },
            "workflow_executions": {
                "primary_access": "Query by workflow_id",
                "secondary_access": "Query by status using GSI",
                "write_pattern": "Create workflow executions and update status",
                "read_pattern": "Read workflow status and execution history"
            }
        }
    
    async def create_data_access_layer(self) -> 'DynamoDBDataAccessLayer':
        """Create data access layer for simplified operations"""
        return DynamoDBDataAccessLayer(self.dynamodb_resource, self.table_definitions)
    
    async def get_table_metrics(self, hours: int = 24) -> Dict[str, Dict[str, Any]]:
        """Get CloudWatch metrics for DynamoDB tables"""
        try:
            cloudwatch = self.session.client('cloudwatch')
            end_time = datetime.now()
            start_time = datetime.now().replace(hour=end_time.hour - hours)
            
            metrics = {}
            
            for table_key, table_def in self.table_definitions.items():
                table_name = table_def["table_name"]
                
                try:
                    # Get consumed read capacity
                    read_capacity = cloudwatch.get_metric_statistics(
                        Namespace='AWS/DynamoDB',
                        MetricName='ConsumedReadCapacityUnits',
                        Dimensions=[{'Name': 'TableName', 'Value': table_name}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=3600,
                        Statistics=['Sum', 'Average']
                    )
                    
                    # Get consumed write capacity
                    write_capacity = cloudwatch.get_metric_statistics(
                        Namespace='AWS/DynamoDB',
                        MetricName='ConsumedWriteCapacityUnits',
                        Dimensions=[{'Name': 'TableName', 'Value': table_name}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=3600,
                        Statistics=['Sum', 'Average']
                    )
                    
                    # Get throttled requests
                    throttles = cloudwatch.get_metric_statistics(
                        Namespace='AWS/DynamoDB',
                        MetricName='ThrottledRequests',
                        Dimensions=[{'Name': 'TableName', 'Value': table_name}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=3600,
                        Statistics=['Sum']
                    )
                    
                    metrics[table_key] = {
                        "table_name": table_name,
                        "read_capacity": {
                            "total": sum(point['Sum'] for point in read_capacity['Datapoints']),
                            "average": sum(point['Average'] for point in read_capacity['Datapoints']) / max(len(read_capacity['Datapoints']), 1)
                        },
                        "write_capacity": {
                            "total": sum(point['Sum'] for point in write_capacity['Datapoints']),
                            "average": sum(point['Average'] for point in write_capacity['Datapoints']) / max(len(write_capacity['Datapoints']), 1)
                        },
                        "throttles": sum(point['Sum'] for point in throttles['Datapoints'])
                    }
                    
                except Exception as e:
                    logger.warning(f"Could not get metrics for {table_name}: {e}")
                    metrics[table_key] = {"error": str(e)}
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting table metrics: {e}")
            return {"error": str(e)}


class DynamoDBDataAccessLayer:
    """
    Simplified data access layer for DynamoDB operations
    Provides high-level methods for common operations
    """
    
    def __init__(self, dynamodb_resource, table_definitions: Dict[str, Any]):
        self.dynamodb = dynamodb_resource
        self.table_definitions = table_definitions
        self.tables = {}
        
        # Initialize table references
        for table_key, table_def in table_definitions.items():
            self.tables[table_key] = dynamodb_resource.Table(table_def["table_name"])
    
    async def store_agent_state(self, agent_id: str, state_data: Dict[str, Any]) -> bool:
        """Store agent state"""
        try:
            table = self.tables["agent_states"]
            
            item = {
                "agent_id": agent_id,
                "status": state_data.get("status", "unknown"),
                "last_updated": datetime.now().isoformat(),
                "state_data": json.dumps(state_data)
            }
            
            table.put_item(Item=item)
            return True
            
        except Exception as e:
            logger.error(f"Error storing agent state: {e}")
            return False
    
    async def get_agent_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent state"""
        try:
            table = self.tables["agent_states"]
            
            response = table.get_item(Key={"agent_id": agent_id})
            
            if "Item" in response:
                item = response["Item"]
                state_data = json.loads(item.get("state_data", "{}"))
                return {
                    "agent_id": item["agent_id"],
                    "status": item["status"],
                    "last_updated": item["last_updated"],
                    **state_data
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting agent state: {e}")
            return None
    
    async def store_conversation_message(self, thread_id: str, message_data: Dict[str, Any]) -> bool:
        """Store conversation message"""
        try:
            table = self.tables["conversations"]
            
            item = {
                "thread_id": thread_id,
                "timestamp": message_data.get("timestamp", datetime.now().isoformat()),
                "sender": message_data.get("sender", "unknown"),
                "recipient": message_data.get("recipient", "unknown"),
                "message_type": message_data.get("message_type", "unknown"),
                "content": json.dumps(message_data.get("content", {})),
                "correlation_id": message_data.get("correlation_id"),
                "metadata": json.dumps(message_data.get("metadata", {}))
            }
            
            table.put_item(Item=item)
            return True
            
        except Exception as e:
            logger.error(f"Error storing conversation message: {e}")
            return False
    
    async def get_conversation_history(self, thread_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history"""
        try:
            table = self.tables["conversations"]
            
            response = table.query(
                KeyConditionExpression="thread_id = :thread_id",
                ExpressionAttributeValues={":thread_id": thread_id},
                ScanIndexForward=False,  # Most recent first
                Limit=limit
            )
            
            messages = []
            for item in response.get("Items", []):
                message = {
                    "thread_id": item["thread_id"],
                    "timestamp": item["timestamp"],
                    "sender": item["sender"],
                    "recipient": item["recipient"],
                    "message_type": item["message_type"],
                    "content": json.loads(item.get("content", "{}")),
                    "correlation_id": item.get("correlation_id"),
                    "metadata": json.loads(item.get("metadata", "{}"))
                }
                messages.append(message)
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    async def store_decision_proposal(self, proposal_data: Dict[str, Any]) -> bool:
        """Store decision proposal"""
        try:
            table = self.tables["decisions"]
            
            item = {
                "proposal_id": proposal_data["proposal_id"],
                "status": proposal_data.get("status", "pending"),
                "created_at": proposal_data.get("created_at", datetime.now().isoformat()),
                "created_by": proposal_data.get("created_by", "unknown"),
                "category": proposal_data.get("category", "general"),
                "title": proposal_data.get("title", ""),
                "description": proposal_data.get("description", ""),
                "proposal_data": json.dumps(proposal_data)
            }
            
            table.put_item(Item=item)
            return True
            
        except Exception as e:
            logger.error(f"Error storing decision proposal: {e}")
            return False
    
    async def get_decision_proposal(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """Get decision proposal"""
        try:
            table = self.tables["decisions"]
            
            response = table.get_item(Key={"proposal_id": proposal_id})
            
            if "Item" in response:
                item = response["Item"]
                proposal_data = json.loads(item.get("proposal_data", "{}"))
                return {
                    "proposal_id": item["proposal_id"],
                    "status": item["status"],
                    "created_at": item["created_at"],
                    "created_by": item["created_by"],
                    "category": item["category"],
                    **proposal_data
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting decision proposal: {e}")
            return None
    
    async def store_system_event(self, event_data: Dict[str, Any]) -> bool:
        """Store system event"""
        try:
            table = self.tables["system_events"]
            
            timestamp = event_data.get("timestamp", datetime.now().isoformat())
            event_date = timestamp.split("T")[0]  # Extract date part
            
            item = {
                "event_date": event_date,
                "timestamp": timestamp,
                "event_type": event_data.get("event_type", "unknown"),
                "source": event_data.get("source", "unknown"),
                "severity": event_data.get("severity", "info"),
                "event_data": json.dumps(event_data)
            }
            
            table.put_item(Item=item)
            return True
            
        except Exception as e:
            logger.error(f"Error storing system event: {e}")
            return False
    
    async def get_system_events(
        self, 
        event_date: str, 
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get system events"""
        try:
            table = self.tables["system_events"]
            
            if event_type:
                # Query by event type using GSI
                response = table.query(
                    IndexName="event-type-timestamp-index",
                    KeyConditionExpression="event_type = :event_type",
                    ExpressionAttributeValues={":event_type": event_type},
                    ScanIndexForward=False,
                    Limit=limit
                )
            else:
                # Query by date
                response = table.query(
                    KeyConditionExpression="event_date = :event_date",
                    ExpressionAttributeValues={":event_date": event_date},
                    ScanIndexForward=False,
                    Limit=limit
                )
            
            events = []
            for item in response.get("Items", []):
                event = {
                    "event_date": item["event_date"],
                    "timestamp": item["timestamp"],
                    "event_type": item["event_type"],
                    "source": item["source"],
                    "severity": item["severity"],
                    **json.loads(item.get("event_data", "{}"))
                }
                events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting system events: {e}")
            return []