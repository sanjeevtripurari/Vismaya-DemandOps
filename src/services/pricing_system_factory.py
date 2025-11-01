"""
Factory for creating and configuring the pricing system
"""

from typing import Optional
from ..core.pricing_interfaces import IPricingService, ServiceType
from ..infrastructure.pricing_cache import SQLitePricingCache
from .aws_pricing_service import AWSPricingService


class PricingSystemFactory:
    """Factory for creating configured pricing system instances"""
    
    @staticmethod
    def create_pricing_service(cache_db_path: Optional[str] = None) -> IPricingService:
        """Create a fully configured pricing service"""
        # Create cache
        cache = SQLitePricingCache(cache_db_path or "data/pricing_cache.db")
        
        # Create main service
        pricing_service = AWSPricingService(cache)
        
        # Register agent strands (will be implemented in subsequent tasks)
        # pricing_service.register_agent_strand(EC2Agent())
        # pricing_service.register_agent_strand(RDSAgent())
        # pricing_service.register_agent_strand(S3Agent())
        
        # Register web scrapers (will be implemented in subsequent tasks)
        # pricing_service.register_web_scraper(ServiceType.EC2, EC2WebScraper())
        # pricing_service.register_web_scraper(ServiceType.RDS, RDSWebScraper())
        # pricing_service.register_web_scraper(ServiceType.S3, S3WebScraper())
        
        return pricing_service
    
    @staticmethod
    def create_test_pricing_service() -> IPricingService:
        """Create pricing service for testing with in-memory cache"""
        cache = SQLitePricingCache(":memory:")
        return AWSPricingService(cache)


# Global instance for easy access
_pricing_service_instance: Optional[IPricingService] = None


def get_pricing_service() -> IPricingService:
    """Get global pricing service instance"""
    global _pricing_service_instance
    
    if _pricing_service_instance is None:
        _pricing_service_instance = PricingSystemFactory.create_pricing_service()
    
    return _pricing_service_instance


def initialize_pricing_system(cache_db_path: Optional[str] = None) -> IPricingService:
    """Initialize the global pricing system"""
    global _pricing_service_instance
    
    _pricing_service_instance = PricingSystemFactory.create_pricing_service(cache_db_path)
    return _pricing_service_instance