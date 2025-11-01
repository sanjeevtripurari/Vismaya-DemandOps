"""
Main AWS pricing service implementation
"""

import time
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..core.pricing_interfaces import (
    IPricingService, IAgentStrand, IPricingCache, IWebScraper,
    ServiceType, Region, ResourceSpec, CostEstimate, ServicePricing,
    ValidationResult, PricingError, DataSourceError
)
from ..infrastructure.pricing_cache import SQLitePricingCache
from ..infrastructure.pricing_error_handler import (
    robust_pricing_operation, performance_monitor, graceful_degradation
)
from ..infrastructure.pricing_logger import (
    log_pricing_operation, log_cache_operation, log_cost_calculation
)


class AWSPricingService(IPricingService):
    """Main implementation of AWS pricing service"""
    
    def __init__(self, cache: Optional[IPricingCache] = None):
        self.cache = cache or SQLitePricingCache()
        self.agent_strands: Dict[ServiceType, IAgentStrand] = {}
        self.web_scrapers: Dict[ServiceType, IWebScraper] = {}
        self._setup_fallback_strategies()
    
    def register_agent_strand(self, agent: IAgentStrand):
        """Register an agent strand for a specific service"""
        self.agent_strands[agent.service_type] = agent
    
    def register_web_scraper(self, service: ServiceType, scraper: IWebScraper):
        """Register a web scraper for a specific service"""
        self.web_scrapers[service] = scraper
    
    def _setup_fallback_strategies(self):
        """Setup fallback strategies for graceful degradation"""
        graceful_degradation.add_fallback(self._get_cached_pricing_fallback, priority=1)
        graceful_degradation.add_fallback(self._get_default_pricing_fallback, priority=2)
    
    @robust_pricing_operation
    async def get_service_pricing(self, service: ServiceType, region: Region) -> Optional[ServicePricing]:
        """Get pricing data for a specific service and region"""
        start_time = time.time()
        
        async with performance_monitor("get_service_pricing", {"service": service.value, "region": region.value}):
            try:
                # Try cache first
                cached_pricing = await self.cache.get_cached_pricing(service, region, max_age_hours=24)
                if cached_pricing:
                    log_cache_operation("get_pricing", hit=True, service=service.value, region=region.value)
                    return cached_pricing
                
                log_cache_operation("get_pricing", hit=False, service=service.value, region=region.value)
                
                # Try web scraping
                if service in self.web_scrapers:
                    pricing = await self._scrape_pricing_data(service, region)
                    if pricing:
                        # Cache the result
                        await self.cache.store_pricing(pricing)
                        return pricing
                
                # Try agent strand as fallback
                if service in self.agent_strands:
                    pricing = await self.agent_strands[service].get_pricing_data(region)
                    if pricing:
                        await self.cache.store_pricing(pricing)
                        return pricing
                
                # No pricing data available
                return None
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                log_pricing_operation("get_service_pricing", service.value, region.value, False, duration_ms)
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                log_pricing_operation("get_service_pricing", service.value, region.value, True, duration_ms)
    
    @robust_pricing_operation
    async def calculate_cost(self, resource_spec: ResourceSpec) -> CostEstimate:
        """Calculate cost estimate for a resource specification"""
        start_time = time.time()
        
        async with performance_monitor("calculate_cost", {
            "service": resource_spec.service_type.value,
            "instance_type": resource_spec.instance_type,
            "quantity": resource_spec.quantity,
            "duration_months": resource_spec.duration_months
        }):
            try:
                # Generate cache key
                resource_hash = SQLitePricingCache.generate_resource_hash(resource_spec)
                
                # Check cache first
                cached_estimate = await self.cache.get_cost_estimate(resource_hash, max_age_hours=1)
                if cached_estimate:
                    log_cache_operation("get_estimate", hit=True, details={"resource_hash": resource_hash[:16]})
                    return cached_estimate
                
                log_cache_operation("get_estimate", hit=False, details={"resource_hash": resource_hash[:16]})
                
                # Use agent strand for calculation
                if resource_spec.service_type not in self.agent_strands:
                    raise PricingError(f"No agent strand available for service: {resource_spec.service_type.value}")
                
                agent = self.agent_strands[resource_spec.service_type]
                
                # Validate resource specification
                validation = await agent.validate_resource_spec(resource_spec)
                if not validation.is_valid:
                    raise ValidationError(f"Invalid resource specification: {', '.join(validation.errors)}")
                
                # Calculate cost
                estimate = await agent.estimate_cost(resource_spec)
                
                # Cache the result
                await self.cache.store_cost_estimate(resource_hash, estimate)
                
                # Log the calculation
                log_cost_calculation(
                    resource_spec.service_type.value,
                    resource_spec.instance_type or "N/A",
                    resource_spec.quantity,
                    resource_spec.duration_months,
                    estimate.total_cost,
                    estimate.confidence_level
                )
                
                return estimate
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                log_pricing_operation("calculate_cost", resource_spec.service_type.value, resource_spec.region.value, False, duration_ms)
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                log_pricing_operation("calculate_cost", resource_spec.service_type.value, resource_spec.region.value, True, duration_ms)
    
    @robust_pricing_operation
    async def refresh_pricing_data(self, service: ServiceType, region: Region) -> bool:
        """Refresh pricing data from external sources"""
        start_time = time.time()
        
        async with performance_monitor("refresh_pricing_data", {"service": service.value, "region": region.value}):
            try:
                success = False
                
                # Try web scraping first
                if service in self.web_scrapers:
                    pricing = await self._scrape_pricing_data(service, region)
                    if pricing:
                        await self.cache.store_pricing(pricing)
                        success = True
                
                # Try agent strand as backup
                if not success and service in self.agent_strands:
                    pricing = await self.agent_strands[service].get_pricing_data(region)
                    if pricing:
                        await self.cache.store_pricing(pricing)
                        success = True
                
                return success
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                log_pricing_operation("refresh_pricing_data", service.value, region.value, False, duration_ms)
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                log_pricing_operation("refresh_pricing_data", service.value, region.value, success, duration_ms)
    
    async def get_cached_pricing(self, service: ServiceType, region: Region, max_age_hours: int = 24) -> Optional[ServicePricing]:
        """Get cached pricing data if available and not expired"""
        return await self.cache.get_pricing(service, region, max_age_hours)
    
    async def _scrape_pricing_data(self, service: ServiceType, region: Region) -> Optional[ServicePricing]:
        """Scrape pricing data using registered web scraper"""
        if service not in self.web_scrapers:
            return None
        
        scraper = self.web_scrapers[service]
        
        # Get service-specific pricing URL
        pricing_url = self._get_pricing_url(service, region)
        if not pricing_url:
            return None
        
        try:
            pricing_entries = await scraper.scrape_pricing_page(pricing_url)
            
            if pricing_entries:
                return ServicePricing(
                    service=service,
                    region=region,
                    pricing_entries=pricing_entries,
                    effective_date=datetime.now(),
                    source_url=pricing_url,
                    metadata={"scraping_method": "web_scraper", "entries_count": len(pricing_entries)}
                )
            
        except Exception as e:
            # Log error but don't raise - this is a fallback operation
            from ..infrastructure.pricing_logger import log_error
            log_error("scrape_pricing_data", e, {"service": service.value, "region": region.value, "url": pricing_url})
        
        return None
    
    def _get_pricing_url(self, service: ServiceType, region: Region) -> Optional[str]:
        """Get AWS pricing URL for service and region"""
        base_urls = {
            ServiceType.EC2: "https://aws.amazon.com/ec2/pricing/on-demand/",
            ServiceType.RDS: "https://aws.amazon.com/rds/pricing/",
            ServiceType.S3: "https://aws.amazon.com/s3/pricing/",
            ServiceType.LAMBDA: "https://aws.amazon.com/lambda/pricing/",
            ServiceType.ELB: "https://aws.amazon.com/elasticloadbalancing/pricing/",
        }
        
        return base_urls.get(service)
    
    async def _get_cached_pricing_fallback(self, service: ServiceType, region: Region) -> Optional[ServicePricing]:
        """Fallback strategy: get cached pricing even if expired"""
        return await self.cache.get_pricing(service, region, max_age_hours=24*7)  # 1 week old data
    
    async def _get_default_pricing_fallback(self, service: ServiceType, region: Region) -> Optional[ServicePricing]:
        """Fallback strategy: return default/estimated pricing"""
        # This would return basic default pricing data
        # Implementation depends on requirements for offline capability
        return None
    
    async def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache statistics and health information"""
        return await self.cache.get_cache_stats()
    
    async def cleanup_expired_cache(self) -> int:
        """Clean up expired cache entries"""
        return await self.cache.cleanup_expired()
    
    def get_supported_services(self) -> List[ServiceType]:
        """Get list of supported AWS services"""
        return list(self.agent_strands.keys())
    
    def get_supported_regions(self) -> List[Region]:
        """Get list of supported AWS regions"""
        return list(Region)
    
    async def validate_resource_specification(self, resource_spec: ResourceSpec) -> ValidationResult:
        """Validate resource specification"""
        if resource_spec.service_type not in self.agent_strands:
            return ValidationResult(
                is_valid=False,
                errors=[f"Unsupported service type: {resource_spec.service_type.value}"]
            )
        
        agent = self.agent_strands[resource_spec.service_type]
        return await agent.validate_resource_spec(resource_spec)
    
    async def get_instance_types(self, service: ServiceType, region: Region) -> List[str]:
        """Get supported instance types for service and region"""
        if service not in self.agent_strands:
            return []
        
        agent = self.agent_strands[service]
        return agent.get_supported_instance_types(region)