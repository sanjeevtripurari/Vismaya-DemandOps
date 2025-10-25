"""
AWS Pricing API Provider
Implements IAWSPricingProvider interface
Provides real-time AWS pricing data without hallucination
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio
from functools import lru_cache

from ..core.interfaces import IAWSPricingProvider
from ..core.models import (
    PricingData, ResourceType, PricingModel,
    PricingAPIError, PricingDataUnavailableError, 
    InvalidResourceSpecificationError, RateLimitExceededError
)

logger = logging.getLogger(__name__)


class AWSPricingProvider(IAWSPricingProvider):
    """AWS Pricing API implementation - Real data only, no hallucination"""
    
    def __init__(self, aws_session, config=None):
        self._session = aws_session
        self._config = config
        self._pricing_client = None
        self._cache = {}
        self._cache_ttl = 3600  # 1 hour cache TTL
        self._rate_limit_delay = 6  # 6 seconds between requests (10 per minute)
        self._last_request_time = {}
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize AWS Pricing client"""
        try:
            # AWS Pricing API is only available in us-east-1
            self._pricing_client = self._session.client('pricing', region_name='us-east-1')
            logger.info("AWS Pricing API client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize AWS Pricing client: {e}")
            self._pricing_client = None
    
    def _refresh_client_if_needed(self):
        """Refresh client if credentials are expired"""
        try:
            if self._pricing_client:
                # Test if current client works
                sts = self._session.client('sts')
                sts.get_caller_identity()
                logger.debug("AWS credentials are valid for pricing API")
        except Exception as e:
            error_str = str(e)
            if any(keyword in error_str for keyword in ['ExpiredToken', 'RequestExpired', 'TokenRefreshRequired']):
                logger.warning("AWS credentials expired, attempting refresh...")
                try:
                    from .aws_session_factory import AWSSessionFactory
                    session_factory = AWSSessionFactory(self._config)
                    self._session = session_factory.create_session()
                    self._initialize_client()
                    logger.info("✅ AWS session refreshed for pricing API")
                except Exception as refresh_error:
                    logger.error(f"❌ Failed to refresh AWS session: {refresh_error}")
                    self._pricing_client = None
                    raise PricingAPIError(f"AWS credential refresh failed: {refresh_error}")
            else:
                logger.error(f"AWS pricing client test failed: {e}")
                raise PricingAPIError(f"AWS pricing client error: {e}")
    
    async def _rate_limit_check(self, service_type: str):
        """Check and enforce rate limiting"""
        current_time = datetime.now()
        last_request = self._last_request_time.get(service_type)
        
        if last_request:
            time_since_last = (current_time - last_request).total_seconds()
            if time_since_last < self._rate_limit_delay:
                wait_time = self._rate_limit_delay - time_since_last
                logger.info(f"Rate limiting: waiting {wait_time:.1f}s for {service_type}")
                await asyncio.sleep(wait_time)
        
        self._last_request_time[service_type] = current_time
    
    def _get_cache_key(self, service: str, **kwargs) -> str:
        """Generate cache key for pricing data"""
        key_parts = [service]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        return "|".join(key_parts)
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Check if cache entry is still valid"""
        if not cache_entry:
            return False
        
        cache_time = cache_entry.get('timestamp')
        if not cache_time:
            return False
        
        age = (datetime.now() - cache_time).total_seconds()
        return age < self._cache_ttl
    
    def _get_from_cache(self, cache_key: str) -> Optional[PricingData]:
        """Get pricing data from cache if valid"""
        cache_entry = self._cache.get(cache_key)
        if self._is_cache_valid(cache_entry):
            logger.debug(f"Cache hit for {cache_key}")
            return cache_entry['data']
        return None
    
    def _store_in_cache(self, cache_key: str, pricing_data: PricingData):
        """Store pricing data in cache"""
        self._cache[cache_key] = {
            'data': pricing_data,
            'timestamp': datetime.now()
        }
        logger.debug(f"Cached pricing data for {cache_key}")
    
    async def get_ec2_pricing(self, instance_type: str, region: str, os: str = "Linux") -> PricingData:
        """Get EC2 instance pricing for all models (On-Demand, Reserved, Spot)"""
        try:
            # Check cache first
            cache_key = self._get_cache_key("ec2", instance_type=instance_type, region=region, os=os)
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            # Refresh client and check rate limits
            self._refresh_client_if_needed()
            await self._rate_limit_check("ec2")
            
            if not self._pricing_client:
                raise PricingDataUnavailableError("AWS Pricing API client not available")
            
            logger.info(f"Fetching real EC2 pricing for {instance_type} in {region} ({os})")
            
            # Build filters for AWS Pricing API
            filters = [
                {'Type': 'TERM_MATCH', 'Field': 'ServiceCode', 'Value': 'AmazonEC2'},
                {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
                {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': self._get_location_name(region)},
                {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': os},
                {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
                {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'NA'},
                {'Type': 'TERM_MATCH', 'Field': 'capacitystatus', 'Value': 'Used'}
            ]
            
            # Get On-Demand pricing
            response = self._pricing_client.get_products(
                ServiceCode='AmazonEC2',
                Filters=filters
            )
            
            pricing_data = PricingData(region=region, source="AWS Pricing API")
            
            # Parse On-Demand pricing
            if response.get('PriceList'):
                for price_item in response['PriceList']:
                    price_data = json.loads(price_item)
                    terms = price_data.get('terms', {})
                    
                    # Extract On-Demand pricing
                    on_demand_terms = terms.get('OnDemand', {})
                    for term_key, term_data in on_demand_terms.items():
                        price_dimensions = term_data.get('priceDimensions', {})
                        for dim_key, dim_data in price_dimensions.items():
                            price_per_unit = dim_data.get('pricePerUnit', {})
                            usd_price = price_per_unit.get('USD')
                            if usd_price:
                                pricing_data.on_demand_hourly = float(usd_price)
                                break
                        if pricing_data.on_demand_hourly:
                            break
                    
                    if pricing_data.on_demand_hourly:
                        break
            
            # Try to get Reserved Instance pricing (simplified - 1 year term)
            try:
                ri_filters = filters + [
                    {'Type': 'TERM_MATCH', 'Field': 'termType', 'Value': 'Reserved'}
                ]
                
                ri_response = self._pricing_client.get_products(
                    ServiceCode='AmazonEC2',
                    Filters=ri_filters
                )
                
                # Parse Reserved Instance pricing (this is complex, simplified version)
                if ri_response.get('PriceList'):
                    for price_item in ri_response['PriceList'][:1]:  # Just take first match
                        price_data = json.loads(price_item)
                        terms = price_data.get('terms', {})
                        
                        reserved_terms = terms.get('Reserved', {})
                        for term_key, term_data in reserved_terms.items():
                            price_dimensions = term_data.get('priceDimensions', {})
                            for dim_key, dim_data in price_dimensions.items():
                                price_per_unit = dim_data.get('pricePerUnit', {})
                                usd_price = price_per_unit.get('USD')
                                if usd_price and float(usd_price) > 0:
                                    # This is typically upfront cost, convert to monthly
                                    pricing_data.reserved_monthly = float(usd_price) / 12
                                    break
                            if pricing_data.reserved_monthly:
                                break
                        if pricing_data.reserved_monthly:
                            break
            
            except Exception as ri_error:
                logger.warning(f"Could not fetch Reserved Instance pricing: {ri_error}")
            
            # Note: Spot pricing is not available through Pricing API, would need EC2 API
            logger.info(f"✅ Retrieved EC2 pricing: On-Demand=${pricing_data.on_demand_hourly}/hr")
            
            # Cache the result
            self._store_in_cache(cache_key, pricing_data)
            
            return pricing_data
            
        except Exception as e:
            error_msg = f"Failed to fetch EC2 pricing for {instance_type}: {str(e)}"
            logger.error(error_msg)
            
            if 'AccessDenied' in str(e):
                raise PricingDataUnavailableError("Access denied to AWS Pricing API. Check IAM permissions for 'pricing:GetProducts'")
            elif 'Throttling' in str(e) or 'Rate' in str(e):
                raise RateLimitExceededError("AWS Pricing API rate limit exceeded. Please try again later.")
            else:
                raise PricingAPIError(error_msg)
    
    async def get_storage_pricing(self, storage_type: str, region: str) -> PricingData:
        """Get EBS/S3 storage pricing"""
        try:
            # Check cache first
            cache_key = self._get_cache_key("storage", storage_type=storage_type, region=region)
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            # Refresh client and check rate limits
            self._refresh_client_if_needed()
            await self._rate_limit_check("storage")
            
            if not self._pricing_client:
                raise PricingDataUnavailableError("AWS Pricing API client not available")
            
            logger.info(f"Fetching real storage pricing for {storage_type} in {region}")
            
            pricing_data = PricingData(region=region, source="AWS Pricing API")
            
            if storage_type.lower() in ['ebs', 'gp3', 'gp2', 'io1', 'io2']:
                # EBS pricing
                filters = [
                    {'Type': 'TERM_MATCH', 'Field': 'ServiceCode', 'Value': 'AmazonEC2'},
                    {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': self._get_location_name(region)},
                    {'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': 'Storage'},
                    {'Type': 'TERM_MATCH', 'Field': 'volumeType', 'Value': storage_type.upper()}
                ]
                
                response = self._pricing_client.get_products(
                    ServiceCode='AmazonEC2',
                    Filters=filters
                )
                
                # Parse EBS pricing (per GB-month)
                if response.get('PriceList'):
                    for price_item in response['PriceList'][:1]:
                        price_data = json.loads(price_item)
                        terms = price_data.get('terms', {})
                        
                        on_demand_terms = terms.get('OnDemand', {})
                        for term_key, term_data in on_demand_terms.items():
                            price_dimensions = term_data.get('priceDimensions', {})
                            for dim_key, dim_data in price_dimensions.items():
                                price_per_unit = dim_data.get('pricePerUnit', {})
                                usd_price = price_per_unit.get('USD')
                                if usd_price:
                                    # EBS pricing is per GB-month, store as monthly cost per GB
                                    pricing_data.reserved_monthly = float(usd_price)
                                    break
                            if pricing_data.reserved_monthly:
                                break
                        if pricing_data.reserved_monthly:
                            break
            
            elif storage_type.lower() == 's3':
                # S3 pricing
                filters = [
                    {'Type': 'TERM_MATCH', 'Field': 'ServiceCode', 'Value': 'AmazonS3'},
                    {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': self._get_location_name(region)},
                    {'Type': 'TERM_MATCH', 'Field': 'storageClass', 'Value': 'General Purpose'}
                ]
                
                response = self._pricing_client.get_products(
                    ServiceCode='AmazonS3',
                    Filters=filters
                )
                
                # Parse S3 pricing
                if response.get('PriceList'):
                    for price_item in response['PriceList'][:1]:
                        price_data = json.loads(price_item)
                        terms = price_data.get('terms', {})
                        
                        on_demand_terms = terms.get('OnDemand', {})
                        for term_key, term_data in on_demand_terms.items():
                            price_dimensions = term_data.get('priceDimensions', {})
                            for dim_key, dim_data in price_dimensions.items():
                                price_per_unit = dim_data.get('pricePerUnit', {})
                                usd_price = price_per_unit.get('USD')
                                if usd_price:
                                    # S3 pricing is per GB-month
                                    pricing_data.reserved_monthly = float(usd_price)
                                    break
                            if pricing_data.reserved_monthly:
                                break
                        if pricing_data.reserved_monthly:
                            break
            
            logger.info(f"✅ Retrieved storage pricing: {storage_type}=${pricing_data.reserved_monthly}/GB-month")
            
            # Cache the result
            self._store_in_cache(cache_key, pricing_data)
            
            return pricing_data
            
        except Exception as e:
            error_msg = f"Failed to fetch storage pricing for {storage_type}: {str(e)}"
            logger.error(error_msg)
            
            if 'AccessDenied' in str(e):
                raise PricingDataUnavailableError("Access denied to AWS Pricing API. Check IAM permissions for 'pricing:GetProducts'")
            elif 'Throttling' in str(e) or 'Rate' in str(e):
                raise RateLimitExceededError("AWS Pricing API rate limit exceeded. Please try again later.")
            else:
                raise PricingAPIError(error_msg)
    
    async def get_service_pricing(self, service: str, region: str, **kwargs) -> PricingData:
        """Get pricing for other AWS services"""
        try:
            # Check cache first
            cache_key = self._get_cache_key(service, region=region, **kwargs)
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            # Refresh client and check rate limits
            self._refresh_client_if_needed()
            await self._rate_limit_check(service)
            
            if not self._pricing_client:
                raise PricingDataUnavailableError("AWS Pricing API client not available")
            
            logger.info(f"Fetching real pricing for {service} in {region}")
            
            pricing_data = PricingData(region=region, source="AWS Pricing API")
            
            # Map service names to AWS service codes
            service_code_map = {
                'rds': 'AmazonRDS',
                'lambda': 'AWSLambda',
                'cloudwatch': 'AmazonCloudWatch',
                'bedrock': 'AmazonBedrock'
            }
            
            service_code = service_code_map.get(service.lower())
            if not service_code:
                raise InvalidResourceSpecificationError(f"Unsupported service: {service}")
            
            # Basic filters
            filters = [
                {'Type': 'TERM_MATCH', 'Field': 'ServiceCode', 'Value': service_code},
                {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': self._get_location_name(region)}
            ]
            
            # Add service-specific filters
            if service.lower() == 'rds':
                instance_class = kwargs.get('instance_class', 'db.t3.micro')
                engine = kwargs.get('engine', 'mysql')
                filters.extend([
                    {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_class},
                    {'Type': 'TERM_MATCH', 'Field': 'databaseEngine', 'Value': engine}
                ])
            
            response = self._pricing_client.get_products(
                ServiceCode=service_code,
                Filters=filters
            )
            
            # Parse pricing data
            if response.get('PriceList'):
                for price_item in response['PriceList'][:1]:  # Take first match
                    price_data = json.loads(price_item)
                    terms = price_data.get('terms', {})
                    
                    on_demand_terms = terms.get('OnDemand', {})
                    for term_key, term_data in on_demand_terms.items():
                        price_dimensions = term_data.get('priceDimensions', {})
                        for dim_key, dim_data in price_dimensions.items():
                            price_per_unit = dim_data.get('pricePerUnit', {})
                            usd_price = price_per_unit.get('USD')
                            if usd_price:
                                pricing_data.on_demand_hourly = float(usd_price)
                                break
                        if pricing_data.on_demand_hourly:
                            break
                    if pricing_data.on_demand_hourly:
                        break
            
            logger.info(f"✅ Retrieved {service} pricing: ${pricing_data.on_demand_hourly}/hr")
            
            # Cache the result
            self._store_in_cache(cache_key, pricing_data)
            
            return pricing_data
            
        except Exception as e:
            error_msg = f"Failed to fetch {service} pricing: {str(e)}"
            logger.error(error_msg)
            
            if 'AccessDenied' in str(e):
                raise PricingDataUnavailableError("Access denied to AWS Pricing API. Check IAM permissions for 'pricing:GetProducts'")
            elif 'Throttling' in str(e) or 'Rate' in str(e):
                raise RateLimitExceededError("AWS Pricing API rate limit exceeded. Please try again later.")
            else:
                raise PricingAPIError(error_msg)
    
    async def clear_cache(self) -> None:
        """Clear pricing data cache"""
        self._cache.clear()
        logger.info("Pricing data cache cleared")
    
    def _get_location_name(self, region: str) -> str:
        """Map AWS region code to location name used in Pricing API"""
        region_map = {
            'us-east-1': 'US East (N. Virginia)',
            'us-east-2': 'US East (Ohio)',
            'us-west-1': 'US West (N. California)',
            'us-west-2': 'US West (Oregon)',
            'eu-west-1': 'Europe (Ireland)',
            'eu-central-1': 'Europe (Frankfurt)',
            'ap-southeast-1': 'Asia Pacific (Singapore)',
            'ap-southeast-2': 'Asia Pacific (Sydney)',
            'ap-northeast-1': 'Asia Pacific (Tokyo)',
            'ca-central-1': 'Canada (Central)',
            'sa-east-1': 'South America (Sao Paulo)'
        }
        
        return region_map.get(region, region)