"""
Core interfaces for the cost-effective AWS pricing system
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum


class ServiceType(Enum):
    """AWS service types supported by the pricing system"""
    EC2 = "ec2"
    RDS = "rds"
    S3 = "s3"
    LAMBDA = "lambda"
    ELB = "elb"
    VPC = "vpc"
    CLOUDFRONT = "cloudfront"
    EBS = "ebs"


class Region(Enum):
    """AWS regions for pricing"""
    US_EAST_1 = "us-east-1"
    US_EAST_2 = "us-east-2"
    US_WEST_1 = "us-west-1"
    US_WEST_2 = "us-west-2"
    EU_WEST_1 = "eu-west-1"
    EU_CENTRAL_1 = "eu-central-1"
    AP_SOUTHEAST_1 = "ap-southeast-1"


@dataclass
class ResourceSpec:
    """Specification for AWS resource cost calculation"""
    service_type: ServiceType
    instance_type: Optional[str] = None
    quantity: int = 1
    duration_months: int = 1
    region: Region = Region.US_EAST_1
    additional_specs: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.additional_specs is None:
            self.additional_specs = {}


@dataclass
class CostBreakdown:
    """Detailed cost breakdown for a resource"""
    compute_cost: float = 0.0
    storage_cost: float = 0.0
    network_cost: float = 0.0
    additional_costs: Dict[str, float] = None
    
    def __post_init__(self):
        if self.additional_costs is None:
            self.additional_costs = {}
    
    @property
    def total_cost(self) -> float:
        """Calculate total cost from all components"""
        base_cost = self.compute_cost + self.storage_cost + self.network_cost
        additional_total = sum(self.additional_costs.values())
        return base_cost + additional_total


@dataclass
class CostEstimate:
    """Cost estimate result with confidence and metadata"""
    monthly_cost: float
    total_cost: float
    breakdown: CostBreakdown
    confidence_level: float  # 0.0 to 1.0
    last_updated: datetime
    source: str
    notes: List[str] = None
    
    def __post_init__(self):
        if self.notes is None:
            self.notes = []


@dataclass
class PriceEntry:
    """Individual pricing entry from AWS data"""
    service: ServiceType
    region: Region
    resource_type: str  # e.g., "t3.micro", "gp3", "standard"
    price_per_unit: float
    unit: str  # e.g., "hour", "GB-month", "request"
    currency: str = "USD"
    effective_date: datetime = None
    
    def __post_init__(self):
        if self.effective_date is None:
            self.effective_date = datetime.now()


@dataclass
class ServicePricing:
    """Complete pricing data for an AWS service"""
    service: ServiceType
    region: Region
    pricing_entries: List[PriceEntry]
    effective_date: datetime
    source_url: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def get_price(self, resource_type: str) -> Optional[PriceEntry]:
        """Get pricing entry for specific resource type"""
        for entry in self.pricing_entries:
            if entry.resource_type == resource_type:
                return entry
        return None


@dataclass
class ValidationResult:
    """Result of resource specification validation"""
    is_valid: bool
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class IPricingService(ABC):
    """Main interface for AWS pricing operations"""
    
    @abstractmethod
    async def get_service_pricing(self, service: ServiceType, region: Region) -> Optional[ServicePricing]:
        """Get pricing data for a specific service and region"""
        pass
    
    @abstractmethod
    async def calculate_cost(self, resource_spec: ResourceSpec) -> CostEstimate:
        """Calculate cost estimate for a resource specification"""
        pass
    
    @abstractmethod
    async def refresh_pricing_data(self, service: ServiceType, region: Region) -> bool:
        """Refresh pricing data from external sources"""
        pass
    
    @abstractmethod
    async def get_cached_pricing(self, service: ServiceType, region: Region, max_age_hours: int = 24) -> Optional[ServicePricing]:
        """Get cached pricing data if available and not expired"""
        pass


class IAgentStrand(ABC):
    """Base interface for service-specific pricing agents"""
    
    @property
    @abstractmethod
    def service_type(self) -> ServiceType:
        """The AWS service this agent handles"""
        pass
    
    @abstractmethod
    async def estimate_cost(self, resource_spec: ResourceSpec) -> CostEstimate:
        """Estimate cost for the given resource specification"""
        pass
    
    @abstractmethod
    async def get_pricing_data(self, region: Region) -> ServicePricing:
        """Get current pricing data for this service"""
        pass
    
    @abstractmethod
    async def validate_resource_spec(self, spec: ResourceSpec) -> ValidationResult:
        """Validate that the resource specification is correct for this service"""
        pass
    
    @abstractmethod
    def get_supported_instance_types(self, region: Region) -> List[str]:
        """Get list of supported instance types for this service and region"""
        pass


class IWebScraper(ABC):
    """Interface for web scraping AWS pricing data"""
    
    @abstractmethod
    async def scrape_pricing_page(self, url: str) -> List[PriceEntry]:
        """Scrape pricing data from AWS pricing page"""
        pass
    
    @abstractmethod
    async def parse_pricing_table(self, html: str, service: ServiceType, region: Region) -> List[PriceEntry]:
        """Parse HTML pricing table into structured data"""
        pass
    
    @abstractmethod
    async def validate_pricing_data(self, entries: List[PriceEntry]) -> ValidationResult:
        """Validate scraped pricing data for consistency"""
        pass


class IPricingCache(ABC):
    """Interface for pricing data caching operations"""
    
    @abstractmethod
    async def store_pricing(self, pricing: ServicePricing) -> bool:
        """Store pricing data in cache"""
        pass
    
    @abstractmethod
    async def get_pricing(self, service: ServiceType, region: Region, max_age_hours: int = 24) -> Optional[ServicePricing]:
        """Retrieve pricing data from cache"""
        pass
    
    @abstractmethod
    async def store_cost_estimate(self, resource_hash: str, estimate: CostEstimate) -> bool:
        """Store cost estimate in cache"""
        pass
    
    @abstractmethod
    async def get_cost_estimate(self, resource_hash: str, max_age_hours: int = 1) -> Optional[CostEstimate]:
        """Retrieve cost estimate from cache"""
        pass
    
    @abstractmethod
    async def cleanup_expired(self) -> int:
        """Remove expired cache entries, return count of removed items"""
        pass
    
    @abstractmethod
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics and health information"""
        pass


class PricingError(Exception):
    """Base exception for pricing system errors"""
    pass


class DataSourceError(PricingError):
    """Error accessing external data sources"""
    pass


class ValidationError(PricingError):
    """Error in resource specification validation"""
    pass


class CacheError(PricingError):
    """Error in cache operations"""
    pass