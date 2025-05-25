"""Data ingestion module for DataInsightKit.

This module provides functionality for loading and preprocessing data
from various sources and formats.
"""

from .loader import DataLoader, DataFormat, DataSource
from .profiler import DataProfiler, ProfileResult

__all__ = [
    'DataLoader',
    'DataFormat',
    'DataSource',
    'DataProfiler',
    'ProfileResult',
]