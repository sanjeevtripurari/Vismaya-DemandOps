"""
Dependency Injection Container
Manages object creation and dependencies
Following Dependency Inversion Principle
"""

import logging
from typing import Dict, Any

from ..core.interfaces import (
    ICostDataProvider, IResourceProvider, IForecastingService, 
    IAIAssistant, IAuthenticationService
)
from ..infrastructure.aws_cost_provider import AWSCostProvider
from ..infrastructure.aws_resource_provider import AWSResourceProvider
from ..infrastructure.bedrock_ai_assistant import BedrockAIAssistant
from ..infrastructure.aws_session_factory import AWSSessionFactory, AWSAuthenticationService
from ..infrastructure.sqlite_repository import SQLiteRepository
from ..services.cost_service import CostAnalysisService
from ..services.resource_service import ResourceManagementService
from .use_cases import (
    GetUsageSummaryUseCase, AnalyzeScenarioUseCase, 
    GetCostInsightsUseCase, HandleChatUseCase, GetResourceDetailsUseCase
)

logger = logging.getLogger(__name__)


class SimpleForecastingService(IForecastingService):
    """Enhanced forecasting implementation with organic growth projections"""
    
    async def generate_forecast(self, historical_data):
        from ..core.models import CostForecast
        if not historical_data:
            return CostForecast(
                forecasted_amount=0.0,
                confidence_level=0.0,
                forecast_period_days=30,
                base_amount=0.0
            )
        
        # Calculate organic growth based on current usage patterns
        recent_amount = historical_data[-1].amount
        
        if len(historical_data) > 1:
            # Calculate trend from historical data
            previous_amount = historical_data[-2].amount
            growth_rate = (recent_amount - previous_amount) / previous_amount if previous_amount > 0 else 0
        else:
            # For single data point, assume minimal organic growth
            growth_rate = 0.05  # 5% monthly growth for new accounts
        
        # Cap growth rate to realistic bounds
        growth_rate = max(-0.5, min(growth_rate, 2.0))  # Between -50% and 200%
        
        # Calculate daily growth rate
        daily_growth_rate = growth_rate / 30
        
        # Project 30-day forecast with organic growth
        forecasted_amount = recent_amount * (1 + growth_rate)
        
        # Calculate confidence based on data availability
        confidence = min(0.9, 0.5 + (len(historical_data) * 0.1))
        
        return CostForecast(
            forecasted_amount=forecasted_amount,
            confidence_level=confidence,
            forecast_period_days=30,
            base_amount=recent_amount,
            trend_factor=1 + growth_rate,
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
                self._services['resource_service'],
                self._config.DEFAULT_BUDGET
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
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            health_status['error'] = str(e)
        
        return health_status