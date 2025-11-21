"""
SQLite-based caching implementation for AWS pricing data
"""

import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from ..core.pricing_interfaces import (
    IPricingCache, ServicePricing, CostEstimate, ServiceType, Region,
    PriceEntry, CostBreakdown, CacheError
)


class SQLitePricingCache(IPricingCache):
    """SQLite implementation of pricing data cache"""
    
    def __init__(self, db_path: str = "data/pricing_cache.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS pricing_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        service TEXT NOT NULL,
                        region TEXT NOT NULL,
                        pricing_data TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP NOT NULL,
                        source_url TEXT,
                        metadata TEXT,
                        UNIQUE(service, region)
                    );
                    
                    CREATE TABLE IF NOT EXISTS cost_estimates (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        resource_hash TEXT UNIQUE NOT NULL,
                        estimate_data TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP NOT NULL
                    );
                    
                    CREATE TABLE IF NOT EXISTS cache_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        operation TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        details TEXT
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_pricing_service_region 
                    ON pricing_cache(service, region);
                    
                    CREATE INDEX IF NOT EXISTS idx_pricing_expires 
                    ON pricing_cache(expires_at);
                    
                    CREATE INDEX IF NOT EXISTS idx_estimates_expires 
                    ON cost_estimates(expires_at);
                    
                    CREATE INDEX IF NOT EXISTS idx_estimates_hash 
                    ON cost_estimates(resource_hash);
                """)
        except sqlite3.Error as e:
            raise CacheError(f"Failed to initialize database: {e}")
    
    async def store_pricing(self, pricing: ServicePricing) -> bool:
        """Store pricing data in cache"""
        try:
            # Convert pricing data to JSON
            pricing_json = self._serialize_pricing(pricing)
            expires_at = datetime.now() + timedelta(hours=24)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO pricing_cache 
                    (service, region, pricing_data, expires_at, source_url, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    pricing.service.value,
                    pricing.region.value,
                    pricing_json,
                    expires_at.isoformat(),
                    pricing.source_url,
                    json.dumps(pricing.metadata)
                ))
                
                # Log cache operation
                conn.execute("""
                    INSERT INTO cache_stats (operation, details)
                    VALUES (?, ?)
                """, (
                    "store_pricing",
                    json.dumps({
                        "service": pricing.service.value,
                        "region": pricing.region.value,
                        "entries_count": len(pricing.pricing_entries)
                    })
                ))
            
            return True
            
        except (sqlite3.Error, json.JSONEncodeError) as e:
            raise CacheError(f"Failed to store pricing data: {e}")
    
    async def get_pricing(self, service: ServiceType, region: Region, max_age_hours: int = 24) -> Optional[ServicePricing]:
        """Retrieve pricing data from cache"""
        try:
            min_timestamp = datetime.now() - timedelta(hours=max_age_hours)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT pricing_data, source_url, metadata, created_at
                    FROM pricing_cache
                    WHERE service = ? AND region = ? AND expires_at > ?
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (service.value, region.value, min_timestamp.isoformat()))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                pricing_data, source_url, metadata_json, created_at = row
                
                # Deserialize pricing data
                pricing = self._deserialize_pricing(
                    pricing_data, service, region, source_url, metadata_json
                )
                
                # Log cache hit
                conn.execute("""
                    INSERT INTO cache_stats (operation, details)
                    VALUES (?, ?)
                """, (
                    "get_pricing_hit",
                    json.dumps({
                        "service": service.value,
                        "region": region.value,
                        "age_hours": (datetime.now() - datetime.fromisoformat(created_at)).total_seconds() / 3600
                    })
                ))
                
                return pricing
                
        except (sqlite3.Error, json.JSONDecodeError) as e:
            raise CacheError(f"Failed to retrieve pricing data: {e}")
    
    async def store_cost_estimate(self, resource_hash: str, estimate: CostEstimate) -> bool:
        """Store cost estimate in cache"""
        try:
            estimate_json = self._serialize_estimate(estimate)
            expires_at = datetime.now() + timedelta(hours=1)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO cost_estimates 
                    (resource_hash, estimate_data, expires_at)
                    VALUES (?, ?, ?)
                """, (resource_hash, estimate_json, expires_at.isoformat()))
                
                # Log cache operation
                conn.execute("""
                    INSERT INTO cache_stats (operation, details)
                    VALUES (?, ?)
                """, (
                    "store_estimate",
                    json.dumps({
                        "resource_hash": resource_hash[:16] + "...",
                        "total_cost": estimate.total_cost
                    })
                ))
            
            return True
            
        except (sqlite3.Error, json.JSONEncodeError) as e:
            raise CacheError(f"Failed to store cost estimate: {e}")
    
    async def get_cost_estimate(self, resource_hash: str, max_age_hours: int = 1) -> Optional[CostEstimate]:
        """Retrieve cost estimate from cache"""
        try:
            min_timestamp = datetime.now() - timedelta(hours=max_age_hours)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT estimate_data, created_at
                    FROM cost_estimates
                    WHERE resource_hash = ? AND expires_at > ?
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (resource_hash, min_timestamp.isoformat()))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                estimate_data, created_at = row
                estimate = self._deserialize_estimate(estimate_data)
                
                # Log cache hit
                conn.execute("""
                    INSERT INTO cache_stats (operation, details)
                    VALUES (?, ?)
                """, (
                    "get_estimate_hit",
                    json.dumps({
                        "resource_hash": resource_hash[:16] + "...",
                        "age_hours": (datetime.now() - datetime.fromisoformat(created_at)).total_seconds() / 3600
                    })
                ))
                
                return estimate
                
        except (sqlite3.Error, json.JSONDecodeError) as e:
            raise CacheError(f"Failed to retrieve cost estimate: {e}")
    
    async def cleanup_expired(self) -> int:
        """Remove expired cache entries"""
        try:
            now = datetime.now().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                # Clean up expired pricing data
                cursor = conn.execute("""
                    DELETE FROM pricing_cache WHERE expires_at <= ?
                """, (now,))
                pricing_deleted = cursor.rowcount
                
                # Clean up expired cost estimates
                cursor = conn.execute("""
                    DELETE FROM cost_estimates WHERE expires_at <= ?
                """, (now,))
                estimates_deleted = cursor.rowcount
                
                total_deleted = pricing_deleted + estimates_deleted
                
                # Log cleanup operation
                conn.execute("""
                    INSERT INTO cache_stats (operation, details)
                    VALUES (?, ?)
                """, (
                    "cleanup_expired",
                    json.dumps({
                        "pricing_deleted": pricing_deleted,
                        "estimates_deleted": estimates_deleted,
                        "total_deleted": total_deleted
                    })
                ))
                
                return total_deleted
                
        except sqlite3.Error as e:
            raise CacheError(f"Failed to cleanup expired entries: {e}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics and health information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get pricing cache stats
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_entries,
                        COUNT(CASE WHEN expires_at > datetime('now') THEN 1 END) as active_entries,
                        MIN(created_at) as oldest_entry,
                        MAX(created_at) as newest_entry
                    FROM pricing_cache
                """)
                pricing_stats = dict(zip([col[0] for col in cursor.description], cursor.fetchone()))
                
                # Get cost estimate stats
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_estimates,
                        COUNT(CASE WHEN expires_at > datetime('now') THEN 1 END) as active_estimates,
                        MIN(created_at) as oldest_estimate,
                        MAX(created_at) as newest_estimate
                    FROM cost_estimates
                """)
                estimate_stats = dict(zip([col[0] for col in cursor.description], cursor.fetchone()))
                
                # Get recent operation stats
                cursor = conn.execute("""
                    SELECT operation, COUNT(*) as count
                    FROM cache_stats
                    WHERE timestamp > datetime('now', '-24 hours')
                    GROUP BY operation
                """)
                operation_stats = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Calculate cache hit rates
                hits = operation_stats.get('get_pricing_hit', 0) + operation_stats.get('get_estimate_hit', 0)
                total_gets = hits + operation_stats.get('get_pricing_miss', 0) + operation_stats.get('get_estimate_miss', 0)
                hit_rate = (hits / total_gets * 100) if total_gets > 0 else 0
                
                return {
                    "pricing_cache": pricing_stats,
                    "estimate_cache": estimate_stats,
                    "operations_24h": operation_stats,
                    "hit_rate_percent": round(hit_rate, 2),
                    "database_size_mb": round(self.db_path.stat().st_size / (1024 * 1024), 2)
                }
                
        except sqlite3.Error as e:
            raise CacheError(f"Failed to get cache stats: {e}")
    
    def _serialize_pricing(self, pricing: ServicePricing) -> str:
        """Serialize ServicePricing to JSON"""
        data = {
            "service": pricing.service.value,
            "region": pricing.region.value,
            "effective_date": pricing.effective_date.isoformat(),
            "source_url": pricing.source_url,
            "metadata": pricing.metadata,
            "pricing_entries": [
                {
                    "service": entry.service.value,
                    "region": entry.region.value,
                    "resource_type": entry.resource_type,
                    "price_per_unit": entry.price_per_unit,
                    "unit": entry.unit,
                    "currency": entry.currency,
                    "effective_date": entry.effective_date.isoformat()
                }
                for entry in pricing.pricing_entries
            ]
        }
        return json.dumps(data)
    
    def _deserialize_pricing(self, pricing_json: str, service: ServiceType, region: Region, 
                           source_url: str, metadata_json: str) -> ServicePricing:
        """Deserialize JSON to ServicePricing"""
        data = json.loads(pricing_json)
        
        pricing_entries = [
            PriceEntry(
                service=ServiceType(entry["service"]),
                region=Region(entry["region"]),
                resource_type=entry["resource_type"],
                price_per_unit=entry["price_per_unit"],
                unit=entry["unit"],
                currency=entry["currency"],
                effective_date=datetime.fromisoformat(entry["effective_date"])
            )
            for entry in data["pricing_entries"]
        ]
        
        return ServicePricing(
            service=service,
            region=region,
            pricing_entries=pricing_entries,
            effective_date=datetime.fromisoformat(data["effective_date"]),
            source_url=source_url,
            metadata=json.loads(metadata_json) if metadata_json else {}
        )
    
    def _serialize_estimate(self, estimate: CostEstimate) -> str:
        """Serialize CostEstimate to JSON"""
        data = {
            "monthly_cost": estimate.monthly_cost,
            "total_cost": estimate.total_cost,
            "breakdown": {
                "compute_cost": estimate.breakdown.compute_cost,
                "storage_cost": estimate.breakdown.storage_cost,
                "network_cost": estimate.breakdown.network_cost,
                "additional_costs": estimate.breakdown.additional_costs
            },
            "confidence_level": estimate.confidence_level,
            "last_updated": estimate.last_updated.isoformat(),
            "source": estimate.source,
            "notes": estimate.notes
        }
        return json.dumps(data)
    
    def _deserialize_estimate(self, estimate_json: str) -> CostEstimate:
        """Deserialize JSON to CostEstimate"""
        data = json.loads(estimate_json)
        
        breakdown = CostBreakdown(
            compute_cost=data["breakdown"]["compute_cost"],
            storage_cost=data["breakdown"]["storage_cost"],
            network_cost=data["breakdown"]["network_cost"],
            additional_costs=data["breakdown"]["additional_costs"]
        )
        
        return CostEstimate(
            monthly_cost=data["monthly_cost"],
            total_cost=data["total_cost"],
            breakdown=breakdown,
            confidence_level=data["confidence_level"],
            last_updated=datetime.fromisoformat(data["last_updated"]),
            source=data["source"],
            notes=data["notes"]
        )
    
    @staticmethod
    def generate_resource_hash(resource_spec) -> str:
        """Generate hash for resource specification caching"""
        # Create a consistent string representation of the resource spec
        spec_str = f"{resource_spec.service_type.value}:{resource_spec.instance_type}:{resource_spec.quantity}:{resource_spec.duration_months}:{resource_spec.region.value}:{json.dumps(resource_spec.additional_specs, sort_keys=True)}"
        return hashlib.sha256(spec_str.encode()).hexdigest()