"""
Dependency Injection Container
Manages object creation and dependencies
Following Dependency Inversion Principle
"""

import logging
from typing import Dict, Any

from ..core.interfaces import (
    ICostDataProvider, IResourceProvider, IForecastingService, 
    IAIAssistant, IAuthenticationService, IForecastingAIAssistant,
    IAWSPricingProvider, IQueryParser, ICostEstimationEngine
)
from ..infrastructure.aws_cost_provider import AWSCostProvider
from ..infrastructure.aws_resource_provider import AWSResourceProvider
from ..infrastructure.bedrock_ai_assistant import BedrockAIAssistant
from ..infrastructure.aws_session_factory import AWSSessionFactory, AWSAuthenticationService
from ..infrastructure.sqlite_repository import SQLiteRepository
from ..infrastructure.aws_pricing_provider import AWSPricingProvider
from ..infrastructure.forecasting_bedrock_assistant import ForecastingBedrockAssistant
from ..services.cost_service import CostAnalysisService
from ..services.resource_service import ResourceManagementService
from ..services.query_parser import NaturalLanguageQueryParser
from ..services.cost_estimation_engine import CostEstimationEngine
from ..services.forecasting_ai_assistant import ForecastingAIAssistant
from .use_cases import (
    GetUsageSummaryUseCase, AnalyzeScenarioUseCase, 
    GetCostInsightsUseCase, HandleChatUseCase, GetResourceDetailsUseCase
)

logger = logging.getLogger(__name__)


class SimpleForecastingService(IForecastingService):
    """Enhanced forecasting implementation using real Cost Explorer data"""
    
    async def generate_forecast(self, historical_data):
        from ..core.models import CostForecast
        import logging
        
        logger = logging.getLogger(__name__)
        
        if not historical_data:
            logger.warning("No historical data available for forecasting")
            return CostForecast(
                forecasted_amount=0.0,
                confidence_level=0.0,
                forecast_period_days=30,
                base_amount=0.0,
                trend_factor=1.0,
                daily_growth_rate=0.0
            )
        
        # Use the most recent month as base
        recent_amount = historical_data[-1].amount
        logger.info(f"Base amount for forecast: ${recent_amount:.2f}")
        
        # Calculate trend using multiple data points for better accuracy
        if len(historical_data) >= 3:
            # Use weighted average of recent trends
            trends = []
            for i in range(len(historical_data) - 1, 0, -1):
                current = historical_data[i].amount
                previous = historical_data[i-1].amount
                if previous > 0:
                    month_growth = (current - previous) / previous
                    trends.append(month_growth)
            
            if trends:
                # Weight recent trends more heavily
                weights = [2**i for i in range(len(trends))]
                weighted_growth = sum(t * w for t, w in zip(trends, weights)) / sum(weights)
            else:
                weighted_growth = 0.0
                
        elif len(historical_data) == 2:
            # Simple month-over-month growth
            current = historical_data[-1].amount
            previous = historical_data[-2].amount
            weighted_growth = (current - previous) / previous if previous > 0 else 0.0
        else:
            # Single data point - use conservative growth based on service type analysis
            weighted_growth = 0.02  # 2% monthly growth for established accounts
        
        # Apply realistic bounds and adjust for Cost Explorer usage patterns
        # Cost Explorer API calls tend to be consistent, so cap growth
        weighted_growth = max(-0.3, min(weighted_growth, 0.5))  # Between -30% and 50%
        
        # Calculate daily growth rate for timeline predictions
        daily_growth_rate = weighted_growth / 30
        
        # Project 30-day forecast with compound growth
        forecasted_amount = recent_amount * (1 + weighted_growth)
        
        # Calculate confidence based on data quality and consistency
        confidence = 0.5  # Base confidence
        if len(historical_data) >= 3:
            confidence += 0.2  # More data points
        if len(historical_data) >= 6:
            confidence += 0.2  # Full 6-month history
        
        # Adjust confidence based on trend consistency
        if len(historical_data) >= 2:
            # Check if trend is consistent (low variance)
            amounts = [d.amount for d in historical_data[-3:]]  # Last 3 months
            if len(amounts) >= 2:
                avg_amount = sum(amounts) / len(amounts)
                variance = sum((x - avg_amount) ** 2 for x in amounts) / len(amounts)
                if variance < (avg_amount * 0.1) ** 2:  # Low variance
                    confidence += 0.1
        
        confidence = min(0.95, confidence)  # Cap at 95%
        
        logger.info(f"Forecast: ${forecasted_amount:.2f} (growth: {weighted_growth*100:.1f}%, confidence: {confidence*100:.1f}%)")
        
        return CostForecast(
            forecasted_amount=forecasted_amount,
            confidence_level=confidence,
            forecast_period_days=30,
            base_amount=recent_amount,
            trend_factor=1 + weighted_growth,
            daily_growth_rate=daily_growth_rate
        )
    
    async def analyze_scenario(self, current_usage, scenario):
        from ..core.models import ScenarioResult
        # Basic scenario analysis
        additional_cost = (scenario.additional_ec2_instances * 120) + (scenario.additional_storage_gb * 0.10)
        new_total = current_usage.total_monthly_cost + additional_cost
        
        return ScenarioResult(
            scenario_input=scenario,
            projected_monthly_cost=new_total,
            cost_difference=additional_cost,
            budget_impact=max(0, new_total - current_usage.budget_info.total_budget),
            recommendations=[]
        )


