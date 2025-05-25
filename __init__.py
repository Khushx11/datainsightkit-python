"""
DataInsightKit - A Python library for generating natural language insights from tabular data.

This library provides tools for analyzing, describing, and exporting insights from structured data
in various formats including text, markdown, HTML, and JSON.
"""

__version__ = "0.1.0"

from .main import DataInsightKit
from .analysis import (
    CorrelationAnalyzer, 
    CorrelationResult,
    TextAnalyzer,
    TextAnalysisResult
)

__all__ = [
    "DataInsightKit",
    "CorrelationAnalyzer",
    "CorrelationResult",
    "TextAnalyzer",
    "TextAnalysisResult",
    "__version__"
]
