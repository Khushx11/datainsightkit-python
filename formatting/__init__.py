"""Formatting module for DataInsightKit.

This module provides utilities for formatting data and analysis results
in a human-readable way.
"""

from .formatter import (
    Formatter,
    MarkdownFormatter,
    HTMLFormatter,
    TextFormatter,
    JSONFormatter
)

__all__ = [
    'Formatter',
    'MarkdownFormatter',
    'HTMLFormatter',
    'TextFormatter',
    'JSONFormatter',
]