class DependencyContainer:
    """Dependency injection container"""
    
    def __init__(self, config):
        self._config = config
        self._services: Dict[str, Any] = {}
        self._initialized = False
    
    def initialize(self):
        """Initialize all dependencies"""
        if self._initialized:
            return
        
        logger.info("Initializing dependency container")
        
        try:
            # Core infrastructure
            self._services['session_factory'] = AWSSessionFactory(self._config)
            aws_session = self._services['session_factory'].create_session()
            
            # Authentication
            self._services['auth_service'] = AWSAuthenticationService(
                self._services['session_factory']
            )
            
            # Data repository
            self._services['data_repository'] = SQLiteRepository()
            
            # Data providers
            self._services['cost_provider'] = AWSCostProvider(aws_session, self._config)
            self._services['resource_provider'] = AWSResourceProvider(aws_session)
            self._services['forecasting_service'] = SimpleForecastingService()
            self._services['ai_assistant'] = BedrockAIAssistant(
                aws_session, 
                self._config.BEDROCK_MODEL_ID
            )
            
            # Forecasting AI components
            self._services['pricing_provider'] = AWSPricingProvider(aws_session, self._config)
            self._services['query_parser'] = NaturalLanguageQueryParser()
            self._services['cost_estimation_engine'] = CostEstimationEngine()
            self._services['forecasting_bedrock_assistant'] = ForecastingBedrockAssistant(
                aws_session,
                self._config.BEDROCK_MODEL_ID
            )
            
            # Forecasting AI Assistant
            self._services['forecasting_ai_assistant'] = ForecastingAIAssistant(
                self._services['pricing_provider'],
                self._services['query_parser'],
                self._services['cost_estimation_engine'],
                self._services['ai_assistant']
            )
            
            # Application services
            self._services['cost_service'] = CostAnalysisService(
                self._services['cost_provider'],
                self._services['forecasting_service'],
                self._services['ai_assistant']
            )
            
            self._services['resource_service'] = ResourceManagementService(
                self._services['resource_provider']
            )
            
            # Use cases
            self._services['get_usage_summary_use_case'] = GetUsageSummaryUseCase(
                self._services['cost_service'],
                self._services['resource_service'],
                self._config
            )
            
            self._services['analyze_scenario_use_case'] = AnalyzeScenarioUseCase(
                self._services['resource_service']
            )
            
            self._services['get_cost_insights_use_case'] = GetCostInsightsUseCase(
                self._services['cost_service']
            )
            
            self._services['handle_chat_use_case'] = HandleChatUseCase(
                self._services['cost_service'],
                self._services['get_usage_summary_use_case']
            )
            
            self._services['get_resource_details_use_case'] = GetResourceDetailsUseCase(
                self._services['resource_service']
            )
            
            self._initialized = True
            logger.info("Dependency container initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing dependency container: {e}")
            raise
    
    def get(self, service_name: str) -> Any:
        """Get a service by name"""
        if not self._initialized:
            self.initialize()
        
        if service_name not in self._services:
            raise ValueError(f"Service '{service_name}' not found")
        
        return self._services[service_name]
    
    def get_use_case(self, use_case_name: str) -> Any:
        """Get a use case by name"""
        return self.get(f"{use_case_name}_use_case")
    
    async def health_check(self) -> Dict[str, bool]:
        """Perform health check on all services"""
        health_status = {}
        
        try:
            # Check authentication
            auth_service = self.get('auth_service')
            health_status['authentication'] = await auth_service.authenticate()
            
            # Check cost provider
            cost_provider = self.get('cost_provider')
            current_costs = await cost_provider.get_current_costs()
            health_status['cost_data'] = current_costs.amount >= 0
            
            # Check resource provider
            resource_provider = self.get('resource_provider')
            ec2_instances = await resource_provider.get_ec2_instances()
            health_status['resource_data'] = isinstance(ec2_instances, list)
            
            # Check AI assistant
            ai_assistant = self.get('ai_assistant')
            health_status['ai_assistant'] = ai_assistant._bedrock_client is not None
            
            # Check forecasting AI assistant
            try:
                forecasting_ai = self.get('forecasting_ai_assistant')
                health_status['forecasting_ai'] = forecasting_ai is not None
            except Exception:
                health_status['forecasting_ai'] = False
            
            # Check pricing provider
            try:
                pricing_provider = self.get('pricing_provider')
                health_status['pricing_provider'] = pricing_provider._pricing_client is not None
            except Exception:
                health_status['pricing_provider'] = False
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            health_status['error'] = str(e)
        
        return health_status