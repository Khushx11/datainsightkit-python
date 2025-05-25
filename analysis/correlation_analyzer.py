"""
Correlation analysis module for DataInsightKit.

This module provides functionality to analyze relationships between variables
in a dataset using various correlation and association measures.
"""

from typing import Dict, List, Optional, Tuple, Union, Literal
import pandas as pd
import numpy as np
from scipy import stats
from dataclasses import dataclass

@dataclass
class CorrelationResult:
    """Data class to store correlation analysis results."""
    pair: Tuple[str, str]
    correlation: float
    p_value: Optional[float] = None
    method: str = "pearson"
    
    def to_dict(self) -> Dict:
        """Convert the result to a dictionary."""
        return {
            "pair": self.pair,
            "correlation": self.correlation,
            "p_value": self.p_value,
            "method": self.method,
            "type": "positive" if self.correlation > 0 else "negative"
        }

class CorrelationAnalyzer:
    """
    Analyzes correlations and associations between variables in a DataFrame.
    
    This class provides methods to compute various correlation measures:
    - Pearson's r for linear relationships between numeric variables
    - Spearman's rho for monotonic relationships between numeric variables
    - Cramér's V for associations between categorical variables
    - Theil's U for asymmetric associations between categorical variables
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize the CorrelationAnalyzer with a DataFrame.
        
        Args:
            df: Input pandas DataFrame
        """
        self.df = df
        self.numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        self.categorical_cols = df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()
        self.results = {
            'pearson': [],
            'spearman': [],
            'cramers_v': [],
            'theils_u': []
        }
    
    def analyze(
        self, 
        method: Literal['pearson', 'spearman', 'all'] = 'pearson',
        threshold: float = 0.7,
        p_value_threshold: float = 0.05
    ) -> Dict[str, List[Dict]]:
        """
        Analyze correlations between variables.
        
        Args:
            method: Correlation method to use ('pearson', 'spearman', or 'all')
            threshold: Absolute correlation threshold to consider (0 to 1)
            p_value_threshold: Maximum p-value to consider statistically significant
            
        Returns:
            Dictionary containing correlation results for each method
        """
        if method in ['pearson', 'all']:
            self._analyze_pearson(threshold, p_value_threshold)
        if method in ['spearman', 'all']:
            self._analyze_spearman(threshold, p_value_threshold)
        if method in ['all']:
            self._analyze_categorical()
            
        return self._get_significant_results(threshold)
    
    def _analyze_pearson(self, threshold: float = 0.7, p_value_threshold: float = 0.05) -> None:
        """Calculate Pearson correlation coefficients."""
        if len(self.numeric_cols) < 2:
            return
            
        corr_matrix = self.df[self.numeric_cols].corr(method='pearson')
        p_values = self._calculate_p_values(self.df[self.numeric_cols])
        
        self._process_correlation_matrix(
            corr_matrix, 
            p_values, 
            'pearson', 
            threshold, 
            p_value_threshold
        )
    
    def _analyze_spearman(self, threshold: float = 0.7, p_value_threshold: float = 0.05) -> None:
        """Calculate Spearman's rank correlation coefficients."""
        if len(self.numeric_cols) < 2:
            return
            
        corr_matrix = self.df[self.numeric_cols].corr(method='spearman')
        p_values = self._calculate_p_values(self.df[self.numeric_cols], method='spearman')
        
        self._process_correlation_matrix(
            corr_matrix, 
            p_values, 
            'spearman', 
            threshold, 
            p_value_threshold
        )
    
    def _analyze_categorical(self) -> None:
        """Calculate Cramér's V and Theil's U for categorical variables."""
        if len(self.categorical_cols) < 2:
            return
            
        # Calculate Cramér's V and Theil's U for all categorical variable pairs
        for i, col1 in enumerate(self.categorical_cols):
            for col2 in self.categorical_cols[i+1:]:
                # Calculate Cramér's V
                confusion_matrix = pd.crosstab(self.df[col1], self.df[col2])
                chi2 = stats.chi2_contingency(confusion_matrix)[0]
                n = confusion_matrix.sum().sum()
                phi2 = chi2 / n
                r, k = confusion_matrix.shape
                phi2corr = max(0, phi2 - ((k-1)*(r-1))/(n-1))
                rcorr = r - ((r-1)**2)/(n-1)
                kcorr = k - ((k-1)**2)/(n-1)
                cramers_v = np.sqrt(phi2corr / min((kcorr-1), (rcorr-1)))
                
                # Calculate Theil's U (uncertainty coefficient)
                def theils_u(x, y):
                    s_xy = stats.entropy(x, y)
                    s_x = stats.entropy(x)
                    return (s_x - s_xy) / s_x if s_x > 0 else 0
                
                u_col1_given_col2 = theils_u(self.df[col1].values, self.df[col2].values)
                u_col2_given_col1 = theils_u(self.df[col2].values, self.df[col1].values)
                
                # Store results
                self.results['cramers_v'].append(CorrelationResult(
                    pair=(col1, col2),
                    correlation=cramers_v,
                    method='cramers_v'
                ))
                
                self.results['theils_u'].append(CorrelationResult(
                    pair=(col1, col2),
                    correlation=u_col1_given_col2,
                    method='theils_u_col1_given_col2'
                ))
                
                self.results['theils_u'].append(CorrelationResult(
                    pair=(col2, col1),
                    correlation=u_col2_given_col1,
                    method='theils_u_col2_given_col1'
                ))
    
    def _process_correlation_matrix(
        self, 
        corr_matrix: pd.DataFrame, 
        p_values: pd.DataFrame,
        method: str,
        threshold: float,
        p_value_threshold: float
    ) -> None:
        """Process correlation matrix and store significant results."""
        for i, col1 in enumerate(corr_matrix.columns):
            for col2 in corr_matrix.columns[i+1:]:
                corr = corr_matrix.loc[col1, col2]
                p_val = p_values.loc[col1, col2] if p_values is not None else None
                
                if not np.isnan(corr) and abs(corr) >= threshold and \
                   (p_val is None or p_val <= p_value_threshold):
                    self.results[method].append(CorrelationResult(
                        pair=(col1, col2),
                        correlation=corr,
                        p_value=p_val,
                        method=method
                    ))
    
    def _calculate_p_values(
        self, 
        df: pd.DataFrame, 
        method: str = 'pearson'
    ) -> Optional[pd.DataFrame]:
        """Calculate p-values for correlation coefficients."""
        if method not in ['pearson', 'spearman']:
            return None
            
        df = df.dropna()
        n = len(df)
        
        if n < 3:  # Need at least 3 points for meaningful p-value
            return None
            
        if method == 'pearson':
            corr_matrix = df.corr(method='pearson')
            # Calculate t-statistics and p-values
            t_matrix = corr_matrix * np.sqrt((n - 2) / (1 - corr_matrix**2 + 1e-10))
            p_values = 2 * (1 - stats.t.cdf(np.abs(t_matrix), df=n-2))
        else:  # spearman
            # For spearman, we'll use scipy's spearmanr which returns p-values
            cols = df.columns
            p_values = pd.DataFrame(
                np.nan, 
                index=cols, 
                columns=cols,
                dtype=float
            )
            
            for i, col1 in enumerate(cols):
                for col2 in cols[i:]:
                    if col1 == col2:
                        p_values.loc[col1, col2] = 0.0
                    else:
                        _, p_val = stats.spearmanr(df[col1], df[col2], nan_policy='omit')
                        p_values.loc[col1, col2] = p_val
                        p_values.loc[col2, col1] = p_val
        
        return p_values
    
    def _get_significant_results(self, threshold: float) -> Dict[str, List[Dict]]:
        """Get significant correlation results above the threshold."""
        significant_results = {}
        
        for method, results in self.results.items():
            significant = []
            for result in results:
                if abs(result.correlation) >= threshold:
                    significant.append(result.to_dict())
            
            # Sort by absolute correlation in descending order
            significant.sort(key=lambda x: abs(x['correlation']), reverse=True)
            significant_results[method] = significant
        
        return significant_results
    
    def get_correlation_matrix(self, method: str = 'pearson') -> pd.DataFrame:
        """
        Get the correlation matrix for the specified method.
        
        Args:
            method: Correlation method ('pearson' or 'spearman')
            
        Returns:
            Correlation matrix as a pandas DataFrame
        """
        if method not in ['pearson', 'spearman']:
            raise ValueError("method must be 'pearson' or 'spearman'")
            
        if len(self.numeric_cols) < 2:
            return pd.DataFrame()
            
        return self.df[self.numeric_cols].corr(method=method)
