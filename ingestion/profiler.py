"""
Data profiling module for DataInsightKit.

This module provides functionality to profile and analyze pandas DataFrames,
extracting statistical insights and metadata about the data.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union, TypeVar
import pandas as pd
import numpy as np

# Type variable for generic numeric types
Numeric = TypeVar('Numeric', int, float, np.number)

@dataclass
class ColumnProfile:
    """
    Holds profiling information for a single column in a DataFrame.
    
    Attributes:
        name: The name of the column
        dtype: The data type of the column
        role: The inferred role of the column ('numeric', 'categorical', 'datetime', 'text', 'unknown')
        stats: Dictionary of statistical measures for the column
        top_values: List of most common values and their counts
        missing_percent: Percentage of missing values
        unique_percent: Percentage of unique values
        cardinality: Number of unique values
    """
    name: str
    dtype: str
    role: str = "unknown"
    stats: Dict[str, Any] = field(default_factory=dict)
    top_values: Dict[Any, int] = field(default_factory=dict)
    missing_percent: float = 0.0
    unique_percent: float = 0.0
    cardinality: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the profile to a dictionary."""
        return {
            "name": self.name,
            "dtype": self.dtype,
            "role": self.role,
            "stats": self.stats,
            "top_values": self.top_values,
            "missing_percent": self.missing_percent,
            "unique_percent": self.unique_percent,
            "cardinality": self.cardinality
        }


