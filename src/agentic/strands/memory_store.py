"""
Memory Store implementation for Strands framework
Persistent storage using AWS DynamoDB for agent conversations, decisions, and state
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from ..core.interfaces import IMemoryStore
from ..core.models import (
    AgentMessage, AgentState, DecisionProposal, SystemEvent,
    MemoryStoreError
)


class DynamoDBMemoryStore(IMemoryStore):
    """
    DynamoDB-based memory store for persistent agent data
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # DynamoDB configuration
        self.region = config.get("aws_region", "us-east-1")
        self.table_prefix = config.get("table_prefix", "vismaya-agentic")
        
        # Table names
        self.tables = {
            "conversations": f"{self.table_prefix}-conversations",
            "decisions": f"{self.table_prefix}-decisions",
            "agent_states": f"{self.table_prefix}-agent-states",
            "system_events": f"{self.table_prefix}-system-events"
        }
        
        # Initialize DynamoDB client
        try:
            self.dynamodb = boto3.resource('dynamodb', region_name=self.region)
            self.dynamodb_client = boto3.client('dynamodb', region_name=self.region)
        except NoCredentialsError:
            self.logger.error("AWS credentials not found")
            raise MemoryStoreError("AWS credentials not configured")
        
        # Table references
        self.table_refs = {}
        
        # Initialize tables
        self._initialize_tables()
    
    def _initialize_tables(self) -> None:
        """Initialize DynamoDB tables"""
        try:
            # Check if tables exist and create if necessary
            for table_type, table_name in self.tables.items():
                try:
                    table = self.dynamodb.Table(table_name)
                    table.load()  # This will raise an exception if table doesn't exist
                    self.table_refs[table_type] = table
                    self.logger.info(f"Connected to existing table: {table_name}")
                    
                except ClientError as e:
                    if e.response['Error']['Code'] == 'ResourceNotFoundException':
                        # Table doesn't exist, create it
                        self._create_table(table_type, table_name)
                    else:
                        raise
            
        except Exception as e:
            self.logger.error(f"Error initializing DynamoDB tables: {e}")
            raise MemoryStoreError(f"Failed to initialize tables: {e}")
    
    def _create_table(self, table_type: str, table_name: str) -> None:
        """Create DynamoDB table based on type"""
        try:
            if table_type == "conversations":
                table = self.dynamodb.create_table(
                    TableName=table_name,
                    KeySchema=[
                        {'AttributeName': 'thread_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'thread_id', 'AttributeType': 'S'},
                        {'AttributeName': 'timestamp', 'AttributeType': 'S'}
                    ],
                    BillingMode='PAY_PER_REQUEST'
                )
                
            elif table_type == "decisions":
                table = self.dynamodb.create_table(
                    TableName=table_name,
                    KeySchema=[
                        {'AttributeName': 'proposal_id', 'KeyType': 'HASH'}
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'proposal_id', 'AttributeType': 'S'},
                        {'AttributeName': 'created_by', 'AttributeType': 'S'},
                        {'AttributeName': 'status', 'AttributeType': 'S'}
                    ],
                    GlobalSecondaryIndexes=[
                        {
                            'IndexName': 'CreatedByIndex',
                            'KeySchema': [
                                {'AttributeName': 'created_by', 'KeyType': 'HASH'},
                                {'AttributeName': 'proposal_id', 'KeyType': 'RANGE'}
                            ],
                            'Projection': {'ProjectionType': 'ALL'}
                        },
                        {
                            'IndexName': 'StatusIndex',
                            'KeySchema': [
                                {'AttributeName': 'status', 'KeyType': 'HASH'},
                                {'AttributeName': 'proposal_id', 'KeyType': 'RANGE'}
                            ],
                            'Projection': {'ProjectionType': 'ALL'}
                        }
                    ],
                    BillingMode='PAY_PER_REQUEST'
                )
                
            elif table_type == "agent_states":
                table = self.dynamodb.create_table(
                    TableName=table_name,
                    KeySchema=[
                        {'AttributeName': 'agent_id', 'KeyType': 'HASH'}
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'agent_id', 'AttributeType': 'S'}
                    ],
                    BillingMode='PAY_PER_REQUEST'
                )
                
            elif table_type == "system_events":
                table = self.dynamodb.create_table(
                    TableName=table_name,
                    KeySchema=[
                        {'AttributeName': 'event_type', 'KeyType': 'HASH'},
                        {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'event_type', 'AttributeType': 'S'},
                        {'AttributeName': 'timestamp', 'AttributeType': 'S'}
                    ],
                    BillingMode='PAY_PER_REQUEST'
                )
            
            # Wait for table to be created
            table.wait_until_exists()
            self.table_refs[table_type] = table
            self.logger.info(f"Created table: {table_name}")
            
        except Exception as e:
            self.logger.error(f"Error creating table {table_name}: {e}")
            raise MemoryStoreError(f"Failed to create table {table_name}: {e}")
    
    async def store_conversation(self, thread_id: str, message: AgentMessage) -> bool:
        """Store conversation message with full context"""
        try:
            table = self.table_refs["conversations"]
            
            item = {
                'thread_id': thread_id,
                'timestamp': message.timestamp.isoformat(),
                'message_id': message.correlation_id,
                'sender': message.sender,
                'recipient': message.recipient,
                'message_type': message.message_type.value,
                'content': json.dumps(message.content),
                'priority': message.priority,
                'requires_response': message.requires_response,
                'metadata': json.dumps(message.metadata),
                'ttl': int((datetime.now() + timedelta(days=365)).timestamp())  # 1 year TTL
            }
            
            table.put_item(Item=item)
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing conversation message: {e}")
            return False
    
    async def retrieve_conversation_history(self, thread_id: str, limit: int = 50) -> List[AgentMessage]:
        """Retrieve conversation history for context"""
        try:
            table = self.table_refs["conversations"]
            
            response = table.query(
                KeyConditionExpression='thread_id = :thread_id',
                ExpressionAttributeValues={':thread_id': thread_id},
                ScanIndexForward=False,  # Most recent first
                Limit=limit
            )
            
            messages = []
            for item in response['Items']:
                try:
                    message = AgentMessage(
                        sender=item['sender'],
                        recipient=item['recipient'],
                        message_type=item['message_type'],
                        content=json.loads(item['content']),
                        timestamp=datetime.fromisoformat(item['timestamp']),
                        correlation_id=item['message_id'],
                        priority=item.get('priority', 'normal'),
                        requires_response=item.get('requires_response', False),
                        metadata=json.loads(item.get('metadata', '{}'))
                    )
                    messages.append(message)
                    
                except Exception as e:
                    self.logger.error(f"Error parsing message from DynamoDB: {e}")
                    continue
            
            # Return in chronological order (oldest first)
            return list(reversed(messages))
            
        except Exception as e:
            self.logger.error(f"Error retrieving conversation history: {e}")
            return []
    
    async def store_agent_state(self, agent_id: str, state: AgentState) -> bool:
        """Store agent state"""
        try:
            table = self.table_refs["agent_states"]
            
            item = {
                'agent_id': agent_id,
                'status': state.status.value,
                'current_task': state.current_task,
                'context': json.dumps(state.context),
                'last_updated': state.last_updated.isoformat(),
                'performance_metrics': json.dumps(state.performance_metrics),
                'error_count': state.error_count,
                'last_error': state.last_error,
                'uptime_seconds': state.uptime_seconds,
                'memory_usage_mb': state.memory_usage_mb,
                'cpu_usage_percent': state.cpu_usage_percent,
                'ttl': int((datetime.now() + timedelta(days=30)).timestamp())  # 30 days TTL
            }
            
            table.put_item(Item=item)
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing agent state: {e}")
            return False
    
    async def retrieve_agent_state(self, agent_id: str) -> Optional[AgentState]:
        """Retrieve agent state"""
        try:
            table = self.table_refs["agent_states"]
            
            response = table.get_item(Key={'agent_id': agent_id})
            
            if 'Item' not in response:
                return None
            
            item = response['Item']
            
            state = AgentState(
                agent_id=agent_id,
                status=item['status'],
                current_task=item.get('current_task'),
                context=json.loads(item.get('context', '{}')),
                last_updated=datetime.fromisoformat(item['last_updated']),
                performance_metrics=json.loads(item.get('performance_metrics', '{}')),
                error_count=item.get('error_count', 0),
                last_error=item.get('last_error'),
                uptime_seconds=item.get('uptime_seconds', 0.0),
                memory_usage_mb=item.get('memory_usage_mb', 0.0),
                cpu_usage_percent=item.get('cpu_usage_percent', 0.0)
            )
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error retrieving agent state: {e}")
            return None
    
    async def store_decision_proposal(self, proposal: DecisionProposal) -> bool:
        """Store decision proposal"""
        try:
            table = self.table_refs["decisions"]
            
            item = {
                'proposal_id': proposal.proposal_id,
                'title': proposal.title,
                'description': proposal.description,
                'created_by': proposal.created_by,
                'created_at': proposal.created_at.isoformat(),
                'status': proposal.status.value,
                'estimated_cost_impact': proposal.estimated_cost_impact,
                'risk_level': proposal.risk_level.value,
                'required_approvers': json.dumps(proposal.required_approvers),
                'recommendations': json.dumps(proposal.recommendations),
                'approval_responses': json.dumps([
                    {**response, 'timestamp': response.get('timestamp', datetime.now().isoformat())}
                    for response in proposal.approval_responses
                ]),
                'execution_plan': json.dumps(proposal.execution_plan),
                'metadata': json.dumps(proposal.metadata),
                'approval_deadline': proposal.approval_deadline.isoformat() if proposal.approval_deadline else None,
                'ttl': int((datetime.now() + timedelta(days=365)).timestamp())  # 1 year TTL
            }
            
            # Add impact analysis if present
            if proposal.impact_analysis:
                item['impact_analysis'] = json.dumps({
                    'cost_impact': proposal.impact_analysis.cost_impact,
                    'risk_assessment': proposal.impact_analysis.risk_assessment.value,
                    'affected_resources': proposal.impact_analysis.affected_resources,
                    'timeline_impact': proposal.impact_analysis.timeline_impact,
                    'rollback_plan': proposal.impact_analysis.rollback_plan,
                    'success_metrics': proposal.impact_analysis.success_metrics,
                    'stakeholder_impact': proposal.impact_analysis.stakeholder_impact,
                    'compliance_considerations': proposal.impact_analysis.compliance_considerations
                })
            
            table.put_item(Item=item)
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing decision proposal: {e}")
            return False
    
    async def retrieve_decision_proposal(self, proposal_id: str) -> Optional[DecisionProposal]:
        """Retrieve decision proposal"""
        try:
            table = self.table_refs["decisions"]
            
            response = table.get_item(Key={'proposal_id': proposal_id})
            
            if 'Item' not in response:
                return None
            
            item = response['Item']
            
            # Create decision proposal
            proposal = DecisionProposal(
                proposal_id=item['proposal_id'],
                title=item['title'],
                description=item['description'],
                created_by=item['created_by'],
                created_at=datetime.fromisoformat(item['created_at']),
                status=item['status'],
                estimated_cost_impact=item.get('estimated_cost_impact', 0.0),
                risk_level=item.get('risk_level', 'low'),
                required_approvers=json.loads(item.get('required_approvers', '[]')),
                recommendations=json.loads(item.get('recommendations', '[]')),
                approval_responses=json.loads(item.get('approval_responses', '[]')),
                execution_plan=json.loads(item.get('execution_plan', '{}')),
                metadata=json.loads(item.get('metadata', '{}')),
                approval_deadline=datetime.fromisoformat(item['approval_deadline']) if item.get('approval_deadline') else None
            )
            
            # Add impact analysis if present
            if 'impact_analysis' in item:
                impact_data = json.loads(item['impact_analysis'])
                from ..core.models import DecisionImpactAnalysis, RiskLevel
                
                proposal.impact_analysis = DecisionImpactAnalysis(
                    cost_impact=impact_data.get('cost_impact', 0.0),
                    risk_assessment=RiskLevel(impact_data.get('risk_assessment', 'low')),
                    affected_resources=impact_data.get('affected_resources', []),
                    timeline_impact=impact_data.get('timeline_impact', ''),
                    rollback_plan=impact_data.get('rollback_plan'),
                    success_metrics=impact_data.get('success_metrics', []),
                    stakeholder_impact=impact_data.get('stakeholder_impact', {}),
                    compliance_considerations=impact_data.get('compliance_considerations', [])
                )
            
            return proposal
            
        except Exception as e:
            self.logger.error(f"Error retrieving decision proposal: {e}")
            return None
    
    async def query_decisions_by_criteria(self, criteria: Dict[str, Any]) -> List[DecisionProposal]:
        """Query decisions by specific criteria with enhanced similarity matching"""
        try:
            table = self.table_refs["decisions"]
            decisions = []
            
            # Handle different query types
            if 'created_by' in criteria:
                # Query by creator
                response = table.query(
                    IndexName='CreatedByIndex',
                    KeyConditionExpression='created_by = :created_by',
                    ExpressionAttributeValues={':created_by': criteria['created_by']},
                    Limit=criteria.get('limit', 50)
                )
                
                for item in response['Items']:
                    decision = await self.retrieve_decision_proposal(item['proposal_id'])
                    if decision:
                        decisions.append(decision)
            
            elif 'status' in criteria:
                # Query by status
                response = table.query(
                    IndexName='StatusIndex',
                    KeyConditionExpression='status = :status',
                    ExpressionAttributeValues={':status': criteria['status']},
                    Limit=criteria.get('limit', 50)
                )
                
                for item in response['Items']:
                    decision = await self.retrieve_decision_proposal(item['proposal_id'])
                    if decision:
                        decisions.append(decision)
            
            else:
                # Scan table with filters (less efficient)
                scan_kwargs = {'Limit': criteria.get('limit', 50)}
                
                # Add filters
                filter_expressions = []
                expression_values = {}
                
                if 'cost_range' in criteria:
                    cost_range = criteria['cost_range']
                    if 'min' in cost_range:
                        filter_expressions.append('estimated_cost_impact >= :min_cost')
                        expression_values[':min_cost'] = cost_range['min']
                    if 'max' in cost_range:
                        filter_expressions.append('estimated_cost_impact <= :max_cost')
                        expression_values[':max_cost'] = cost_range['max']
                
                if 'risk_level' in criteria:
                    filter_expressions.append('risk_level = :risk_level')
                    expression_values[':risk_level'] = criteria['risk_level']
                
                if 'created_after' in criteria:
                    filter_expressions.append('created_at >= :created_after')
                    expression_values[':created_after'] = criteria['created_after']
                
                if 'created_before' in criteria:
                    filter_expressions.append('created_at <= :created_before')
                    expression_values[':created_before'] = criteria['created_before']
                
                if 'title_contains' in criteria:
                    filter_expressions.append('contains(title, :title_text)')
                    expression_values[':title_text'] = criteria['title_contains']
                
                if 'description_contains' in criteria:
                    filter_expressions.append('contains(description, :desc_text)')
                    expression_values[':desc_text'] = criteria['description_contains']
                
                if filter_expressions:
                    scan_kwargs['FilterExpression'] = ' AND '.join(filter_expressions)
                    scan_kwargs['ExpressionAttributeValues'] = expression_values
                
                response = table.scan(**scan_kwargs)
                
                for item in response['Items']:
                    decision = await self.retrieve_decision_proposal(item['proposal_id'])
                    if decision:
                        decisions.append(decision)
            
            # Apply additional filtering for similarity matching
            if 'similarity_to' in criteria:
                reference_decision = criteria['similarity_to']
                scored_decisions = []
                
                for decision in decisions:
                    similarity_score = self._calculate_decision_similarity(reference_decision, decision)
                    if similarity_score >= criteria.get('min_similarity', 0.3):
                        scored_decisions.append((similarity_score, decision))
                
                # Sort by similarity score and return top matches
                scored_decisions.sort(key=lambda x: x[0], reverse=True)
                decisions = [decision for _, decision in scored_decisions[:criteria.get('max_similar', 10)]]
            
            return decisions
            
        except Exception as e:
            self.logger.error(f"Error querying decisions by criteria: {e}")
            return []
    
    async def store_system_event(self, event: SystemEvent) -> bool:
        """Store system event"""
        try:
            table = self.table_refs["system_events"]
            
            item = {
                'event_type': event.event_type,
                'timestamp': event.timestamp.isoformat(),
                'event_id': event.event_id,
                'source': event.source,
                'data': json.dumps(event.data),
                'severity': event.severity,
                'affected_agents': json.dumps(event.affected_agents),
                'requires_action': event.requires_action,
                'ttl': int((datetime.now() + timedelta(days=90)).timestamp())  # 90 days TTL
            }
            
            table.put_item(Item=item)
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing system event: {e}")
            return False
    
    async def get_system_events(self, event_type: Optional[str] = None, limit: int = 100) -> List[SystemEvent]:
        """Get system events by type"""
        try:
            table = self.table_refs["system_events"]
            events = []
            
            if event_type:
                # Query by event type
                response = table.query(
                    KeyConditionExpression='event_type = :event_type',
                    ExpressionAttributeValues={':event_type': event_type},
                    ScanIndexForward=False,  # Most recent first
                    Limit=limit
                )
            else:
                # Scan all events (less efficient)
                response = table.scan(Limit=limit)
            
            for item in response['Items']:
                try:
                    event = SystemEvent(
                        event_id=item['event_id'],
                        event_type=item['event_type'],
                        source=item['source'],
                        data=json.loads(item['data']),
                        timestamp=datetime.fromisoformat(item['timestamp']),
                        severity=item.get('severity', 'info'),
                        affected_agents=json.loads(item.get('affected_agents', '[]')),
                        requires_action=item.get('requires_action', False)
                    )
                    events.append(event)
                    
                except Exception as e:
                    self.logger.error(f"Error parsing system event from DynamoDB: {e}")
                    continue
            
            return events
            
        except Exception as e:
            self.logger.error(f"Error retrieving system events: {e}")
            return []
    
    def _calculate_decision_similarity(self, decision1: DecisionProposal, decision2: DecisionProposal) -> float:
        """Calculate similarity score between two decisions"""
        try:
            similarity_score = 0.0
            
            # Cost similarity (40% weight)
            cost_diff = abs(decision1.estimated_cost_impact - decision2.estimated_cost_impact)
            max_cost = max(decision1.estimated_cost_impact, decision2.estimated_cost_impact, 1.0)  # Avoid division by zero
            cost_similarity = 1 - (cost_diff / max_cost)
            similarity_score += cost_similarity * 0.4
            
            # Risk level similarity (30% weight)
            if decision1.risk_level == decision2.risk_level:
                similarity_score += 0.3
            
            # Creator similarity (20% weight)
            if decision1.created_by == decision2.created_by:
                similarity_score += 0.2
            
            # Title/description similarity (10% weight)
            title_similarity = self._calculate_text_similarity(decision1.title, decision2.title)
            desc_similarity = self._calculate_text_similarity(decision1.description, decision2.description)
            text_similarity = (title_similarity + desc_similarity) / 2
            similarity_score += text_similarity * 0.1
            
            return min(similarity_score, 1.0)  # Cap at 1.0
            
        except Exception as e:
            self.logger.error(f"Error calculating decision similarity: {e}")
            return 0.0
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using Jaccard similarity"""
        try:
            if not text1 or not text2:
                return 0.0
            
            # Convert to lowercase and split into words
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            
            # Calculate Jaccard similarity
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            if not union:
                return 0.0
            
            return len(intersection) / len(union)
            
        except Exception as e:
            self.logger.error(f"Error calculating text similarity: {e}")
            return 0.0
    
    async def get_conversation_analytics(self, thread_id: str) -> Dict[str, Any]:
        """Get analytics for conversation thread"""
        try:
            history = await self.retrieve_conversation_history(thread_id, limit=1000)
            
            if not history:
                return {"error": "No conversation history found"}
            
            # Calculate analytics
            analytics = {
                "total_messages": len(history),
                "participants": list(set(msg.sender for msg in history)),
                "message_types": {},
                "activity_timeline": {},
                "average_response_time": 0.0,
                "conversation_duration": 0.0
            }
            
            # Message type distribution
            for msg in history:
                msg_type = msg.message_type.value
                analytics["message_types"][msg_type] = analytics["message_types"].get(msg_type, 0) + 1
            
            # Activity timeline (messages per hour)
            for msg in history:
                hour_key = msg.timestamp.strftime("%Y-%m-%d %H:00")
                analytics["activity_timeline"][hour_key] = analytics["activity_timeline"].get(hour_key, 0) + 1
            
            # Calculate conversation duration
            if len(history) > 1:
                start_time = min(msg.timestamp for msg in history)
                end_time = max(msg.timestamp for msg in history)
                analytics["conversation_duration"] = (end_time - start_time).total_seconds()
            
            # Calculate average response time (simplified)
            response_times = []
            for i in range(1, len(history)):
                if history[i].sender != history[i-1].sender:  # Different sender = response
                    time_diff = (history[i].timestamp - history[i-1].timestamp).total_seconds()
                    if time_diff < 3600:  # Only consider responses within 1 hour
                        response_times.append(time_diff)
            
            if response_times:
                analytics["average_response_time"] = sum(response_times) / len(response_times)
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"Error getting conversation analytics: {e}")
            return {"error": str(e)}
    
    async def cleanup_old_data(self, retention_days: int = 365) -> Dict[str, int]:
        """Clean up old data based on retention policy"""
        try:
            cleanup_stats = {
                "conversations_cleaned": 0,
                "decisions_cleaned": 0,
                "agent_states_cleaned": 0,
                "system_events_cleaned": 0
            }
            
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            cutoff_timestamp = int(cutoff_date.timestamp())
            
            # Clean up old conversations (using TTL, so this is mostly for manual cleanup)
            conversations_table = self.table_refs["conversations"]
            
            # Scan for old conversations
            response = conversations_table.scan(
                FilterExpression='#ttl < :cutoff',
                ExpressionAttributeNames={'#ttl': 'ttl'},
                ExpressionAttributeValues={':cutoff': cutoff_timestamp}
            )
            
            # Delete old conversations
            with conversations_table.batch_writer() as batch:
                for item in response['Items']:
                    batch.delete_item(
                        Key={
                            'thread_id': item['thread_id'],
                            'timestamp': item['timestamp']
                        }
                    )
                    cleanup_stats["conversations_cleaned"] += 1
            
            # Similar cleanup for other tables...
            # (Implementation would be similar for decisions, agent_states, system_events)
            
            self.logger.info(f"Cleanup completed: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            self.logger.error(f"Error during data cleanup: {e}")
            return {"error": str(e)}
    
    def get_memory_store_stats(self) -> Dict[str, Any]:
        """Get memory store statistics"""
        try:
            stats = {
                "tables": {},
                "region": self.region,
                "table_prefix": self.table_prefix
            }
            
            # Get table statistics
            for table_type, table_name in self.tables.items():
                try:
                    table = self.table_refs.get(table_type)
                    if table:
                        table.reload()
                        stats["tables"][table_type] = {
                            "table_name": table_name,
                            "item_count": table.item_count,
                            "table_size_bytes": table.table_size_bytes,
                            "status": table.table_status
                        }
                except Exception as e:
                    stats["tables"][table_type] = {"error": str(e)}
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting memory store stats: {e}")
            return {"error": str(e)}