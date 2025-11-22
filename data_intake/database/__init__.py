"""
Data Intake Database Module

Provides storage layer for the three-tier data architecture:
- L1: raw_events
- L2: normalized_events
- L3: feature_store
"""

from data_intake.database.storage import (
    DataIntakeStorage,
    get_storage,
)

__all__ = [
    "DataIntakeStorage",
    "get_storage",
]
