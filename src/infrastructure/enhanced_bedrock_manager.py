"""
Enhanced AWS Bedrock Manager for Agentic AI System
Provides advanced AI capabilities with multiple models and intelligent routing
"""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
import boto3
from dataclasses import dataclass

from .aws_session_factory import AWSSessionFactory

logger = logging.getLogger(__name__)


class ModelCapability(Enum):
    """AI model capabilities"""
    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    ANALYSIS = "analysis"
    REASONING = "reasoning"
    CONVERSATION = "conversation"
    SUMMARIZATION = "summarization"
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"


class TaskComplexity(Enum):
    """Task complexity levels"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXPERT = "expert"


@dataclass
class ModelConfiguration:
    """Configuration for AI model"""
    model_id: str
    name: str
    provider: str
    capabilities: List[ModelCapability]
    max_tokens: int
    cost_per_1k_input_tokens: float
    cost_per_1k_output_tokens: float
    complexity_rating: TaskComplexity
    recommended_use_cases: List[str]
    temperature_range: tuple = (0.0, 1.0)
    supports_streaming: bool = False
    context_window: int = 4096


@dataclass
class AIRequest:
    """AI request structure"""
    task_type: str
    content: str
    context: Optional[Dict[str, Any]] = None
    complexity: TaskComplexity = TaskComplexity.MODERATE
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    agent_id: Optional[str] = None
    correlation_id: Optional[str] = None


@dataclass
class AIResponse:
    """AI response structure"""
    content: str
    model_used: str
    tokens_used: Dict[str, int]
    cost_estimate: float
    processing_time_ms: float
    confidence_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class EnhancedBedrockManager:
    """
    Enhanced Bedrock manager with intelligent model selection and cost optimization
    """
    
    def __init__(self, aws_session_factory: AWSSessionFactory, config: Dict[str, Any]):
        self.session_factory = aws_session_factory
        self.config = config
        self.session = None
        self.bedrock_client = None
        
        # Model configurations
        self.models = self._initialize_model_configurations()
        
        # Usage tracking
        self.usage_stats = {
            "total_requests": 0,
            "total_cost": 0.0,
            "model_usage": {},
            "agent_usage": {}
        }
        
        # Performance optimization
        self.model_performance_cache = {}
        self.cost_optimization_enabled = config.get("cost_optimization", True)
        self.performance_tracking_enabled = config.get("performance_tracking", True)
        
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize Bedrock client"""
        try:
            self.session = self.session_factory.get_session()
            self.bedrock_client = self.session.client('bedrock-runtime')
            logger.info("Enhanced Bedrock client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e}")
            raise
    
    def _initialize_model_configurations(self) -> Dict[str, ModelConfiguration]:
        """Initialize model configurations"""
        return {
            # Claude 3 Models
            "claude-3-opus": ModelConfiguration(
                model_id="anthropic.claude-3-opus-20240229-v1:0",
                name="Claude 3 Opus",
                provider="Anthropic",
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.ANALYSIS,
                    ModelCapability.REASONING,
                    ModelCapability.CONVERSATION
                ],
                max_tokens=4096,
                cost_per_1k_input_tokens=0.015,
                cost_per_1k_output_tokens=0.075,
                complexity_rating=TaskComplexity.EXPERT,
                recommended_use_cases=[
                    "complex_analysis", "strategic_decisions", "code_review",
                    "detailed_explanations", "multi-step_reasoning"
                ],
                context_window=200000
            ),
            "claude-3-sonnet": ModelConfiguration(
                model_id="anthropic.claude-3-sonnet-20240229-v1:0",
                name="Claude 3 Sonnet",
                provider="Anthropic",
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.ANALYSIS,
                    ModelCapability.REASONING,
                    ModelCapability.CONVERSATION,
                    ModelCapability.SUMMARIZATION
                ],
                max_tokens=4096,
                cost_per_1k_input_tokens=0.003,
                cost_per_1k_output_tokens=0.015,
                complexity_rating=TaskComplexity.COMPLEX,
                recommended_use_cases=[
                    "cost_analysis", "report_generation", "decision_support",
                    "data_interpretation", "recommendations"
                ],
                context_window=200000
            ),
            "claude-3-haiku": ModelConfiguration(
                model_id="anthropic.claude-3-haiku-20240307-v1:0",
                name="Claude 3 Haiku",
                provider="Anthropic",
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.CONVERSATION,
                    ModelCapability.SUMMARIZATION,
                    ModelCapability.CLASSIFICATION
                ],
                max_tokens=4096,
                cost_per_1k_input_tokens=0.00025,
                cost_per_1k_output_tokens=0.00125,
                complexity_rating=TaskComplexity.SIMPLE,
                recommended_use_cases=[
                    "simple_queries", "status_updates", "basic_analysis",
                    "quick_responses", "data_formatting"
                ],
                context_window=200000
            ),
            # Titan Models
            "titan-text-express": ModelConfiguration(
                model_id="amazon.titan-text-express-v1",
                name="Titan Text Express",
                provider="Amazon",
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.SUMMARIZATION,
                    ModelCapability.EXTRACTION
                ],
                max_tokens=8192,
                cost_per_1k_input_tokens=0.0008,
                cost_per_1k_output_tokens=0.0016,
                complexity_rating=TaskComplexity.MODERATE,
                recommended_use_cases=[
                    "text_processing", "content_generation", "data_extraction",
                    "simple_analysis"
                ],
                context_window=8192
            ),
            # Jurassic Models
            "jurassic-2-ultra": ModelConfiguration(
                model_id="ai21.j2-ultra-v1",
                name="Jurassic-2 Ultra",
                provider="AI21 Labs",
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.ANALYSIS,
                    ModelCapability.CONVERSATION
                ],
                max_tokens=8192,
                cost_per_1k_input_tokens=0.0188,
                cost_per_1k_output_tokens=0.0188,
                complexity_rating=TaskComplexity.COMPLEX,
                recommended_use_cases=[
                    "detailed_analysis", "long_form_content", "complex_reasoning"
                ],
                context_window=8192
            )
        }
    
    async def process_ai_request(self, request: AIRequest) -> AIResponse:
        """Process AI request with intelligent model selection"""
        try:
            start_time = datetime.now()
            
            # Select optimal model
            selected_model = await self._select_optimal_model(request)
            
            # Prepare request
            bedrock_request = await self._prepare_bedrock_request(request, selected_model)
            
            # Make API call
            response = await self._invoke_bedrock_model(bedrock_request, selected_model)
            
            # Process response
            ai_response = await self._process_bedrock_response(
                response, selected_model, start_time, request
            )
            
            # Update usage statistics
            await self._update_usage_stats(request, ai_response, selected_model)
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Error processing AI request: {e}")
            raise
    
    async def _select_optimal_model(self, request: AIRequest) -> ModelConfiguration:
        """Select optimal model based on request characteristics"""
        try:
            # Get candidate models based on task type and complexity
            candidates = self._get_candidate_models(request)
            
            if not candidates:
                # Fallback to default model
                return self.models["claude-3-sonnet"]
            
            # Apply selection criteria
            if self.cost_optimization_enabled:
                # Prioritize cost-effectiveness for simple tasks
                if request.complexity in [TaskComplexity.SIMPLE, TaskComplexity.MODERATE]:
                    candidates.sort(key=lambda m: m.cost_per_1k_input_tokens + m.cost_per_1k_output_tokens)
            
            # Consider performance history
            if self.performance_tracking_enabled:
                candidates = await self._rank_by_performance(candidates, request)
            
            selected_model = candidates[0]
            
            logger.debug(f"Selected model {selected_model.name} for task {request.task_type}")
            return selected_model
            
        except Exception as e:
            logger.error(f"Error selecting model: {e}")
            return self.models["claude-3-sonnet"]  # Safe fallback
    
    def _get_candidate_models(self, request: AIRequest) -> List[ModelConfiguration]:
        """Get candidate models based on request requirements"""
        candidates = []
        
        # Map task types to capabilities
        task_capability_map = {
            "cost_analysis": [ModelCapability.ANALYSIS, ModelCapability.REASONING],
            "decision_proposal": [ModelCapability.REASONING, ModelCapability.TEXT_GENERATION],
            "report_generation": [ModelCapability.TEXT_GENERATION, ModelCapability.SUMMARIZATION],
            "conversation": [ModelCapability.CONVERSATION, ModelCapability.TEXT_GENERATION],
            "code_generation": [ModelCapability.CODE_GENERATION],
            "data_extraction": [ModelCapability.EXTRACTION, ModelCapability.ANALYSIS],
            "classification": [ModelCapability.CLASSIFICATION],
            "summarization": [ModelCapability.SUMMARIZATION]
        }
        
        required_capabilities = task_capability_map.get(request.task_type, [ModelCapability.TEXT_GENERATION])
        
        # Filter models by capabilities and complexity
        for model in self.models.values():
            # Check if model has required capabilities
            if any(cap in model.capabilities for cap in required_capabilities):
                # Check complexity match
                complexity_scores = {
                    TaskComplexity.SIMPLE: 1,
                    TaskComplexity.MODERATE: 2,
                    TaskComplexity.COMPLEX: 3,
                    TaskComplexity.EXPERT: 4
                }
                
                model_score = complexity_scores[model.complexity_rating]
                request_score = complexity_scores[request.complexity]
                
                # Allow models that can handle the complexity or higher
                if model_score >= request_score:
                    candidates.append(model)
        
        return candidates
    
    async def _rank_by_performance(
        self, 
        candidates: List[ModelConfiguration], 
        request: AIRequest
    ) -> List[ModelConfiguration]:
        """Rank candidates by historical performance"""
        try:
            # Get performance metrics for each candidate
            performance_scores = {}
            
            for model in candidates:
                cache_key = f"{model.model_id}_{request.task_type}"
                
                if cache_key in self.model_performance_cache:
                    perf_data = self.model_performance_cache[cache_key]
                    
                    # Calculate composite score
                    # Lower response time and higher success rate = better score
                    response_time_score = 1.0 / max(perf_data.get("avg_response_time", 1000), 100)
                    success_rate_score = perf_data.get("success_rate", 0.5)
                    cost_efficiency_score = 1.0 / max(perf_data.get("avg_cost", 0.01), 0.001)
                    
                    composite_score = (
                        response_time_score * 0.3 +
                        success_rate_score * 0.4 +
                        cost_efficiency_score * 0.3
                    )
                    
                    performance_scores[model.model_id] = composite_score
                else:
                    # No performance data, use default score
                    performance_scores[model.model_id] = 0.5
            
            # Sort by performance score (descending)
            candidates.sort(key=lambda m: performance_scores.get(m.model_id, 0.5), reverse=True)
            
            return candidates
            
        except Exception as e:
            logger.error(f"Error ranking models by performance: {e}")
            return candidates
    
    async def _prepare_bedrock_request(
        self, 
        request: AIRequest, 
        model: ModelConfiguration
    ) -> Dict[str, Any]:
        """Prepare Bedrock API request"""
        try:
            # Base request structure
            bedrock_request = {
                "modelId": model.model_id,
                "contentType": "application/json",
                "accept": "application/json"
            }
            
            # Prepare body based on model provider
            if model.provider == "Anthropic":
                body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": request.max_tokens or min(model.max_tokens, 4096),
                    "temperature": request.temperature or 0.1,
                    "messages": [
                        {
                            "role": "user",
                            "content": self._format_content_for_claude(request)
                        }
                    ]
                }
            
            elif model.provider == "Amazon":
                body = {
                    "inputText": request.content,
                    "textGenerationConfig": {
                        "maxTokenCount": request.max_tokens or min(model.max_tokens, 4096),
                        "temperature": request.temperature or 0.1,
                        "topP": 0.9
                    }
                }
            
            elif model.provider == "AI21 Labs":
                body = {
                    "prompt": request.content,
                    "maxTokens": request.max_tokens or min(model.max_tokens, 4096),
                    "temperature": request.temperature or 0.1,
                    "topP": 0.9
                }
            
            else:
                raise ValueError(f"Unsupported model provider: {model.provider}")
            
            bedrock_request["body"] = json.dumps(body)
            return bedrock_request
            
        except Exception as e:
            logger.error(f"Error preparing Bedrock request: {e}")
            raise
    
    def _format_content_for_claude(self, request: AIRequest) -> str:
        """Format content specifically for Claude models"""
        content = request.content
        
        # Add context if provided
        if request.context:
            context_str = json.dumps(request.context, indent=2)
            content = f"Context:\n{context_str}\n\nRequest:\n{content}"
        
        # Add task-specific instructions
        task_instructions = {
            "cost_analysis": "Analyze the provided cost data and provide actionable insights. Focus on trends, anomalies, and optimization opportunities.",
            "decision_proposal": "Create a structured decision proposal with clear recommendations, impact analysis, and implementation steps.",
            "report_generation": "Generate a comprehensive report with clear sections, data analysis, and actionable conclusions.",
            "conversation": "Respond naturally and helpfully to the user's query. Be concise but informative.",
            "summarization": "Provide a clear, concise summary highlighting the key points and important details."
        }
        
        if request.task_type in task_instructions:
            instruction = task_instructions[request.task_type]
            content = f"{instruction}\n\n{content}"
        
        return content
    
    async def _invoke_bedrock_model(
        self, 
        bedrock_request: Dict[str, Any], 
        model: ModelConfiguration
    ) -> Dict[str, Any]:
        """Invoke Bedrock model with retry logic"""
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                response = self.bedrock_client.invoke_model(**bedrock_request)
                return response
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Bedrock API call failed (attempt {attempt + 1}): {e}")
                    await asyncio.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    logger.error(f"Bedrock API call failed after {max_retries} attempts: {e}")
                    raise
    
    async def _process_bedrock_response(
        self, 
        response: Dict[str, Any], 
        model: ModelConfiguration,
        start_time: datetime,
        request: AIRequest
    ) -> AIResponse:
        """Process Bedrock API response"""
        try:
            # Read response body
            response_body = json.loads(response['body'].read())
            
            # Extract content based on model provider
            if model.provider == "Anthropic":
                content = response_body['content'][0]['text']
                input_tokens = response_body['usage']['input_tokens']
                output_tokens = response_body['usage']['output_tokens']
            
            elif model.provider == "Amazon":
                content = response_body['results'][0]['outputText']
                input_tokens = response_body.get('inputTextTokenCount', 0)
                output_tokens = response_body.get('results', [{}])[0].get('tokenCount', 0)
            
            elif model.provider == "AI21 Labs":
                content = response_body['completions'][0]['data']['text']
                input_tokens = response_body.get('prompt', {}).get('tokens', 0)
                output_tokens = response_body['completions'][0].get('data', {}).get('tokens', 0)
            
            else:
                raise ValueError(f"Unsupported model provider: {model.provider}")
            
            # Calculate metrics
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            cost_estimate = self._calculate_cost(model, input_tokens, output_tokens)
            
            # Create response
            ai_response = AIResponse(
                content=content,
                model_used=model.name,
                tokens_used={
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens
                },
                cost_estimate=cost_estimate,
                processing_time_ms=processing_time,
                metadata={
                    "model_id": model.model_id,
                    "provider": model.provider,
                    "task_type": request.task_type,
                    "complexity": request.complexity.value,
                    "agent_id": request.agent_id,
                    "correlation_id": request.correlation_id
                }
            )
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Error processing Bedrock response: {e}")
            raise
    
    def _calculate_cost(self, model: ModelConfiguration, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for API call"""
        input_cost = (input_tokens / 1000) * model.cost_per_1k_input_tokens
        output_cost = (output_tokens / 1000) * model.cost_per_1k_output_tokens
        return input_cost + output_cost
    
    async def _update_usage_stats(
        self, 
        request: AIRequest, 
        response: AIResponse, 
        model: ModelConfiguration
    ) -> None:
        """Update usage statistics"""
        try:
            # Update global stats
            self.usage_stats["total_requests"] += 1
            self.usage_stats["total_cost"] += response.cost_estimate
            
            # Update model usage
            model_key = model.model_id
            if model_key not in self.usage_stats["model_usage"]:
                self.usage_stats["model_usage"][model_key] = {
                    "requests": 0,
                    "total_cost": 0.0,
                    "total_tokens": 0,
                    "avg_response_time": 0.0
                }
            
            model_stats = self.usage_stats["model_usage"][model_key]
            model_stats["requests"] += 1
            model_stats["total_cost"] += response.cost_estimate
            model_stats["total_tokens"] += response.tokens_used["total_tokens"]
            
            # Update average response time
            current_avg = model_stats["avg_response_time"]
            new_avg = (current_avg * (model_stats["requests"] - 1) + response.processing_time_ms) / model_stats["requests"]
            model_stats["avg_response_time"] = new_avg
            
            # Update agent usage
            if request.agent_id:
                agent_key = request.agent_id
                if agent_key not in self.usage_stats["agent_usage"]:
                    self.usage_stats["agent_usage"][agent_key] = {
                        "requests": 0,
                        "total_cost": 0.0,
                        "preferred_models": {}
                    }
                
                agent_stats = self.usage_stats["agent_usage"][agent_key]
                agent_stats["requests"] += 1
                agent_stats["total_cost"] += response.cost_estimate
                
                # Track preferred models
                if model_key not in agent_stats["preferred_models"]:
                    agent_stats["preferred_models"][model_key] = 0
                agent_stats["preferred_models"][model_key] += 1
            
            # Update performance cache
            cache_key = f"{model.model_id}_{request.task_type}"
            if cache_key not in self.model_performance_cache:
                self.model_performance_cache[cache_key] = {
                    "requests": 0,
                    "total_response_time": 0.0,
                    "total_cost": 0.0,
                    "success_count": 0
                }
            
            perf_data = self.model_performance_cache[cache_key]
            perf_data["requests"] += 1
            perf_data["total_response_time"] += response.processing_time_ms
            perf_data["total_cost"] += response.cost_estimate
            perf_data["success_count"] += 1
            
            # Calculate averages
            perf_data["avg_response_time"] = perf_data["total_response_time"] / perf_data["requests"]
            perf_data["avg_cost"] = perf_data["total_cost"] / perf_data["requests"]
            perf_data["success_rate"] = perf_data["success_count"] / perf_data["requests"]
            
        except Exception as e:
            logger.error(f"Error updating usage stats: {e}")
    
    async def get_usage_statistics(self) -> Dict[str, Any]:
        """Get comprehensive usage statistics"""
        try:
            stats = self.usage_stats.copy()
            
            # Add derived metrics
            if stats["total_requests"] > 0:
                stats["average_cost_per_request"] = stats["total_cost"] / stats["total_requests"]
            else:
                stats["average_cost_per_request"] = 0.0
            
            # Add model performance rankings
            model_rankings = []
            for model_id, model_stats in stats["model_usage"].items():
                if model_stats["requests"] > 0:
                    model_rankings.append({
                        "model_id": model_id,
                        "model_name": next((m.name for m in self.models.values() if m.model_id == model_id), model_id),
                        "requests": model_stats["requests"],
                        "total_cost": model_stats["total_cost"],
                        "avg_cost_per_request": model_stats["total_cost"] / model_stats["requests"],
                        "avg_response_time": model_stats["avg_response_time"]
                    })
            
            # Sort by usage
            model_rankings.sort(key=lambda x: x["requests"], reverse=True)
            stats["model_rankings"] = model_rankings
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting usage statistics: {e}")
            return {"error": str(e)}
    
    async def optimize_costs(self) -> Dict[str, Any]:
        """Analyze usage and provide cost optimization recommendations"""
        try:
            stats = await self.get_usage_statistics()
            recommendations = []
            
            # Analyze model usage patterns
            for model_ranking in stats.get("model_rankings", []):
                model_id = model_ranking["model_id"]
                avg_cost = model_ranking["avg_cost_per_request"]
                
                # Find cheaper alternatives
                current_model = next((m for m in self.models.values() if m.model_id == model_id), None)
                if current_model:
                    cheaper_alternatives = [
                        m for m in self.models.values()
                        if (m.cost_per_1k_input_tokens + m.cost_per_1k_output_tokens) < 
                           (current_model.cost_per_1k_input_tokens + current_model.cost_per_1k_output_tokens)
                        and any(cap in m.capabilities for cap in current_model.capabilities)
                    ]
                    
                    if cheaper_alternatives:
                        cheapest = min(cheaper_alternatives, 
                                     key=lambda m: m.cost_per_1k_input_tokens + m.cost_per_1k_output_tokens)
                        
                        potential_savings = (avg_cost * 0.3) * model_ranking["requests"]  # Estimate 30% savings
                        
                        recommendations.append({
                            "type": "model_substitution",
                            "current_model": current_model.name,
                            "recommended_model": cheapest.name,
                            "potential_monthly_savings": potential_savings,
                            "description": f"Consider using {cheapest.name} for simpler tasks to reduce costs"
                        })
            
            # Analyze agent usage patterns
            for agent_id, agent_stats in stats.get("agent_usage", {}).items():
                if agent_stats["total_cost"] > 10.0:  # Focus on high-cost agents
                    recommendations.append({
                        "type": "agent_optimization",
                        "agent_id": agent_id,
                        "current_monthly_cost": agent_stats["total_cost"],
                        "description": f"Agent {agent_id} has high AI usage costs. Consider optimizing prompts or using cheaper models for routine tasks."
                    })
            
            return {
                "total_monthly_cost": stats["total_cost"],
                "optimization_recommendations": recommendations,
                "potential_total_savings": sum(r.get("potential_monthly_savings", 0) for r in recommendations)
            }
            
        except Exception as e:
            logger.error(f"Error optimizing costs: {e}")
            return {"error": str(e)}
    
    def get_model_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """Get information about available models and their capabilities"""
        return {
            model_key: {
                "name": model.name,
                "provider": model.provider,
                "capabilities": [cap.value for cap in model.capabilities],
                "complexity_rating": model.complexity_rating.value,
                "cost_per_1k_input_tokens": model.cost_per_1k_input_tokens,
                "cost_per_1k_output_tokens": model.cost_per_1k_output_tokens,
                "max_tokens": model.max_tokens,
                "context_window": model.context_window,
                "recommended_use_cases": model.recommended_use_cases
            }
            for model_key, model in self.models.items()
        }


# Convenience functions for different agent types
class AgentAIInterface:
    """
    Simplified AI interface for agents
    """
    
    def __init__(self, bedrock_manager: EnhancedBedrockManager, agent_id: str):
        self.bedrock_manager = bedrock_manager
        self.agent_id = agent_id
    
    async def analyze_data(self, data: Dict[str, Any], analysis_type: str = "general") -> str:
        """Analyze data and provide insights"""
        request = AIRequest(
            task_type="cost_analysis" if "cost" in analysis_type else "analysis",
            content=f"Analyze the following data and provide insights:\n\n{json.dumps(data, indent=2)}",
            complexity=TaskComplexity.MODERATE,
            agent_id=self.agent_id
        )
        
        response = await self.bedrock_manager.process_ai_request(request)
        return response.content
    
    async def generate_report(self, data: Dict[str, Any], report_type: str) -> str:
        """Generate a report based on data"""
        request = AIRequest(
            task_type="report_generation",
            content=f"Generate a {report_type} report based on the following data:\n\n{json.dumps(data, indent=2)}",
            complexity=TaskComplexity.MODERATE,
            agent_id=self.agent_id
        )
        
        response = await self.bedrock_manager.process_ai_request(request)
        return response.content
    
    async def create_decision_proposal(self, context: Dict[str, Any], recommendation: str) -> str:
        """Create a structured decision proposal"""
        request = AIRequest(
            task_type="decision_proposal",
            content=f"Create a decision proposal for: {recommendation}",
            context=context,
            complexity=TaskComplexity.COMPLEX,
            agent_id=self.agent_id
        )
        
        response = await self.bedrock_manager.process_ai_request(request)
        return response.content
    
    async def chat_response(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate conversational response"""
        request = AIRequest(
            task_type="conversation",
            content=message,
            context=context,
            complexity=TaskComplexity.SIMPLE,
            agent_id=self.agent_id
        )
        
        response = await self.bedrock_manager.process_ai_request(request)
        return response.content