"""
Analysis module for DataInsightKit.

This module provides various analysis tools for tabular data, including anomaly detection,
correlation analysis, and text analysis.
"""

from .anomaly_detector import AnomalyDetector, AnomalyResult
from .correlation_analyzer import CorrelationAnalyzer, CorrelationResult
from .text_analyzer import TextAnalyzer, TextAnalysisResult

__all__ = [
    'AnomalyDetector', 
    'AnomalyResult',
    'CorrelationAnalyzer',
    'CorrelationResult',
    'TextAnalyzer',
    'TextAnalysisResult'
]