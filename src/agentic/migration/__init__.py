"""
Agentic AI System Migration Module

This module provides comprehensive migration capabilities for transitioning
from a legacy system to the agentic AI architecture.

Components:
- DataMigrationManager: Handles data transformation and migration
- CompatibilityLayer: Maintains backward compatibility during transition
- FeatureFlagManager: Manages gradual feature rollout
- MigrationOrchestrator: Coordinates the complete migration process
"""

from .data_migration import DataMigrationManager, MigrationResult
from .compatibility_layer import (
    CompatibilityLayer, 
    CompatibilityMode, 
    BackwardCompatibilityManager,
    EndpointMapping
)
from .feature_flags import (
    FeatureFlagManager, 
    FeatureFlag, 
    FeatureEvaluation,
    RolloutStrategy
)
from .migration_orchestrator import MigrationOrchestrator, MigrationPhase
from .enable_all_features import enable_all_agentic_features

__all__ = [
    # Data Migration
    "DataMigrationManager",
    "MigrationResult",
    
    # Compatibility Layer
    "CompatibilityLayer",
    "CompatibilityMode", 
    "BackwardCompatibilityManager",
    "EndpointMapping",
    
    # Feature Flags
    "FeatureFlagManager",
    "FeatureFlag",
    "FeatureEvaluation", 
    "RolloutStrategy",
    
    # Migration Orchestration
    "MigrationOrchestrator",
    "MigrationPhase",
    
    # Utilities
    "enable_all_agentic_features"
]