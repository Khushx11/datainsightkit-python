"""
Text analysis module for DataInsightKit.

This module provides functionality for analyzing text data in DataFrames,
including sentiment analysis, keyword extraction, and text statistics.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from textblob import TextBlob
import re
from dataclasses import dataclass

@dataclass
class TextAnalysisResult:
    """Container for text analysis results."""
    count: int
    avg_length: float
    min_length: int
    max_length: int
    sentiment: float
    subjectivity: float
    keywords: List[str]
    readability: Optional[float] = None
    word_count: Optional[Dict[str, int]] = None

class TextAnalyzer:
    """
    Analyzes text columns in a DataFrame to extract insights like sentiment,
    keywords, and text statistics.
    
    Args:
        df: Input DataFrame containing text data to analyze
    """
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        # Consider both 'object' and 'string' dtypes for text columns
        self.text_cols = df.select_dtypes(include=['object', 'string']).columns
    
    def _calculate_readability(self, text: str) -> float:
        """Calculate Flesch Reading Ease score for a given text."""
        try:
            sentences = len(re.split(r'[.!?]+', text))
            words = len(text.split())
            syllables = sum([len(re.findall(r'[aeiouyAEIOUY]+', word)) for word in text.split()])
            
            if words == 0 or sentences == 0:
                return 0.0
                
            # Flesch Reading Ease formula
            return 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
        except:
            return 0.0
    
    def analyze(self, top_k_keywords: int = 5, min_text_length: int = 5) -> Dict[str, Dict[str, Any]]:
        """
        Analyze text columns in the DataFrame.
        
        Args:
            top_k_keywords: Number of top keywords to extract per column
            min_text_length: Minimum average text length to consider a column for analysis
            
        Returns:
            Dictionary containing analysis results for each text column
        """
        results = {}

        for col in self.text_cols:
            # Skip columns with mostly empty or very short text
            texts = self.df[col].dropna().astype(str)
            if texts.empty or texts.str.strip().eq('').all():
                continue
                
            # Calculate text statistics
            lengths = texts.str.len()
            
            # Skip if average text length is below threshold
            if lengths.mean() < min_text_length:
                continue
                
            # Analyze sentiment and subjectivity
            blob_stats = texts.apply(TextBlob)
            sentiment_scores = blob_stats.apply(lambda x: x.sentiment)
            avg_sentiment = sentiment_scores.apply(lambda x: x.polarity).mean()
            avg_subjectivity = sentiment_scores.apply(lambda x: x.subjectivity).mean()
            
            # Calculate readability scores
            readability_scores = texts.apply(self._calculate_readability)
            avg_readability = readability_scores.mean()
            
            # Extract keywords using TF-IDF
            try:
                tfidf = TfidfVectorizer(
                    stop_words='english',
                    max_features=top_k_keywords,
                    ngram_range=(1, 2),  # Include bigrams
                    min_df=2  # Minimum document frequency
                )
                tfidf_matrix = tfidf.fit_transform(texts)
                keywords = tfidf.get_feature_names_out()
            except Exception as e:
                print(f"Error extracting keywords for column '{col}': {str(e)}")
                keywords = []
            
            # Count word frequencies
            word_counts = {}
            if not texts.empty:
                word_counts = pd.Series(' '.join(texts).lower().split()).value_counts().to_dict()
            
            # Store results
            results[col] = TextAnalysisResult(
                count=len(texts),
                avg_length=float(lengths.mean()),
                min_length=int(lengths.min()),
                max_length=int(lengths.max()),
                sentiment=round(avg_sentiment, 3),
                subjectivity=round(avg_subjectivity, 3),
                keywords=list(keywords),
                readability=round(avg_readability, 1) if not pd.isna(avg_readability) else None,
                word_count=word_counts
            )

        return results
    
    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """Convert analysis results to a dictionary."""
        results = self.analyze()
        return {
            col: {
                'count': result.count,
                'avg_length': result.avg_length,
                'min_length': result.min_length,
                'max_length': result.max_length,
                'sentiment': result.sentiment,
                'subjectivity': result.subjectivity,
                'readability': result.readability,
                'keywords': result.keywords,
                'word_count': result.word_count
            }
            for col, result in results.items()
        }