class DataProfiler:
    """
    Profiles a pandas DataFrame to extract statistical insights and metadata.
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize the DataProfiler with a pandas DataFrame.
        
        Args:
            df: The input DataFrame to profile
        """
        self.df = df.copy()
        self.profiles: Dict[str, ColumnProfile] = {}
    
    def _detect_column_role(self, series: pd.Series, unique_ratio: float) -> str:
        """
        Detect the role of a column based on its data type and unique value ratio.
        
        Args:
            series: The column to analyze
            unique_ratio: Ratio of unique values to total values
            
        Returns:
            str: The inferred role of the column
        """
        if pd.api.types.is_numeric_dtype(series):
            # Check if the numeric column is actually categorical (low cardinality)
            if unique_ratio < 0.05:  # Arbitrary threshold
                return 'categorical'
            return 'numeric'
        elif pd.api.types.is_datetime64_any_dtype(series):
            return 'datetime'
        elif pd.api.types.is_bool_dtype(series):
            return 'boolean'
        elif pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series):
            # Check if string column is categorical or text
            if unique_ratio < 0.5:  # Arbitrary threshold
                return 'categorical'
            return 'text'
        return 'unknown'
    
    def _profile_numeric_column(self, series: pd.Series) -> Dict[str, Any]:
        """
        Generate statistics for a numeric column.
        
        Args:
            series: The numeric column to profile
            
        Returns:
            Dict containing numeric statistics
        """
        stats = {
            'mean': series.mean(),
            'std': series.std(),
            'min': series.min(),
            'max': series.max(),
            'median': series.median(),
            'kurtosis': series.kurtosis(),
            'skew': series.skew(),
            'zeros': int((series == 0).sum()),
            'iqr': series.quantile(0.75) - series.quantile(0.25),
            'q1': series.quantile(0.25),
            'q3': series.quantile(0.75),
            'range': series.max() - series.min(),
            'count': series.count(),
            'missing': series.isna().sum()
        }
        
        # Calculate percentage of values within 1, 2, 3 standard deviations
        if not np.isnan(stats['mean']) and not np.isnan(stats['std']) and stats['std'] > 0:
            z_scores = (series - stats['mean']) / stats['std']
            for i in [1, 2, 3]:
                stats[f'within_{i}_std'] = ((z_scores.abs() <= i).sum() / len(series)) * 100
        
        return {k: float(v) if isinstance(v, (np.floating, np.integer)) else v 
               for k, v in stats.items()}
    
    def _profile_categorical_column(self, series: pd.Series) -> Dict[str, Any]:
        """
        Generate statistics for a categorical column.
        
        Args:
            series: The categorical column to profile
            
        Returns:
            Dict containing categorical statistics
        """
        value_counts = series.value_counts()
        value_counts_norm = series.value_counts(normalize=True)
        
        return {
            'top': value_counts.index[0] if not value_counts.empty else None,
            'freq': value_counts.iloc[0] if not value_counts.empty else 0,
            'freq_percent': value_counts_norm.iloc[0] * 100 if not value_counts_norm.empty else 0,
            'n_unique': series.nunique(),
            'most_common': value_counts.head(10).to_dict(),
            'least_common': value_counts.tail(10).to_dict() if len(value_counts) > 10 else {}
        }
    
    def _profile_datetime_column(self, series: pd.Series) -> Dict[str, Any]:
        """
        Generate statistics for a datetime column.
        
        Args:
            series: The datetime column to profile
            
        Returns:
            Dict containing datetime statistics
        """
        stats = {
            'min': series.min(),
            'max': series.max(),
            'range': series.max() - series.min(),
            'missing': series.isna().sum(),
            'count': series.count()
        }
        
        # Convert to string for JSON serialization
        for k in ['min', 'max']:
            if pd.notnull(stats[k]):
                stats[k] = str(stats[k])
        
        if pd.notnull(stats['range']):
            stats['range'] = str(stats['range'])
        
        return stats
    
    def _profile_text_column(self, series: pd.Series) -> Dict[str, Any]:
        """
        Generate statistics for a text column.
        
        Args:
            series: The text column to profile
            
        Returns:
            Dict containing text statistics
        """
        text_lengths = series.dropna().astype(str).apply(len)
        word_counts = series.dropna().astype(str).apply(lambda x: len(x.split()))
        
        stats = {
            'avg_length': float(text_lengths.mean()) if not text_lengths.empty else 0,
            'max_length': int(text_lengths.max()) if not text_lengths.empty else 0,
            'min_length': int(text_lengths.min()) if not text_lengths.empty else 0,
            'avg_words': float(word_counts.mean()) if not word_counts.empty else 0,
            'max_words': int(word_counts.max()) if not word_counts.empty else 0,
            'min_words': int(word_counts.min()) if not word_counts.empty else 0,
            'missing': series.isna().sum(),
            'count': series.count()
        }
        
        # Add character frequency analysis
        if not series.empty:
            all_text = ' '.join(series.dropna().astype(str))
            stats['char_freq'] = {}
            for c in set(all_text):
                if c.strip():  # Skip whitespace
                    stats['char_freq'][c] = all_text.count(c)
        
        return stats
    
    def profile(self) -> Dict[str, ColumnProfile]:
        """
        Profile all columns in the DataFrame.
        
        Returns:
            Dictionary mapping column names to their ColumnProfile objects
        """
        for col in self.df.columns:
            series = self.df[col]
            dtype = str(series.dtype)
            
            # Skip empty columns
            if series.empty:
                self.profiles[col] = ColumnProfile(
                    name=col,
                    dtype=dtype,
                    role='empty'
                )
                continue
            
            # Calculate basic metrics
            n_missing = series.isna().sum()
            n_unique = series.nunique()
            missing_percent = (n_missing / len(series)) * 100
            unique_percent = (n_unique / len(series)) * 100
            
            # Create profile
            profile = ColumnProfile(
                name=col,
                dtype=dtype,
                missing_percent=float(missing_percent),
                unique_percent=float(unique_percent),
                cardinality=int(n_unique)
            )
            
            # Detect column role
            profile.role = self._detect_column_role(series, unique_percent / 100)
            
            # Skip profiling if all values are missing
            if n_missing == len(series):
                self.profiles[col] = profile
                continue
            
            # Profile based on detected role
            try:
                if profile.role == 'numeric':
                    profile.stats = self._profile_numeric_column(series)
                    # Add top values for numeric columns with low cardinality
                    if profile.unique_percent < 20:  # Arbitrary threshold
                        profile.top_values = series.value_counts().head(10).to_dict()
                
                elif profile.role == 'categorical':
                    cat_stats = self._profile_categorical_column(series)
                    profile.stats = cat_stats
                    profile.top_values = cat_stats.get('most_common', {})
                
                elif profile.role == 'datetime':
                    profile.stats = self._profile_datetime_column(series)
                
                elif profile.role == 'text':
                    profile.stats = self._profile_text_column(series)
                
                elif profile.role == 'boolean':
                    profile.stats = {
                        'true_count': int(series.sum()),
                        'false_count': int((~series).sum()),
                        'true_percent': (series.mean() * 100) if len(series) > 0 else 0,
                        'false_percent': ((~series).mean() * 100) if len(series) > 0 else 0,
                        'missing': int(series.isna().sum())
                    }
                    profile.top_values = series.value_counts().head(10).to_dict()
                
            except Exception as e:
                # If profiling fails for any reason, store the error and continue
                profile.role = 'error'
                profile.stats = {'error': str(e)}
            
            self.profiles[col] = profile
        
        return self.profiles
    
    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """
        Convert all profiles to a dictionary.
        
        Returns:
            Dictionary of column names to their profile dictionaries
        """
        return {name: profile.to_dict() for name, profile in self.profiles.items()}
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get a summary of the profiling results.
        
        Returns:
            Dictionary with overall statistics about the dataset
        """
        return {
            'n_variables': len(self.df.columns),
            'n_observations': len(self.df),
            'missing_cells': int(self.df.isna().sum().sum()),
            'missing_cells_percent': float((self.df.isna().sum().sum() / (len(self.df) * len(self.df.columns))) * 100) if len(self.df) > 0 else 0,
            'duplicate_rows': int(self.df.duplicated().sum()),
            'duplicate_rows_percent': float((self.df.duplicated().sum() / len(self.df)) * 100) if len(self.df) > 0 else 0,
            'variable_types': {
                'numeric': sum(1 for p in self.profiles.values() if p.role == 'numeric'),
                'categorical': sum(1 for p in self.profiles.values() if p.role == 'categorical'),
                'text': sum(1 for p in self.profiles.values() if p.role == 'text'),
                'datetime': sum(1 for p in self.profiles.values() if p.role == 'datetime'),
                'boolean': sum(1 for p in self.profiles.values() if p.role == 'boolean'),
                'unknown': sum(1 for p in self.profiles.values() if p.role == 'unknown'),
                'empty': sum(1 for p in self.profiles.values() if p.role == 'empty'),
                'error': sum(1 for p in self.profiles.values() if p.role == 'error')
            }
        }
