"""
User Interface Agent
Autonomous agent for enhanced user interaction management, natural language processing, and multi-modal responses
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json
import re

from ..core.base_agent import BaseAgent
from ..core.interfaces import ISpecializedAgent, IStrandsFramework, IMCPServer
from ..core.models import (
    AgentCapability, DecisionProposal, AgentMessage, MessageType,
    SystemEvent, SystemEventType
)


class UserInterfaceAgent(BaseAgent, ISpecializedAgent):
    """
    Specialized agent for user interface management with enhanced capabilities:
    - Advanced natural language processing and context-aware conversation management
    - Multi-modal response generation and user preference learning
    - Seamless integration between traditional UI and conversational AI interfaces
    """
    
    def __init__(
        self,
        strands_framework: Optional[IStrandsFramework] = None,
        mcp_server: Optional[IMCPServer] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        # Define agent capabilities
        capabilities = [
            AgentCapability(
                name="process_natural_language",
                description="Process and understand natural language queries from users",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "context": {"type": "object"},
                        "user_preferences": {"type": "object"}
                    }
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "intent": {"type": "string"},
                        "entities": {"type": "array"},
                        "confidence": {"type": "number"},
                        "suggested_actions": {"type": "array"}
                    }
                },
                required_permissions=["bedrock:InvokeModel"]
            ),
            AgentCapability(
                name="generate_multimodal_responses",
                description="Generate responses in multiple formats (text, charts, tables, etc.)",
                input_schema={
                    "type": "object",
                    "properties": {
                        "content": {"type": "object"},
                        "response_format": {"type": "string"},
                        "user_context": {"type": "object"}
                    }
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "response": {"type": "object"},
                        "format": {"type": "string"},
                        "interactive_elements": {"type": "array"}
                    }
                },
                required_permissions=["bedrock:InvokeModel"]
            ),
            AgentCapability(
                name="manage_conversation_context",
                description="Manage conversation context and maintain dialogue state",
                input_schema={
                    "type": "object",
                    "properties": {
                        "conversation_id": {"type": "string"},
                        "message_history": {"type": "array"},
                        "user_profile": {"type": "object"}
                    }
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "context_summary": {"type": "object"},
                        "next_actions": {"type": "array"},
                        "conversation_state": {"type": "string"}
                    }
                },
                required_permissions=["dynamodb:*"]
            ),
            AgentCapability(
                name="personalize_user_experience",
                description="Learn and adapt to user preferences and behavior patterns",
                input_schema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "interaction_history": {"type": "array"},
                        "preferences": {"type": "object"}
                    }
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "personalization_profile": {"type": "object"},
                        "recommended_actions": {"type": "array"},
                        "ui_customizations": {"type": "object"}
                    }
                },
                required_permissions=["dynamodb:*"]
            )
        ]
        
        # Default configuration
        default_config = {
            "supported_languages": ["en", "es", "fr", "de"],
            "response_formats": ["text", "chart", "table", "dashboard", "interactive"],
            "conversation_timeout_minutes": 30,
            "max_conversation_history": 50,
            "personalization_enabled": True,
            "nlp_confidence_threshold": 0.7,
            "supported_intents": [
                "cost_query", "forecast_request", "alert_management", 
                "resource_optimization", "dashboard_navigation", "help_request"
            ]
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(
            agent_id="user_interface_agent",
            agent_type="user_interface",
            capabilities=capabilities,
            config=default_config,
            strands_framework=strands_framework,
            mcp_server=mcp_server
        )
        
        # UI agent specific state
        self.active_conversations = {}
        self.user_profiles = {}
        self.conversation_contexts = {}
        self.response_templates = {}
        self.intent_patterns = {}
        self.personalization_data = {}
        
        # Setup specialized handlers
        self._setup_ui_agent_handlers()
    
    @property
    def domain(self) -> str:
        """Get agent domain"""
        return "user_interface"
    
    def _setup_ui_agent_handlers(self) -> None:
        """Setup UI agent specific message and action handlers"""
        # Add specialized action handlers
        self.action_handlers.update({
            "process_natural_language": self._action_process_natural_language,
            "generate_multimodal_responses": self._action_generate_multimodal_responses,
            "manage_conversation_context": self._action_manage_conversation_context,
            "personalize_user_experience": self._action_personalize_user_experience,
            "handle_user_query": self._action_handle_user_query,
            "update_user_preferences": self._action_update_user_preferences,
            "get_conversation_history": self._action_get_conversation_history,
            "create_dashboard_view": self._action_create_dashboard_view
        })
        
        # Add specialized message handlers
        self.message_handlers.update({
            "user_query": self._handle_user_query,
            "dashboard_request": self._handle_dashboard_request,
            "preference_update": self._handle_preference_update,
            "conversation_timeout": self._handle_conversation_timeout
        })
    
    async def _agent_specific_initialization(self) -> None:
        """Initialize UI agent specific components"""
        try:
            self.logger.info("Initializing user interface agent components")
            
            # Initialize NLP patterns and intents
            await self._initialize_nlp_patterns()
            
            # Initialize response templates
            await self._initialize_response_templates()
            
            # Load user profiles and preferences
            await self._load_user_profiles()
            
            # Start background tasks
            asyncio.create_task(self._conversation_management_loop())
            asyncio.create_task(self._personalization_learning_loop())
            asyncio.create_task(self._context_cleanup_loop())
            
            self.logger.info("User interface agent initialization completed")
            
        except Exception as e:
            self.logger.error(f"Error in UI agent initialization: {e}")
            raise
    
    async def analyze_domain_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user interface domain data"""
        try:
            user_interactions = data.get("user_interactions", [])
            conversation_data = data.get("conversation_data", {})
            user_feedback = data.get("user_feedback", [])
            
            # Analyze user interaction patterns
            interaction_patterns = await self._analyze_interaction_patterns(user_interactions)
            
            # Analyze conversation effectiveness
            conversation_analysis = await self._analyze_conversation_effectiveness(conversation_data)
            
            # Analyze user satisfaction and feedback
            satisfaction_analysis = await self._analyze_user_satisfaction(user_feedback)
            
            # Identify personalization opportunities
            personalization_opportunities = await self._identify_personalization_opportunities(user_interactions)
            
            return {
                "interaction_patterns": interaction_patterns,
                "conversation_analysis": conversation_analysis,
                "satisfaction_analysis": satisfaction_analysis,
                "personalization_opportunities": personalization_opportunities,
                "timestamp": datetime.now().isoformat(),
                "interactions_analyzed": len(user_interactions)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing UI domain data: {e}")
            raise
    
    async def generate_recommendations(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate user interface improvement recommendations"""
        try:
            interaction_data = context.get("interaction_data", {})
            user_feedback = context.get("user_feedback", [])
            performance_metrics = context.get("performance_metrics", {})
            
            recommendations = []
            
            # Generate UX improvement recommendations
            ux_recs = await self._generate_ux_recommendations(interaction_data, user_feedback)
            recommendations.extend(ux_recs)
            
            # Generate personalization recommendations
            personalization_recs = await self._generate_personalization_recommendations(interaction_data)
            recommendations.extend(personalization_recs)
            
            # Generate conversation flow recommendations
            conversation_recs = await self._generate_conversation_recommendations(interaction_data)
            recommendations.extend(conversation_recs)
            
            # Generate accessibility recommendations
            accessibility_recs = await self._generate_accessibility_recommendations(user_feedback)
            recommendations.extend(accessibility_recs)
            
            # Sort by user impact and implementation feasibility
            recommendations.sort(key=lambda x: (x.get("user_impact_score", 0), x.get("feasibility_score", 0)), reverse=True)
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return []
    
    async def create_decision_proposal(self, recommendation: Dict[str, Any]) -> DecisionProposal:
        """Create decision proposal from UI improvement recommendation"""
        try:
            # Calculate impact analysis
            impact_analysis = await self._calculate_ui_recommendation_impact(recommendation)
            
            # Determine required approvers
            required_approvers = self._determine_required_approvers(impact_analysis, recommendation)
            
            # Create proposal
            proposal = DecisionProposal(
                proposal_id=f"ui_improvement_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                title=recommendation.get("title", "UI Improvement Recommendation"),
                description=recommendation.get("description", ""),
                impact_analysis=impact_analysis,
                recommendations=[recommendation.get("action", "")],
                required_approvers=required_approvers,
                created_by=self.agent_id,
                created_at=datetime.now(),
                status="pending",
                approval_deadline=datetime.now() + timedelta(days=14),
                estimated_cost_impact=impact_analysis.get("development_cost", 0),
                risk_level=recommendation.get("risk_level", "low")
            )
            
            # Store proposal in memory
            if self.strands_framework:
                await self.strands_framework.store_decision_history(proposal)
            
            return proposal
            
        except Exception as e:
            self.logger.error(f"Error creating decision proposal: {e}")
            raise
    
    # Action handlers
    async def _action_process_natural_language(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Process natural language action"""
        try:
            query = parameters.get("query", "")
            context = parameters.get("context", {})
            user_preferences = parameters.get("user_preferences", {})
            
            # Extract intent from query
            intent = await self._extract_intent(query)
            
            # Extract entities
            entities = await self._extract_entities(query, intent)
            
            # Calculate confidence
            confidence = await self._calculate_nlp_confidence(query, intent, entities)
            
            # Generate suggested actions
            suggested_actions = await self._generate_suggested_actions(intent, entities, context)
            
            return {
                "success": True,
                "intent": intent,
                "entities": entities,
                "confidence": confidence,
                "suggested_actions": suggested_actions,
                "query_processed": query
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _action_generate_multimodal_responses(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate multimodal responses action"""
        try:
            content = parameters.get("content", {})
            response_format = parameters.get("response_format", "text")
            user_context = parameters.get("user_context", {})
            
            # Generate response based on format
            if response_format == "text":
                response = await self._generate_text_response(content, user_context)
            elif response_format == "chart":
                response = await self._generate_chart_response(content, user_context)
            elif response_format == "table":
                response = await self._generate_table_response(content, user_context)
            elif response_format == "dashboard":
                response = await self._generate_dashboard_response(content, user_context)
            else:
                response = await self._generate_text_response(content, user_context)
            
            # Add interactive elements
            interactive_elements = await self._generate_interactive_elements(content, response_format)
            
            return {
                "success": True,
                "response": response,
                "format": response_format,
                "interactive_elements": interactive_elements
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _action_manage_conversation_context(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Manage conversation context action"""
        try:
            conversation_id = parameters.get("conversation_id")
            message_history = parameters.get("message_history", [])
            user_profile = parameters.get("user_profile", {})
            
            if not conversation_id:
                conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Update conversation context
            context_summary = await self._update_conversation_context(conversation_id, message_history, user_profile)
            
            # Determine next actions
            next_actions = await self._determine_next_actions(context_summary, message_history)
            
            # Update conversation state
            conversation_state = await self._update_conversation_state(conversation_id, context_summary)
            
            return {
                "success": True,
                "conversation_id": conversation_id,
                "context_summary": context_summary,
                "next_actions": next_actions,
                "conversation_state": conversation_state
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _action_personalize_user_experience(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Personalize user experience action"""
        try:
            user_id = parameters.get("user_id")
            interaction_history = parameters.get("interaction_history", [])
            preferences = parameters.get("preferences", {})
            
            if not user_id:
                return {"success": False, "error": "user_id is required"}
            
            # Update personalization profile
            personalization_profile = await self._update_personalization_profile(user_id, interaction_history, preferences)
            
            # Generate recommended actions
            recommended_actions = await self._generate_personalized_recommendations(user_id, personalization_profile)
            
            # Generate UI customizations
            ui_customizations = await self._generate_ui_customizations(user_id, personalization_profile)
            
            return {
                "success": True,
                "user_id": user_id,
                "personalization_profile": personalization_profile,
                "recommended_actions": recommended_actions,
                "ui_customizations": ui_customizations
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _action_handle_user_query(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle user query action"""
        try:
            query = parameters.get("query", "")
            user_id = parameters.get("user_id")
            conversation_id = parameters.get("conversation_id")
            
            # Process natural language
            nlp_result = await self._action_process_natural_language({
                "query": query,
                "context": {"user_id": user_id, "conversation_id": conversation_id}
            })
            
            if not nlp_result.get("success"):
                return nlp_result
            
            intent = nlp_result.get("intent")
            entities = nlp_result.get("entities", [])
            
            # Route to appropriate agent based on intent
            response = await self._route_query_to_agent(intent, entities, query, user_id)
            
            # Generate multimodal response
            multimodal_response = await self._action_generate_multimodal_responses({
                "content": response,
                "response_format": "text",
                "user_context": {"user_id": user_id}
            })
            
            return {
                "success": True,
                "query": query,
                "intent": intent,
                "response": multimodal_response.get("response"),
                "conversation_id": conversation_id
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _action_update_user_preferences(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Update user preferences action"""
        try:
            user_id = parameters.get("user_id")
            preferences = parameters.get("preferences", {})
            
            if not user_id:
                return {"success": False, "error": "user_id is required"}
            
            # Update user profile
            if user_id not in self.user_profiles:
                self.user_profiles[user_id] = {}
            
            self.user_profiles[user_id]["preferences"] = preferences
            self.user_profiles[user_id]["last_updated"] = datetime.now().isoformat()
            
            # Store in Strands framework
            if self.strands_framework:
                await self.strands_framework.update_context(
                    self.agent_id,
                    {f"user_profiles.{user_id}": self.user_profiles[user_id]}
                )
            
            return {
                "success": True,
                "user_id": user_id,
                "preferences_updated": True
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _action_get_conversation_history(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get conversation history action"""
        try:
            conversation_id = parameters.get("conversation_id")
            limit = parameters.get("limit", 50)
            
            if not conversation_id or conversation_id not in self.conversation_contexts:
                return {"success": False, "error": "Conversation not found"}
            
            context = self.conversation_contexts[conversation_id]
            history = context.get("message_history", [])
            
            # Apply limit
            limited_history = history[-limit:] if len(history) > limit else history
            
            return {
                "success": True,
                "conversation_id": conversation_id,
                "history": limited_history,
                "total_messages": len(history)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _action_create_dashboard_view(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create dashboard view action"""
        try:
            user_id = parameters.get("user_id")
            dashboard_type = parameters.get("dashboard_type", "overview")
            filters = parameters.get("filters", {})
            
            # Get user preferences
            user_profile = self.user_profiles.get(user_id, {})
            preferences = user_profile.get("preferences", {})
            
            # Generate dashboard configuration
            dashboard_config = await self._generate_dashboard_config(dashboard_type, filters, preferences)
            
            # Get data for dashboard
            dashboard_data = await self._get_dashboard_data(dashboard_type, filters)
            
            return {
                "success": True,
                "dashboard_type": dashboard_type,
                "config": dashboard_config,
                "data": dashboard_data,
                "user_id": user_id
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Message handlers
    async def _handle_user_query(self, message: AgentMessage) -> AgentMessage:
        """Handle user query messages"""
        try:
            query_data = message.content
            query = query_data.get("query", "")
            user_id = query_data.get("user_id")
            
            # Process the query
            result = await self._action_handle_user_query({
                "query": query,
                "user_id": user_id,
                "conversation_id": query_data.get("conversation_id")
            })
            
            return AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type=MessageType.RESPONSE,
                content=result,
                correlation_id=message.correlation_id
            )
            
        except Exception as e:
            self.logger.error(f"Error handling user query: {e}")
            return AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type=MessageType.ERROR,
                content={"error": str(e)},
                correlation_id=message.correlation_id
            )
    
    async def _handle_dashboard_request(self, message: AgentMessage) -> AgentMessage:
        """Handle dashboard request messages"""
        try:
            request_data = message.content
            
            # Create dashboard view
            result = await self._action_create_dashboard_view(request_data)
            
            return AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type=MessageType.RESPONSE,
                content=result,
                correlation_id=message.correlation_id
            )
            
        except Exception as e:
            self.logger.error(f"Error handling dashboard request: {e}")
            return AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type=MessageType.ERROR,
                content={"error": str(e)},
                correlation_id=message.correlation_id
            )
    
    async def _handle_preference_update(self, message: AgentMessage) -> AgentMessage:
        """Handle preference update messages"""
        try:
            preference_data = message.content
            
            # Update user preferences
            result = await self._action_update_user_preferences(preference_data)
            
            return AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type=MessageType.RESPONSE,
                content=result,
                correlation_id=message.correlation_id
            )
            
        except Exception as e:
            self.logger.error(f"Error handling preference update: {e}")
            return AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type=MessageType.ERROR,
                content={"error": str(e)},
                correlation_id=message.correlation_id
            )
    
    async def _handle_conversation_timeout(self, message: AgentMessage) -> AgentMessage:
        """Handle conversation timeout messages"""
        try:
            timeout_data = message.content
            conversation_id = timeout_data.get("conversation_id")
            
            # Clean up timed out conversation
            if conversation_id in self.conversation_contexts:
                # Archive conversation
                archived_context = self.conversation_contexts[conversation_id]
                archived_context["archived_at"] = datetime.now().isoformat()
                archived_context["status"] = "timeout"
                
                # Remove from active conversations
                del self.conversation_contexts[conversation_id]
                if conversation_id in self.active_conversations:
                    del self.active_conversations[conversation_id]
            
            return AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type=MessageType.RESPONSE,
                content={
                    "status": "conversation_timeout_processed",
                    "conversation_id": conversation_id
                },
                correlation_id=message.correlation_id
            )
            
        except Exception as e:
            self.logger.error(f"Error handling conversation timeout: {e}")
            return AgentMessage(
                sender=self.agent_id,
                recipient=message.sender,
                message_type=MessageType.ERROR,
                content={"error": str(e)},
                correlation_id=message.correlation_id
            )
    
    # Helper methods
    async def _initialize_nlp_patterns(self) -> None:
        """Initialize NLP patterns and intent recognition"""
        try:
            self.intent_patterns = {
                "cost_query": [
                    r"(?i).*cost.*",
                    r"(?i).*spend.*",
                    r"(?i).*budget.*",
                    r"(?i).*price.*",
                    r"(?i).*billing.*",
                    r"(?i)how much.*"
                ],
                "forecast_request": [
                    r"(?i).*forecast.*",
                    r"(?i).*predict.*",
                    r"(?i).*future.*",
                    r"(?i).*trend.*",
                    r"(?i).*projection.*"
                ],
                "alert_management": [
                    r"(?i).*alert.*",
                    r"(?i).*notification.*",
                    r"(?i).*warning.*",
                    r"(?i).*threshold.*",
                    r"(?i).*monitor.*"
                ],
                "resource_optimization": [
                    r"(?i).*optimize.*",
                    r"(?i).*resource.*",
                    r"(?i).*utilization.*",
                    r"(?i).*efficiency.*",
                    r"(?i).*rightsize.*"
                ],
                "dashboard_navigation": [
                    r"(?i).*dashboard.*",
                    r"(?i).*view.*",
                    r"(?i).*show.*",
                    r"(?i).*display.*",
                    r"(?i).*navigate.*"
                ],
                "help_request": [
                    r"(?i).*help.*",
                    r"(?i).*how.*",
                    r"(?i).*what.*",
                    r"(?i).*explain.*",
                    r"(?i).*guide.*"
                ]
            }
            
            self.logger.info("NLP patterns initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing NLP patterns: {e}")
            raise
    
    async def _initialize_response_templates(self) -> None:
        """Initialize response templates for different content types"""
        try:
            self.response_templates = {
                "cost_summary": {
                    "text": "💰 **Cost Summary**\n{summary_text}\n\n📊 **Key Metrics:**\n{metrics}\n\n💡 **Recommendations:**\n{recommendations}",
                    "chart": {
                        "type": "line_chart",
                        "title": "Cost Trend",
                        "x_axis": "Date",
                        "y_axis": "Cost ($)"
                    },
                    "table": {
                        "columns": ["Service", "Current Cost", "Previous Period", "Change"],
                        "sortable": True
                    }
                },
                "forecast_result": {
                    "text": "📈 **Forecast Results**\n{forecast_text}\n\n🎯 **Confidence:** {confidence}%\n\n📅 **Period:** {period}",
                    "chart": {
                        "type": "forecast_chart",
                        "title": "Cost Forecast",
                        "show_confidence_bands": True
                    }
                },
                "alert_status": {
                    "text": "🚨 **Alert Status**\n{alert_summary}\n\n⚠️ **Active Alerts:** {active_count}\n\n✅ **Resolved:** {resolved_count}",
                    "table": {
                        "columns": ["Alert", "Severity", "Status", "Created", "Actions"],
                        "filters": ["severity", "status"]
                    }
                },
                "resource_optimization": {
                    "text": "⚡ **Resource Optimization**\n{optimization_text}\n\n💰 **Potential Savings:** ${savings}\n\n🎯 **Recommendations:** {rec_count}",
                    "chart": {
                        "type": "utilization_chart",
                        "title": "Resource Utilization"
                    }
                }
            }
            
            self.logger.info("Response templates initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing response templates: {e}")
            raise
    
    async def _load_user_profiles(self) -> None:
        """Load user profiles and preferences"""
        try:
            # Initialize default user profiles
            self.user_profiles = {
                "ceo": {
                    "role": "ceo",
                    "preferences": {
                        "dashboard_view": "executive_summary",
                        "notification_frequency": "daily",
                        "preferred_charts": ["trend", "summary"],
                        "language": "en"
                    },
                    "interaction_history": []
                },
                "cto": {
                    "role": "cto",
                    "preferences": {
                        "dashboard_view": "technical_metrics",
                        "notification_frequency": "real_time",
                        "preferred_charts": ["detailed", "technical"],
                        "language": "en"
                    },
                    "interaction_history": []
                },
                "finops_lead": {
                    "role": "finops_lead",
                    "preferences": {
                        "dashboard_view": "cost_analysis",
                        "notification_frequency": "hourly",
                        "preferred_charts": ["cost_breakdown", "forecast"],
                        "language": "en"
                    },
                    "interaction_history": []
                },
                "devops_engineer": {
                    "role": "devops_engineer",
                    "preferences": {
                        "dashboard_view": "resource_monitoring",
                        "notification_frequency": "real_time",
                        "preferred_charts": ["utilization", "performance"],
                        "language": "en"
                    },
                    "interaction_history": []
                }
            }
            
            self.logger.info("User profiles loaded")
            
        except Exception as e:
            self.logger.error(f"Error loading user profiles: {e}")
            raise
    
    async def _conversation_management_loop(self) -> None:
        """Conversation management background loop"""
        while self._state.status != "offline":
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Check for conversation timeouts
                await self._check_conversation_timeouts()
                
                # Update conversation contexts
                await self._update_active_conversations()
                
            except Exception as e:
                self.logger.error(f"Error in conversation management loop: {e}")
    
    async def _personalization_learning_loop(self) -> None:
        """Personalization learning background loop"""
        while self._state.status != "offline":
            try:
                await asyncio.sleep(300)  # Learn every 5 minutes
                
                # Update personalization models
                await self._update_personalization_models()
                
            except Exception as e:
                self.logger.error(f"Error in personalization learning loop: {e}")
    
    async def _context_cleanup_loop(self) -> None:
        """Context cleanup background loop"""
        while self._state.status != "offline":
            try:
                await asyncio.sleep(3600)  # Cleanup every hour
                
                # Clean up old conversation contexts
                await self._cleanup_old_contexts()
                
            except Exception as e:
                self.logger.error(f"Error in context cleanup loop: {e}")
    
    async def _extract_intent(self, query: str) -> str:
        """Extract intent from user query"""
        try:
            query_lower = query.lower()
            
            # Check patterns for each intent
            for intent, patterns in self.intent_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, query):
                        return intent
            
            # Default intent if no match
            return "general_query"
            
        except Exception as e:
            self.logger.error(f"Error extracting intent: {e}")
            return "general_query"
    
    async def _extract_entities(self, query: str, intent: str) -> List[Dict[str, Any]]:
        """Extract entities from user query"""
        try:
            entities = []
            
            # Extract common entities based on intent
            if intent == "cost_query":
                # Extract time periods
                time_patterns = [
                    (r"(?i)(last|past)\s+(\d+)\s+(day|days|week|weeks|month|months)", "time_period"),
                    (r"(?i)(this|current)\s+(week|month|year)", "time_period"),
                    (r"(?i)(today|yesterday)", "time_period")
                ]
                
                for pattern, entity_type in time_patterns:
                    matches = re.finditer(pattern, query)
                    for match in matches:
                        entities.append({
                            "type": entity_type,
                            "value": match.group(0),
                            "start": match.start(),
                            "end": match.end()
                        })
                
                # Extract service names
                service_patterns = [
                    (r"(?i)(ec2|rds|s3|lambda|cloudwatch)", "aws_service")
                ]
                
                for pattern, entity_type in service_patterns:
                    matches = re.finditer(pattern, query)
                    for match in matches:
                        entities.append({
                            "type": entity_type,
                            "value": match.group(0).upper(),
                            "start": match.start(),
                            "end": match.end()
                        })
            
            elif intent == "resource_optimization":
                # Extract resource types
                resource_patterns = [
                    (r"(?i)(instance|instances|server|servers)", "resource_type"),
                    (r"(?i)(database|db)", "resource_type"),
                    (r"(?i)(storage|disk|volume)", "resource_type")
                ]
                
                for pattern, entity_type in resource_patterns:
                    matches = re.finditer(pattern, query)
                    for match in matches:
                        entities.append({
                            "type": entity_type,
                            "value": match.group(0),
                            "start": match.start(),
                            "end": match.end()
                        })
            
            return entities
            
        except Exception as e:
            self.logger.error(f"Error extracting entities: {e}")
            return []
    
    async def _calculate_nlp_confidence(self, query: str, intent: str, entities: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for NLP processing"""
        try:
            confidence = 0.5  # Base confidence
            
            # Increase confidence based on intent match strength
            if intent != "general_query":
                confidence += 0.2
            
            # Increase confidence based on entities found
            if entities:
                confidence += min(0.3, len(entities) * 0.1)
            
            # Increase confidence based on query clarity
            if len(query.split()) > 3:  # More detailed queries
                confidence += 0.1
            
            return min(1.0, confidence)
            
        except Exception as e:
            self.logger.error(f"Error calculating NLP confidence: {e}")
            return 0.5
    
    async def _generate_suggested_actions(self, intent: str, entities: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate suggested actions based on intent and entities"""
        try:
            actions = []
            
            if intent == "cost_query":
                actions.extend([
                    {"action": "show_cost_summary", "label": "Show Cost Summary", "priority": 1},
                    {"action": "generate_cost_report", "label": "Generate Detailed Report", "priority": 2},
                    {"action": "compare_periods", "label": "Compare Time Periods", "priority": 3}
                ])
            
            elif intent == "forecast_request":
                actions.extend([
                    {"action": "generate_forecast", "label": "Generate Forecast", "priority": 1},
                    {"action": "scenario_analysis", "label": "Run Scenario Analysis", "priority": 2},
                    {"action": "set_budget_alerts", "label": "Set Budget Alerts", "priority": 3}
                ])
            
            elif intent == "alert_management":
                actions.extend([
                    {"action": "show_active_alerts", "label": "Show Active Alerts", "priority": 1},
                    {"action": "configure_thresholds", "label": "Configure Thresholds", "priority": 2},
                    {"action": "alert_history", "label": "View Alert History", "priority": 3}
                ])
            
            elif intent == "resource_optimization":
                actions.extend([
                    {"action": "analyze_utilization", "label": "Analyze Resource Utilization", "priority": 1},
                    {"action": "rightsizing_recommendations", "label": "Get Rightsizing Recommendations", "priority": 2},
                    {"action": "cost_optimization", "label": "Find Cost Optimizations", "priority": 3}
                ])
            
            elif intent == "dashboard_navigation":
                actions.extend([
                    {"action": "show_dashboard", "label": "Show Dashboard", "priority": 1},
                    {"action": "customize_view", "label": "Customize View", "priority": 2},
                    {"action": "export_data", "label": "Export Data", "priority": 3}
                ])
            
            else:  # help_request or general_query
                actions.extend([
                    {"action": "show_help", "label": "Show Help", "priority": 1},
                    {"action": "feature_tour", "label": "Take Feature Tour", "priority": 2},
                    {"action": "contact_support", "label": "Contact Support", "priority": 3}
                ])
            
            return actions
            
        except Exception as e:
            self.logger.error(f"Error generating suggested actions: {e}")
            return []
    
    async def _route_query_to_agent(self, intent: str, entities: List[Dict[str, Any]], query: str, user_id: str) -> Dict[str, Any]:
        """Route query to appropriate specialized agent"""
        try:
            if intent == "cost_query" and self.mcp_server:
                # Route to cost management agent
                cost_message = AgentMessage(
                    sender=self.agent_id,
                    recipient="cost_management_agent",
                    message_type=MessageType.REQUEST,
                    content={
                        "action": "analyze_cost_data",
                        "query": query,
                        "entities": entities,
                        "user_id": user_id
                    }
                )
                
                response = await self.mcp_server.route_message(cost_message)
                return response.content
            
            elif intent == "forecast_request" and self.mcp_server:
                # Route to forecasting agent
                forecast_message = AgentMessage(
                    sender=self.agent_id,
                    recipient="forecasting_agent",
                    message_type=MessageType.REQUEST,
                    content={
                        "action": "generate_cost_forecast",
                        "query": query,
                        "entities": entities,
                        "user_id": user_id
                    }
                )
                
                response = await self.mcp_server.route_message(forecast_message)
                return response.content
            
            elif intent == "resource_optimization" and self.mcp_server:
                # Route to resource management agent
                resource_message = AgentMessage(
                    sender=self.agent_id,
                    recipient="resource_management_agent",
                    message_type=MessageType.REQUEST,
                    content={
                        "action": "monitor_resource_utilization",
                        "query": query,
                        "entities": entities,
                        "user_id": user_id
                    }
                )
                
                response = await self.mcp_server.route_message(resource_message)
                return response.content
            
            elif intent == "alert_management" and self.mcp_server:
                # Route to alert management agent
                alert_message = AgentMessage(
                    sender=self.agent_id,
                    recipient="alert_management_agent",
                    message_type=MessageType.REQUEST,
                    content={
                        "action": "get_active_alerts",
                        "query": query,
                        "entities": entities,
                        "user_id": user_id
                    }
                )
                
                response = await self.mcp_server.route_message(alert_message)
                return response.content
            
            else:
                # Handle locally
                return await self._handle_general_query(query, intent, entities, user_id)
            
        except Exception as e:
            self.logger.error(f"Error routing query to agent: {e}")
            return {
                "success": False,
                "error": "Unable to process query at this time",
                "fallback_response": "I'm having trouble processing your request. Please try rephrasing your question."
            }
    
    async def _handle_general_query(self, query: str, intent: str, entities: List[Dict[str, Any]], user_id: str) -> Dict[str, Any]:
        """Handle general queries locally"""
        try:
            if intent == "help_request":
                return {
                    "success": True,
                    "response": "I can help you with cost analysis, forecasting, resource optimization, and alert management. What would you like to know?",
                    "suggested_actions": await self._generate_suggested_actions(intent, entities, {"user_id": user_id})
                }
            
            elif intent == "dashboard_navigation":
                return {
                    "success": True,
                    "response": "I can help you navigate the dashboard. What would you like to see?",
                    "suggested_actions": await self._generate_suggested_actions(intent, entities, {"user_id": user_id})
                }
            
            else:
                return {
                    "success": True,
                    "response": f"I understand you're asking about {intent.replace('_', ' ')}. Let me help you with that.",
                    "suggested_actions": await self._generate_suggested_actions(intent, entities, {"user_id": user_id})
                }
            
        except Exception as e:
            self.logger.error(f"Error handling general query: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_response": "I'm having trouble understanding your request. Could you please rephrase it?"
            }
    
    # Response generation methods
    async def _generate_text_response(self, content: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text response"""
        try:
            response_text = content.get("response", "")
            
            # Add personalization based on user context
            user_id = user_context.get("user_id")
            if user_id and user_id in self.user_profiles:
                user_profile = self.user_profiles[user_id]
                role = user_profile.get("role", "user")
                
                # Customize response based on role
                if role == "ceo":
                    response_text = f"📊 **Executive Summary**\n{response_text}"
                elif role == "cto":
                    response_text = f"🔧 **Technical Overview**\n{response_text}"
                elif role == "finops_lead":
                    response_text = f"💰 **Financial Analysis**\n{response_text}"
                elif role == "devops_engineer":
                    response_text = f"⚙️ **Operations Report**\n{response_text}"
            
            return {
                "type": "text",
                "content": response_text,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating text response: {e}")
            return {
                "type": "text",
                "content": "Unable to generate response",
                "error": str(e)
            }
    
    async def _generate_chart_response(self, content: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate chart response"""
        try:
            chart_data = content.get("chart_data", [])
            chart_type = content.get("chart_type", "line")
            
            return {
                "type": "chart",
                "chart_type": chart_type,
                "data": chart_data,
                "config": {
                    "responsive": True,
                    "interactive": True,
                    "theme": "light"
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating chart response: {e}")
            return {
                "type": "chart",
                "error": str(e)
            }
    
    async def _generate_table_response(self, content: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate table response"""
        try:
            table_data = content.get("table_data", [])
            columns = content.get("columns", [])
            
            return {
                "type": "table",
                "columns": columns,
                "data": table_data,
                "config": {
                    "sortable": True,
                    "filterable": True,
                    "paginated": True,
                    "page_size": 25
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating table response: {e}")
            return {
                "type": "table",
                "error": str(e)
            }
    
    async def _generate_dashboard_response(self, content: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate dashboard response"""
        try:
            dashboard_config = content.get("dashboard_config", {})
            
            return {
                "type": "dashboard",
                "config": dashboard_config,
                "widgets": content.get("widgets", []),
                "layout": content.get("layout", "grid"),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating dashboard response: {e}")
            return {
                "type": "dashboard",
                "error": str(e)
            }
    
    async def _generate_interactive_elements(self, content: Dict[str, Any], response_format: str) -> List[Dict[str, Any]]:
        """Generate interactive elements for response"""
        try:
            elements = []
            
            if response_format == "text":
                elements.extend([
                    {"type": "button", "label": "Get More Details", "action": "expand_details"},
                    {"type": "button", "label": "Export", "action": "export_data"}
                ])
            
            elif response_format == "chart":
                elements.extend([
                    {"type": "dropdown", "label": "Chart Type", "options": ["line", "bar", "pie"], "action": "change_chart_type"},
                    {"type": "button", "label": "Download Chart", "action": "download_chart"}
                ])
            
            elif response_format == "table":
                elements.extend([
                    {"type": "search", "placeholder": "Search table...", "action": "filter_table"},
                    {"type": "button", "label": "Export CSV", "action": "export_csv"}
                ])
            
            return elements
            
        except Exception as e:
            self.logger.error(f"Error generating interactive elements: {e}")
            return []
    
    # Additional helper methods for conversation management, personalization, etc.
    async def _update_conversation_context(self, conversation_id: str, message_history: List[Dict[str, Any]], user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Update conversation context"""
        if conversation_id not in self.conversation_contexts:
            self.conversation_contexts[conversation_id] = {
                "created_at": datetime.now().isoformat(),
                "message_history": [],
                "context_summary": {},
                "user_profile": user_profile
            }
        
        context = self.conversation_contexts[conversation_id]
        context["message_history"].extend(message_history)
        context["last_updated"] = datetime.now().isoformat()
        
        # Generate context summary
        context_summary = {
            "conversation_id": conversation_id,
            "message_count": len(context["message_history"]),
            "topics_discussed": await self._extract_conversation_topics(context["message_history"]),
            "user_intent_history": await self._extract_intent_history(context["message_history"]),
            "last_activity": datetime.now().isoformat()
        }
        
        context["context_summary"] = context_summary
        return context_summary
    
    async def _extract_conversation_topics(self, message_history: List[Dict[str, Any]]) -> List[str]:
        """Extract topics from conversation history"""
        topics = set()
        for message in message_history:
            content = message.get("content", "")
            intent = await self._extract_intent(content)
            if intent != "general_query":
                topics.add(intent.replace("_", " "))
        return list(topics)
    
    async def _extract_intent_history(self, message_history: List[Dict[str, Any]]) -> List[str]:
        """Extract intent history from conversation"""
        intents = []
        for message in message_history:
            content = message.get("content", "")
            intent = await self._extract_intent(content)
            intents.append(intent)
        return intents
    
    async def _determine_next_actions(self, context_summary: Dict[str, Any], message_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Determine next actions based on conversation context"""
        actions = []
        
        topics = context_summary.get("topics_discussed", [])
        
        if "cost query" in topics:
            actions.append({"action": "suggest_cost_optimization", "priority": 1})
        
        if "forecast request" in topics:
            actions.append({"action": "suggest_budget_planning", "priority": 2})
        
        if len(message_history) > 5:
            actions.append({"action": "summarize_conversation", "priority": 3})
        
        return actions
    
    async def _update_conversation_state(self, conversation_id: str, context_summary: Dict[str, Any]) -> str:
        """Update conversation state"""
        message_count = context_summary.get("message_count", 0)
        
        if message_count == 0:
            return "new"
        elif message_count < 5:
            return "active"
        elif message_count < 20:
            return "engaged"
        else:
            return "extended"
    
    # Placeholder methods for remaining functionality
    async def _update_personalization_profile(self, user_id: str, interaction_history: List[Dict[str, Any]], preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Update personalization profile"""
        return {"user_id": user_id, "updated": True}
    
    async def _generate_personalized_recommendations(self, user_id: str, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate personalized recommendations"""
        return []
    
    async def _generate_ui_customizations(self, user_id: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate UI customizations"""
        return {"theme": "light", "layout": "grid"}
    
    async def _generate_dashboard_config(self, dashboard_type: str, filters: Dict[str, Any], preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Generate dashboard configuration"""
        return {"type": dashboard_type, "filters": filters}
    
    async def _get_dashboard_data(self, dashboard_type: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get dashboard data"""
        return {"data": "sample_data"}
    
    # Analysis methods for domain data
    async def _analyze_interaction_patterns(self, user_interactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze user interaction patterns"""
        return {"pattern": "increasing_engagement"}
    
    async def _analyze_conversation_effectiveness(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze conversation effectiveness"""
        return {"effectiveness_score": 0.8}
    
    async def _analyze_user_satisfaction(self, user_feedback: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze user satisfaction"""
        return {"satisfaction_score": 0.85}
    
    async def _identify_personalization_opportunities(self, user_interactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify personalization opportunities"""
        return []
    
    # Recommendation generation methods
    async def _generate_ux_recommendations(self, interaction_data: Dict[str, Any], user_feedback: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate UX improvement recommendations"""
        return []
    
    async def _generate_personalization_recommendations(self, interaction_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate personalization recommendations"""
        return []
    
    async def _generate_conversation_recommendations(self, interaction_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate conversation flow recommendations"""
        return []
    
    async def _generate_accessibility_recommendations(self, user_feedback: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate accessibility recommendations"""
        return []
    
    async def _calculate_ui_recommendation_impact(self, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate impact analysis for UI recommendation"""
        return {"development_cost": 1000.0, "user_impact": "high"}
    
    def _determine_required_approvers(self, impact_analysis: Dict[str, Any], recommendation: Dict[str, Any]) -> List[str]:
        """Determine required approvers for UI recommendations"""
        return ["cto"]
    
    # Background loop methods
    async def _check_conversation_timeouts(self) -> None:
        """Check for conversation timeouts"""
        timeout_minutes = self.config.get("conversation_timeout_minutes", 30)
        cutoff_time = datetime.now() - timedelta(minutes=timeout_minutes)
        
        for conv_id, context in list(self.conversation_contexts.items()):
            last_updated = datetime.fromisoformat(context.get("last_updated", datetime.now().isoformat()))
            if last_updated < cutoff_time:
                # Timeout conversation
                await self._timeout_conversation(conv_id)
    
    async def _timeout_conversation(self, conversation_id: str) -> None:
        """Timeout a conversation"""
        if conversation_id in self.conversation_contexts:
            context = self.conversation_contexts[conversation_id]
            context["status"] = "timeout"
            context["ended_at"] = datetime.now().isoformat()
            
            # Move to history
            del self.conversation_contexts[conversation_id]
            if conversation_id in self.active_conversations:
                del self.active_conversations[conversation_id]
    
    async def _update_active_conversations(self) -> None:
        """Update active conversations"""
        self.logger.debug(f"Managing {len(self.conversation_contexts)} active conversations")
    
    async def _update_personalization_models(self) -> None:
        """Update personalization models"""
        self.logger.debug("Updating personalization models")
    
    async def _cleanup_old_contexts(self) -> None:
        """Clean up old conversation contexts"""
        # Keep contexts for 24 hours after timeout
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        # This would clean up archived contexts in a real implementation
        self.logger.debug("Cleaning up old conversation contexts")
        return {}
    
    async def _generate_dashboard_config(self, dashboard_type: str, filters: Dict[str, Any], preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Generate dashboard configuration"""
        return {"type": dashboard_type, "filters": filters}
    
    async def _get_dashboard_data(self, dashboard_type: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get data for dashboard"""
        return {"data": "sample_data"}
    
    # Additional placeholder methods
    async def _analyze_interaction_patterns(self, interactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {"patterns": "analyzed"}
    
    async def _analyze_conversation_effectiveness(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"effectiveness": "high"}
    
    async def _analyze_user_satisfaction(self, feedback: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {"satisfaction": "positive"}
    
    async def _identify_personalization_opportunities(self, interactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return []
    
    async def _generate_ux_recommendations(self, interaction_data: Dict[str, Any], feedback: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return []
    
    async def _generate_personalization_recommendations(self, interaction_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []
    
    async def _generate_conversation_recommendations(self, interaction_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []
    
    async def _generate_accessibility_recommendations(self, feedback: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return []
    
    async def _calculate_ui_recommendation_impact(self, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        return {"impact": "positive"}
    
    def _determine_required_approvers(self, impact_analysis: Dict[str, Any], recommendation: Dict[str, Any]) -> List[str]:
        return ["cto"]
    
    async def _check_conversation_timeouts(self) -> None:
        """Check for conversation timeouts"""
        pass
    
    async def _update_active_conversations(self) -> None:
        """Update active conversations"""
        pass
    
    async def _update_personalization_models(self) -> None:
        """Update personalization models"""
        pass
    
    async def _cleanup_old_contexts(self) -> None:
        """Clean up old conversation contexts"""
        pass
    
    # Backward Compatibility Methods
    async def render_dashboard_header(self, title: str = "Vismaya DemandOps", subtitle: str = None) -> Dict[str, Any]:
        """Render dashboard header (backward compatibility method)"""
        try:
            header_config = {
                "title": title,
                "subtitle": subtitle or "AI-Powered FinOps Platform",
                "timestamp": datetime.now().strftime('%H:%M:%S'),
                "status_indicators": [
                    {"label": "System Online", "status": "healthy", "icon": "🟢"},
                    {"label": "Real-time Data", "status": "active", "icon": "📊"}
                ]
            }
            
            return {
                "success": True,
                "header_config": header_config,
                "enhanced": True
            }
            
        except Exception as e:
            self.logger.error(f"Error rendering dashboard header: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback": "Standard header"
            }
    
    async def render_navigation_tabs(self, tabs: List[str] = None) -> Dict[str, Any]:
        """Render navigation tabs (backward compatibility method)"""
        try:
            default_tabs = [
                "Current Usage", "Detailed Usage", "Detailed Billing", 
                "Forecast", "Historical Data", "Settings"
            ]
            
            tab_config = {
                "tabs": tabs or default_tabs,
                "active_tab": 0,
                "enhanced_features": {
                    "search": True,
                    "favorites": True,
                    "recent": True
                }
            }
            
            return {
                "success": True,
                "tab_config": tab_config,
                "enhanced": True
            }
            
        except Exception as e:
            self.logger.error(f"Error rendering navigation tabs: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback": "Standard tabs"
            }
    
    async def render_metrics_display(self, metrics: Dict[str, Any] = None) -> Dict[str, Any]:
        """Render metrics display (backward compatibility method)"""
        try:
            enhanced_metrics = {
                "current_spend": {
                    "value": metrics.get("current_spend", 0) if metrics else 0,
                    "trend": "up",
                    "confidence": 0.9,
                    "ai_insight": "🤖 Spending within expected range"
                },
                "budget_status": {
                    "value": f"{metrics.get('budget_pct', 0):.0f}%" if metrics else "0%",
                    "status": "healthy",
                    "ai_insight": "🤖 Budget utilization is optimal"
                },
                "forecast": {
                    "value": metrics.get("forecast", 0) if metrics else 0,
                    "accuracy": 0.85,
                    "ai_insight": "🤖 Forecast based on ML models"
                }
            }
            
            return {
                "success": True,
                "enhanced_metrics": enhanced_metrics,
                "enhanced": True
            }
            
        except Exception as e:
            self.logger.error(f"Error rendering metrics display: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback": "Standard metrics"
            }
    
    async def render_cost_charts(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Render cost charts (backward compatibility method)"""
        try:
            chart_config = {
                "monthly_trend": {
                    "type": "line",
                    "title": "Monthly Spend Trend",
                    "enhanced_features": {
                        "ai_annotations": True,
                        "anomaly_detection": True,
                        "forecast_overlay": True
                    }
                },
                "service_breakdown": {
                    "type": "bar",
                    "title": "Service-wise Spend",
                    "enhanced_features": {
                        "drill_down": True,
                        "cost_optimization_hints": True,
                        "interactive_filters": True
                    }
                }
            }
            
            return {
                "success": True,
                "chart_config": chart_config,
                "enhanced": True
            }
            
        except Exception as e:
            self.logger.error(f"Error rendering cost charts: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback": "Standard charts"
            }
    
    async def render_conversational_interface(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Render conversational AI interface (backward compatibility method)"""
        try:
            interface_config = {
                "chat_features": {
                    "natural_language_processing": True,
                    "context_awareness": True,
                    "multi_modal_responses": True,
                    "suggested_actions": True
                },
                "enhanced_capabilities": {
                    "cost_analysis": True,
                    "forecast_generation": True,
                    "optimization_recommendations": True,
                    "real_time_alerts": True
                },
                "personalization": {
                    "user_preferences": True,
                    "conversation_history": True,
                    "adaptive_responses": True
                }
            }
            
            return {
                "success": True,
                "interface_config": interface_config,
                "enhanced": True
            }
            
        except Exception as e:
            self.logger.error(f"Error rendering conversational interface: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback": "Standard chat interface"
            }
    
    async def render_forecasting_interface(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Render forecasting interface (backward compatibility method)"""
        try:
            forecasting_config = {
                "ml_capabilities": {
                    "advanced_models": True,
                    "confidence_intervals": True,
                    "scenario_analysis": True,
                    "trend_detection": True
                },
                "interactive_features": {
                    "what_if_analysis": True,
                    "parameter_tuning": True,
                    "model_comparison": True,
                    "export_forecasts": True
                },
                "ai_insights": {
                    "anomaly_detection": True,
                    "recommendation_engine": True,
                    "risk_assessment": True
                }
            }
            
            return {
                "success": True,
                "forecasting_config": forecasting_config,
                "enhanced": True
            }
            
        except Exception as e:
            self.logger.error(f"Error rendering forecasting interface: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback": "Standard forecasting interface"
            }
    
    async def render_usage_overview(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Render usage overview (backward compatibility method)"""
        try:
            overview_config = {
                "resource_summary": {
                    "ec2_instances": True,
                    "storage_volumes": True,
                    "database_instances": True,
                    "enhanced_metrics": True
                },
                "ai_insights": {
                    "utilization_analysis": True,
                    "optimization_opportunities": True,
                    "cost_predictions": True,
                    "anomaly_detection": True
                },
                "interactive_elements": {
                    "drill_down_capabilities": True,
                    "real_time_updates": True,
                    "export_functionality": True
                }
            }
            
            return {
                "success": True,
                "overview_config": overview_config,
                "enhanced": True
            }
            
        except Exception as e:
            self.logger.error(f"Error rendering usage overview: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback": "Standard usage overview"
            }
    
    async def render_detailed_usage(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Render detailed usage (backward compatibility method)"""
        try:
            detailed_config = {
                "enhanced_tables": {
                    "sortable": True,
                    "filterable": True,
                    "searchable": True,
                    "exportable": True
                },
                "ai_enhancements": {
                    "cost_breakdown": True,
                    "utilization_insights": True,
                    "optimization_suggestions": True
                }
            }
            
            return {
                "success": True,
                "detailed_config": detailed_config,
                "enhanced": True
            }
            
        except Exception as e:
            self.logger.error(f"Error rendering detailed usage: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback": "Standard detailed usage"
            }
    
    async def render_billing_details(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Render billing details (backward compatibility method)"""
        try:
            billing_config = {
                "enhanced_billing": {
                    "cost_allocation": True,
                    "tag_based_analysis": True,
                    "department_breakdown": True,
                    "ai_cost_insights": True
                }
            }
            
            return {
                "success": True,
                "billing_config": billing_config,
                "enhanced": True
            }
            
        except Exception as e:
            self.logger.error(f"Error rendering billing details: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback": "Standard billing details"
            }
    
    async def render_forecast_analysis(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Render forecast analysis (backward compatibility method)"""
        try:
            forecast_config = {
                "ml_forecasting": {
                    "multiple_models": True,
                    "ensemble_predictions": True,
                    "confidence_bands": True,
                    "scenario_modeling": True
                },
                "interactive_analysis": {
                    "parameter_adjustment": True,
                    "what_if_scenarios": True,
                    "sensitivity_analysis": True
                }
            }
            
            return {
                "success": True,
                "forecast_config": forecast_config,
                "enhanced": True
            }
            
        except Exception as e:
            self.logger.error(f"Error rendering forecast analysis: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback": "Standard forecast analysis"
            }
    
    async def render_historical_data(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Render historical data (backward compatibility method)"""
        try:
            historical_config = {
                "enhanced_analytics": {
                    "trend_analysis": True,
                    "pattern_recognition": True,
                    "anomaly_detection": True,
                    "comparative_analysis": True
                },
                "ai_insights": {
                    "cost_drivers": True,
                    "seasonal_patterns": True,
                    "optimization_history": True
                }
            }
            
            return {
                "success": True,
                "historical_config": historical_config,
                "enhanced": True
            }
            
        except Exception as e:
            self.logger.error(f"Error rendering historical data: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback": "Standard historical data"
            }
    
    async def render_settings_panel(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Render settings panel (backward compatibility method)"""
        try:
            settings_config = {
                "enhanced_settings": {
                    "personalization": True,
                    "ai_preferences": True,
                    "notification_management": True,
                    "dashboard_customization": True
                },
                "agent_configuration": {
                    "agent_behavior": True,
                    "automation_rules": True,
                    "approval_workflows": True
                }
            }
            
            return {
                "success": True,
                "settings_config": settings_config,
                "enhanced": True
            }
            
        except Exception as e:
            self.logger.error(f"Error rendering settings panel: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback": "Standard settings panel"
            }