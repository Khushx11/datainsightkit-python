"""
Anomaly detection module for identifying outliers in tabular data.

This module provides functionality to detect anomalies in numeric columns using
various statistical methods.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Literal
from dataclasses import dataclass, field


@dataclass
class AnomalyResult:
    """Dataclass to store anomaly detection results for a single column."""
    column: str
    method: str
    threshold: float
    count: int = 0
    percent: float = 0.0
    indices: List[int] = field(default_factory=list)
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    
    def to_dict(self) -> Dict:
        """Convert the result to a dictionary."""
        return {
            'column': self.column,
            'method': self.method,
            'threshold': self.threshold,
            'count': self.count,
            'percent': self.percent,
            'indices': self.indices[:100],  # Limit to first 100 indices
            'lower_bound': self.lower_bound,
            'upper_bound': self.upper_bound
        }


class AnomalyDetector:
    """
    A class for detecting anomalies in numeric columns of a pandas DataFrame.
    
    This class provides methods to detect anomalies using various statistical
    methods such as IQR (Interquartile Range) and Z-Score.
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize the AnomalyDetector with a pandas DataFrame.
        
        Args:
            df: The input DataFrame to analyze for anomalies
        """
        self.df = df.copy()
        self.results: Dict[str, AnomalyResult] = {}
    
    def detect(
        self, 
        method: Literal['iqr', 'zscore'] = 'iqr', 
        threshold: float = 1.5,
        columns: Optional[List[str]] = None
    ) -> Dict[str, AnomalyResult]:
        """
        Detect anomalies in numeric columns of the DataFrame.
        
        Args:
            method: The method to use for anomaly detection. 
                   Options: 'iqr' (default) or 'zscore'
            threshold: The threshold for anomaly detection.
                     For IQR: multiplier for the IQR (default: 1.5)
                     For Z-Score: number of standard deviations (default: 3.0)
            columns: List of column names to analyze. If None, all numeric columns are used.
            
        Returns:
            Dictionary mapping column names to AnomalyResult objects
        """
        # Set default threshold based on method if not specified
        if method == 'zscore' and threshold == 1.5:
            threshold = 3.0  # More common default for z-score
            
        # Get numeric columns if not specified
        if columns is None:
            columns = self.df.select_dtypes(include=np.number).columns.tolist()
        
        self.results = {}
        
        for col in columns:
            if col not in self.df.columns or not np.issubdtype(self.df[col].dtype, np.number):
                continue
                
            series = self.df[col].dropna()
            
            if method == 'iqr':
                result = self._detect_iqr(series, col, threshold)
            elif method == 'zscore':
                result = self._detect_zscore(series, col, threshold)
            else:
                raise ValueError(f"Unsupported method: {method}. Use 'iqr' or 'zscore'")
            
            self.results[col] = result
        
        return self.results
    
    def _detect_iqr(self, series: pd.Series, col: str, threshold: float) -> AnomalyResult:
        """Detect anomalies using the Interquartile Range (IQR) method."""
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        
        lower_bound = q1 - threshold * iqr
        upper_bound = q3 + threshold * iqr
        
        mask = (series < lower_bound) | (series > upper_bound)
        indices = series[mask].index.tolist()
        
        return AnomalyResult(
            column=col,
            method='iqr',
            threshold=threshold,
            count=len(indices),
            percent=100 * len(indices) / len(series) if len(series) > 0 else 0,
            indices=indices,
            lower_bound=float(lower_bound) if not np.isnan(lower_bound) else None,
            upper_bound=float(upper_bound) if not np.isnan(upper_bound) else None
        )
    
    def _detect_zscore(self, series: pd.Series, col: str, threshold: float) -> AnomalyResult:
        """Detect anomalies using the Z-Score method."""
        zscores = (series - series.mean()) / series.std()
        mask = np.abs(zscores) > threshold
        indices = series[mask].index.tolist()
        
        return AnomalyResult(
            column=col,
            method='zscore',
            threshold=threshold,
            count=len(indices),
            percent=100 * len(indices) / len(series) if len(series) > 0 else 0,
            indices=indices,
            lower_bound=float(series.mean() - threshold * series.std()) if len(series) > 0 else None,
            upper_bound=float(series.mean() + threshold * series.std()) if len(series) > 0 else None
        )
    
    def get_summary(self) -> Dict[str, Dict]:
        """
        Get a summary of the anomaly detection results.
        
        Returns:
            Dictionary with summary statistics for each column
        """
        summary = {}
        for col, result in self.results.items():
            summary[col] = {
                'method': result.method,
                'threshold': result.threshold,
                'anomaly_count': result.count,
                'anomaly_percent': result.percent,
                'sample_indices': result.indices[:5],  # Return first 5 indices as sample
                'bounds': {
                    'lower': result.lower_bound,
                    'upper': result.upper_bound
                }
            }
        return summary
    
    def get_anomalous_rows(self, column: Optional[str] = None) -> pd.DataFrame:
        """
        Get a DataFrame containing only the rows with anomalies.
        
        Args:
            column: If specified, only return anomalies for this column.
                   If None, return anomalies for all columns.
                   
        Returns:
            DataFrame containing only the anomalous rows
        """
        if not self.results:
            return pd.DataFrame()
            
        if column:
            if column not in self.results:
                return pd.DataFrame()
            indices = self.results[column].indices
            return self.df.loc[indices].copy()
        else:
            # Get all unique indices with anomalies
            all_indices = set()
            for result in self.results.values():
                all_indices.update(result.indices)
            return self.df.loc[list(all_indices)].copy()
