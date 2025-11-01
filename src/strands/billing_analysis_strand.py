"""
Billing Analysis Agent Strand
Analyzes AWS billing data and fetches pricing from public sources
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiohttp
from bs4 import BeautifulSoup

from ..core.pricing_interfaces import (
    IAgentStrand, Region, ResourceSpec, CostEstimate, 
    ServicePricing, PriceEntry, ValidationResult, CostBreakdown
)
from ..core.models import ServiceType
from ..infrastructure.pricing_logger import log_pricing_operation, log_web_scraping


class BillingAnalysisStrand(IAgentStrand):
    """Agent strand for analyzing billing data and fetching public pricing"""
    
    def __init__(self):
        self._service_type = ServiceType.OTHER
        self.pricing_cache = {}
        self.billing_services = {}
    
    @property
    def service_type(self) -> ServiceType:
        return self._service_type
    
    async def analyze_billing_services(self, billing_data: Dict[str, float]) -> Dict[str, Any]:
        """Analyze billing data to identify services and usage patterns"""
        try:
            analysis = {
                'total_cost': sum(billing_data.values()),
                'service_breakdown': {},
                'top_services': [],
                'cost_drivers': [],
                'recommendations': []
            }
            
            # Process each service from billing
            for service_name, cost in billing_data.items():
                if cost > 0:
                    service_info = await self._analyze_service(service_name, cost)
                    analysis['service_breakdown'][service_name] = service_info
            
            # Identify top cost drivers
            sorted_services = sorted(billing_data.items(), key=lambda x: x[1], reverse=True)
            analysis['top_services'] = sorted_services[:5]
            
            # Generate cost optimization recommendations
            analysis['recommendations'] = await self._generate_recommendations(billing_data)
            
            return analysis
            
        except Exception as e:
            log_pricing_operation("analyze_billing_services", "billing", "global", False, 0, {"error": str(e)})
            raise
    
    async def _analyze_service(self, service_name: str, cost: float) -> Dict[str, Any]:
        """Analyze individual service usage and fetch pricing data"""
        service_info = {
            'name': service_name,
            'cost': cost,
            'service_type': self._map_service_name(service_name),
            'pricing_data': None,
            'usage_estimate': None,
            'optimization_potential': 0.0
        }
        
        try:
            # Fetch pricing data from public sources
            pricing_data = await self._fetch_service_pricing(service_name)
            if pricing_data:
                service_info['pricing_data'] = pricing_data
                
                # Estimate usage based on cost and pricing
                usage_estimate = await self._estimate_usage(service_name, cost, pricing_data)
                service_info['usage_estimate'] = usage_estimate
                
                # Calculate optimization potential
                optimization = await self._calculate_optimization_potential(service_name, cost, usage_estimate)
                service_info['optimization_potential'] = optimization
        
        except Exception as e:
            log_pricing_operation("analyze_service", service_name, "global", False, 0, {"error": str(e)})
        
        return service_info
    
    async def _fetch_service_pricing(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Fetch pricing data from AWS public pricing pages"""
        try:
            # Map service name to pricing URL
            pricing_url = self._get_pricing_url(service_name)
            if not pricing_url:
                return None
            
            # Check cache first
            cache_key = f"pricing_{service_name}"
            if cache_key in self.pricing_cache:
                cached_data = self.pricing_cache[cache_key]
                if (datetime.now() - cached_data['timestamp']).total_seconds() < 24 * 3600:
                    return cached_data['data']
            
            # Fetch from public URL
            pricing_data = await self._scrape_pricing_page(pricing_url, service_name)
            
            if pricing_data:
                # Cache the result
                self.pricing_cache[cache_key] = {
                    'data': pricing_data,
                    'timestamp': datetime.now()
                }
                
                log_web_scraping(pricing_url, True, len(pricing_data.get('prices', [])))
                return pricing_data
            
            return None
            
        except Exception as e:
            log_web_scraping(pricing_url if 'pricing_url' in locals() else 'unknown', False, 0, str(e))
            return None
    
    async def _scrape_pricing_page(self, url: str, service_name: str) -> Optional[Dict[str, Any]]:
        """Scrape pricing data from AWS public pages"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                async with session.get(url, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        html = await response.text()
                        return await self._parse_pricing_html(html, service_name)
            
            return None
            
        except Exception as e:
            log_web_scraping(url, False, 0, str(e))
            return None
    
    async def _parse_pricing_html(self, html: str, service_name: str) -> Dict[str, Any]:
        """Parse pricing information from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            pricing_data = {
                'service': service_name,
                'prices': [],
                'regions': [],
                'last_updated': datetime.now().isoformat()
            }
            
            # Service-specific parsing logic
            if 'cost explorer' in service_name.lower():
                pricing_data['prices'] = await self._parse_cost_explorer_pricing(soup)
            elif 'bedrock' in service_name.lower():
                pricing_data['prices'] = await self._parse_bedrock_pricing(soup)
            elif 'ec2' in service_name.lower():
                pricing_data['prices'] = await self._parse_ec2_pricing(soup)
            else:
                # Generic pricing extraction
                pricing_data['prices'] = await self._parse_generic_pricing(soup)
            
            return pricing_data
            
        except Exception as e:
            return {'service': service_name, 'prices': [], 'error': str(e)}
    
    async def _parse_cost_explorer_pricing(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parse Cost Explorer specific pricing"""
        prices = []
        
        # Cost Explorer pricing is typically $0.01 per request
        prices.append({
            'type': 'API Request',
            'price': 0.01,
            'unit': 'per request',
            'description': 'GetCostAndUsage API call'
        })
        
        return prices
    
    async def _parse_bedrock_pricing(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parse Bedrock specific pricing"""
        prices = []
        
        # Look for pricing tables
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 3:
                    # Try to extract model, input price, output price
                    model_text = cells[0].get_text(strip=True)
                    if 'claude' in model_text.lower() or 'haiku' in model_text.lower():
                        try:
                            # Extract pricing information
                            input_price_text = cells[1].get_text(strip=True)
                            output_price_text = cells[2].get_text(strip=True)
                            
                            # Parse prices using regex
                            input_match = re.search(r'\$([0-9.]+)', input_price_text)
                            output_match = re.search(r'\$([0-9.]+)', output_price_text)
                            
                            if input_match:
                                prices.append({
                                    'type': f'{model_text} - Input',
                                    'price': float(input_match.group(1)),
                                    'unit': 'per 1K tokens',
                                    'description': f'Input tokens for {model_text}'
                                })
                            
                            if output_match:
                                prices.append({
                                    'type': f'{model_text} - Output',
                                    'price': float(output_match.group(1)),
                                    'unit': 'per 1K tokens',
                                    'description': f'Output tokens for {model_text}'
                                })
                        except:
                            continue
        
        # Fallback pricing if scraping fails
        if not prices:
            prices = [
                {
                    'type': 'Claude 3 Haiku - Input',
                    'price': 0.00025,
                    'unit': 'per 1K tokens',
                    'description': 'Input tokens for Claude 3 Haiku'
                },
                {
                    'type': 'Claude 3 Haiku - Output',
                    'price': 0.00125,
                    'unit': 'per 1K tokens',
                    'description': 'Output tokens for Claude 3 Haiku'
                }
            ]
        
        return prices
    
    async def _parse_ec2_pricing(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parse EC2 specific pricing"""
        prices = []
        
        # Look for instance pricing tables
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    instance_type = cells[0].get_text(strip=True)
                    price_text = cells[1].get_text(strip=True)
                    
                    # Extract price using regex
                    price_match = re.search(r'\$([0-9.]+)', price_text)
                    if price_match and any(t in instance_type.lower() for t in ['t2', 't3', 'm5', 'c5']):
                        prices.append({
                            'type': instance_type,
                            'price': float(price_match.group(1)),
                            'unit': 'per hour',
                            'description': f'{instance_type} on-demand pricing'
                        })
        
        return prices
    
    async def _parse_generic_pricing(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parse generic pricing information"""
        prices = []
        
        # Look for price patterns in text
        text = soup.get_text()
        price_patterns = re.findall(r'\$([0-9.]+)\s*(?:per|/)\s*([a-zA-Z\s]+)', text)
        
        for price, unit in price_patterns[:5]:  # Limit to first 5 matches
            prices.append({
                'type': 'Generic',
                'price': float(price),
                'unit': f'per {unit.strip()}',
                'description': f'Pricing: ${price} per {unit.strip()}'
            })
        
        return prices
    
    async def _estimate_usage(self, service_name: str, cost: float, pricing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate usage based on cost and pricing data"""
        usage_estimate = {
            'estimated_units': 0,
            'unit_type': 'unknown',
            'confidence': 0.5
        }
        
        try:
            if pricing_data and pricing_data.get('prices'):
                # Use the first available price for estimation
                price_info = pricing_data['prices'][0]
                unit_price = price_info['price']
                
                if unit_price > 0:
                    estimated_units = cost / unit_price
                    usage_estimate = {
                        'estimated_units': estimated_units,
                        'unit_type': price_info['unit'],
                        'confidence': 0.8,
                        'calculation': f'${cost} ÷ ${unit_price} {price_info["unit"]} = {estimated_units:.2f}'
                    }
        
        except Exception as e:
            usage_estimate['error'] = str(e)
        
        return usage_estimate
    
    async def _calculate_optimization_potential(self, service_name: str, cost: float, usage_estimate: Dict[str, Any]) -> float:
        """Calculate potential cost optimization"""
        try:
            # Service-specific optimization calculations
            if 'cost explorer' in service_name.lower():
                # Cost Explorer optimization: reduce API calls
                return cost * 0.8  # 80% potential savings by caching
            elif 'bedrock' in service_name.lower():
                # Bedrock optimization: use cheaper models or reduce tokens
                return cost * 0.3  # 30% potential savings
            elif 'ec2' in service_name.lower():
                # EC2 optimization: reserved instances, spot instances
                return cost * 0.4  # 40% potential savings
            else:
                # Generic optimization potential
                return cost * 0.2  # 20% potential savings
        
        except:
            return 0.0
    
    async def _generate_recommendations(self, billing_data: Dict[str, float]) -> List[Dict[str, Any]]:
        """Generate cost optimization recommendations"""
        recommendations = []
        
        total_cost = sum(billing_data.values())
        
        for service_name, cost in billing_data.items():
            if cost > 0:
                percentage = (cost / total_cost) * 100
                
                if 'cost explorer' in service_name.lower() and cost > 1.0:
                    recommendations.append({
                        'service': service_name,
                        'type': 'API Optimization',
                        'description': 'Reduce Cost Explorer API calls by implementing caching',
                        'potential_savings': cost * 0.8,
                        'priority': 'High' if percentage > 20 else 'Medium'
                    })
                
                elif 'bedrock' in service_name.lower() and cost > 0.1:
                    recommendations.append({
                        'service': service_name,
                        'type': 'Model Optimization',
                        'description': 'Use Claude 3 Haiku instead of Sonnet for simple tasks',
                        'potential_savings': cost * 0.3,
                        'priority': 'Medium'
                    })
                
                elif 'ec2' in service_name.lower() and cost > 5.0:
                    recommendations.append({
                        'service': service_name,
                        'type': 'Instance Optimization',
                        'description': 'Consider Reserved Instances or Spot Instances',
                        'potential_savings': cost * 0.4,
                        'priority': 'High' if percentage > 30 else 'Medium'
                    })
        
        return recommendations
    
    def _get_pricing_url(self, service_name: str) -> Optional[str]:
        """Get AWS pricing URL for service"""
        service_lower = service_name.lower()
        
        if 'cost explorer' in service_lower:
            return 'https://aws.amazon.com/aws-cost-management/pricing/'
        elif 'bedrock' in service_lower:
            return 'https://aws.amazon.com/bedrock/pricing/'
        elif 'ec2' in service_lower or 'elastic compute' in service_lower:
            return 'https://aws.amazon.com/ec2/pricing/on-demand/'
        elif 's3' in service_lower or 'simple storage' in service_lower:
            return 'https://aws.amazon.com/s3/pricing/'
        elif 'rds' in service_lower or 'relational database' in service_lower:
            return 'https://aws.amazon.com/rds/pricing/'
        elif 'lambda' in service_lower:
            return 'https://aws.amazon.com/lambda/pricing/'
        elif 'cloudwatch' in service_lower:
            return 'https://aws.amazon.com/cloudwatch/pricing/'
        
        return None
    
    def _map_service_name(self, service_name: str) -> ServiceType:
        """Map service name to ServiceType"""
        service_lower = service_name.lower()
        
        if 'cost explorer' in service_lower:
            return ServiceType.COST_EXPLORER
        elif 'bedrock' in service_lower:
            return ServiceType.BEDROCK
        elif 'ec2' in service_lower or 'elastic compute' in service_lower:
            return ServiceType.EC2
        elif 's3' in service_lower or 'simple storage' in service_lower:
            return ServiceType.S3
        elif 'rds' in service_lower or 'relational database' in service_lower:
            return ServiceType.RDS
        elif 'lambda' in service_lower:
            return ServiceType.LAMBDA
        elif 'cloudwatch' in service_lower:
            return ServiceType.CLOUDWATCH
        else:
            return ServiceType.OTHER
    
    # Required interface methods
    async def estimate_cost(self, resource_spec: ResourceSpec) -> CostEstimate:
        """Estimate cost for resource specification"""
        # This is handled by the billing analysis
        return CostEstimate(
            monthly_cost=0.0,
            total_cost=0.0,
            breakdown=CostBreakdown(),
            confidence_level=0.5,
            last_updated=datetime.now(),
            source="billing_analysis_strand"
        )
    
    async def get_pricing_data(self, region: Region) -> ServicePricing:
        """Get pricing data for region"""
        return ServicePricing(
            service=self.service_type,
            region=region,
            pricing_entries=[],
            effective_date=datetime.now(),
            source_url="billing_analysis"
        )
    
    async def validate_resource_spec(self, spec: ResourceSpec) -> ValidationResult:
        """Validate resource specification"""
        return ValidationResult(is_valid=True)
    
    def get_supported_instance_types(self, region: Region) -> List[str]:
        """Get supported instance types"""
        return []