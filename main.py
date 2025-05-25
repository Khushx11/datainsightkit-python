"""
Main module for DataInsightKit.

This module provides the main DataInsightKit class which serves as the primary
interface for analyzing and describing tabular data.
"""

import json
import pandas as pd
from typing import Dict, Any, Optional, Union, List, Tuple
from pathlib import Path
from datetime import datetime

from datainsightkit.ingestion.profiler import DataProfiler
from datainsightkit.analysis.anomaly_detector import AnomalyDetector
from datainsightkit.analysis.correlation_analyzer import CorrelationAnalyzer, CorrelationResult
from datainsightkit.analysis.text_analyzer import TextAnalyzer, TextAnalysisResult
from datainsightkit.nlg.narrative_generator import NarrativeGenerator

class DataInsightKit:
    """
    Main class for generating insights from tabular data.
    
    This class provides methods to analyze, describe, and export insights
    from pandas DataFrames in various formats.
    """
    
    def __init__(self, dataframe: pd.DataFrame, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the DataInsightKit with a pandas DataFrame.
        
        Args:
            dataframe: The input data as a pandas DataFrame
            config: Optional configuration dictionary for customizing behavior
        """
        self.df = dataframe.copy()
        # Default configuration
        default_config = {
            # General display settings
            'max_categories': 10,  # Max number of categories to show in reports
            'max_decimals': 2,     # Number of decimal places to round numbers
            'top_n': 5,            # Number of top values to show by default
            
            # Text analysis settings
            'top_k_keywords': 5,   # Number of top keywords to extract
            'min_text_length': 5,  # Minimum text length to analyze (in characters)
            'anomaly_method': 'iqr',  # Default anomaly detection method
            'anomaly_threshold': 1.5,  # Threshold for anomaly detection
            'correlation_method': 'pearson',  # Default correlation method
            'correlation_threshold': 0.7,  # Threshold for strong correlation
            'p_value_threshold': 0.05  # Threshold for statistical significance
        }
        
        # Merge with user config, with user values taking precedence
        user_config = {} if config is None else config
        self.config = {**default_config, **user_config}
        self.insights: Dict[str, Any] = {}
        self.profiler: Optional[DataProfiler] = None

    def analyze(self) -> Dict[str, Any]:
        """
        Analyze the input data and generate insights.
        
        Returns:
            Dictionary containing the analysis results
        """
        # Initialize profiler and run analysis
        self.profiler = DataProfiler(self.df)
        profiles = self.profiler.profile()
        
        # Run anomaly detection on numeric columns
        detector = AnomalyDetector(self.df)
        anomalies = detector.detect(
            method=self.config.get('anomaly_method', 'iqr'),
            threshold=self.config.get('anomaly_threshold', 1.5)
        )
        
        # Run correlation analysis
        correlation_analyzer = CorrelationAnalyzer(self.df)
        correlations = correlation_analyzer.analyze(
            method=self.config.get('correlation_method', 'pearson'),
            threshold=self.config.get('correlation_threshold', 0.7),
            p_value_threshold=self.config.get('p_value_threshold', 0.05)
        )
        
        # Run text analysis on text columns
        text_analyzer = TextAnalyzer(self.df)
        text_analysis = text_analyzer.analyze(
            top_k_keywords=self.config.get('top_k_keywords', 5),
            min_text_length=self.config.get('min_text_length', 5)
        )
        
        # Store raw profiles and summary statistics
        self.insights = {
            'profiles': {name: profile.to_dict() for name, profile in profiles.items()},
            'summary': self.profiler.get_summary_stats(),
            'generated_at': datetime.utcnow().isoformat(),
            'dataset_shape': {
                'rows': len(self.df),
                'columns': len(self.df.columns),
                'missing_cells': int(self.df.isna().sum().sum()),
                'missing_percent': (self.df.isna().sum().sum() / (len(self.df) * len(self.df.columns))) * 100,
                'duplicates': int(self.df.duplicated().sum()),
                'duplicates_percent': (self.df.duplicated().sum() / len(self.df)) * 100 if len(self.df) > 0 else 0
            },
            'variable_types': self.profiler.get_summary_stats()['variable_types'],
            'anomalies': {col: result.to_dict() for col, result in anomalies.items()},
            'correlations': correlations,
            'text_analysis': text_analysis
        }
        
        return self.insights

    def _format_number(self, value: Any, decimals: Optional[int] = None) -> str:
        """Format a number with the specified number of decimal places."""
        if decimals is None:
            decimals = self.config['max_decimals']
            
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if value == int(value):
                return str(int(value))
            return f"{value:.{decimals}f}"
        return str(value)

    def _format_value(self, value: Any, decimals: Optional[int] = None) -> str:
        """Format a value for display in the narrative."""
        if pd.isna(value):
            return "N/A"
        if isinstance(value, float):
            return self._format_number(value, decimals)
        if isinstance(value, (list, dict)):
            return json.dumps(value, indent=2)
        return str(value)

    def _generate_markdown_narrative(self) -> str:
        """Generate a markdown narrative from the analysis results."""
        if not self.insights:
            self.analyze()
            
        lines = ["# Data Analysis Report\n"]
        
        # Add dataset overview
        lines.extend([
            "## Dataset Overview\n",
            f"- **Number of variables**: {self.insights['dataset_shape']['columns']}",
            f"- **Number of observations**: {self.insights['dataset_shape']['rows']}",
            f"- **Missing cells**: {self.insights['dataset_shape']['missing_cells']} "
            f"({self._format_number(self.insights['dataset_shape']['missing_percent'])}%)",
            f"- **Duplicate rows**: {self.insights['dataset_shape']['duplicates']} "
            f"({self._format_number(self.insights['dataset_shape']['duplicates_percent'])}%)\n"
        ])
        
        # Add variable type summary
        lines.append("## Variable Types\n")
        for var_type, count in self.insights['variable_types'].items():
            if count > 0:
                lines.append(f"- **{var_type.title()}**: {count}")
        lines.append("")
        
        # Add detailed variable information
        lines.append("## Variable Details\n")
        
        for var_name, profile in self.insights['profiles'].items():
            lines.append(f"### {var_name} ({profile['role'].title()})\n")
            
            # Basic info
            lines.append("#### Overview")
            lines.extend([
                f"- **Type**: {profile['dtype']}",
                f"- **Missing Values**: {self._format_number(profile['missing_percent'])}%",
                f"- **Unique Values**: {profile['cardinality']} "
                f"({self._format_number(profile['unique_percent'])}%)\n"
            ])
            
            # Statistics based on variable type
            if profile['stats']:
                lines.append("#### Statistics")
                if profile['role'] == 'numeric':
                    stats = profile['stats']
                    lines.extend([
                        f"- **Mean**: {self._format_value(stats.get('mean'))}",
                        f"- **Standard Deviation**: {self._format_value(stats.get('std'))}",
                        f"- **Minimum**: {self._format_value(stats.get('min'))}",
                        f"- **25% Quartile**: {self._format_value(stats.get('q1'))}",
                        f"- **Median**: {self._format_value(stats.get('median'))}",
                        f"- **75% Quartile**: {self._format_value(stats.get('q3'))}",
                        f"- **Maximum**: {self._format_value(stats.get('max'))}",
                        f"- **IQR**: {self._format_value(stats.get('iqr'))}",
                        f"- **Skewness**: {self._format_value(stats.get('skew'))}",
                        f"- **Kurtosis**: {self._format_value(stats.get('kurtosis'))}"
                    ])
                elif profile['role'] == 'categorical':
                    stats = profile['stats']
                    lines.append(f"- **Most Common Value**: {stats.get('top')} "
                                f"({self._format_value(stats.get('freq'))} occurrences, "
                                f"{self._format_value(stats.get('freq_percent'))}%)")
                    lines.append(f"- **Unique Values**: {stats.get('n_unique')}")
                    
                    if stats.get('most_common'):
                        lines.append("\n**Most Common Values:**")
                        for value, count in stats['most_common'].items():
                            lines.append(f"- `{value}`: {count}")
                
                elif profile['role'] == 'datetime':
                    stats = profile['stats']
                    lines.extend([
                        f"- **Earliest**: {stats.get('min')}",
                        f"- **Latest**: {stats.get('max')}",
                        f"- **Time Span**: {stats.get('range')}"
                    ])
                
                elif profile['role'] == 'text':
                    stats = profile['stats']
                    lines.extend([
                        f"- **Average Length**: {self._format_value(stats.get('avg_length'))} characters",
                        f"- **Min Length**: {self._format_value(stats.get('min_length'))} characters",
                        f"- **Max Length**: {self._format_value(stats.get('max_length'))} characters",
                        f"- **Average Words**: {self._format_value(stats.get('avg_words'))}",
                        f"- **Min Words**: {self._format_value(stats.get('min_words'))}",
                        f"- **Max Words**: {self._format_value(stats.get('max_words'))}"
                    ])
                
                elif profile['role'] == 'boolean':
                    stats = profile['stats']
                    lines.extend([
                        f"- **True Values**: {self._format_value(stats.get('true_count'))} "
                        f"({self._format_value(stats.get('true_percent'))}%)",
                        f"- **False Values**: {self._format_value(stats.get('false_count'))} "
                        f"({self._format_value(stats.get('false_percent'))}%)",
                        f"- **Missing Values**: {self._format_value(stats.get('missing'))}"
                    ])
                
                lines.append("")
            
            # Add top values if available
            if profile.get('top_values'):
                lines.append("#### Most Common Values")
                for value, count in list(profile['top_values'].items())[:self.config['top_n']]:
                    lines.append(f"- `{value}`: {count}")
                if len(profile['top_values']) > self.config['top_n']:
                    lines.append(f"- ... and {len(profile['top_values']) - self.config['top_n']} more")
                lines.append("")
            
            # Add anomaly information for numeric columns
            if var_name in self.insights.get('anomalies', {}) and profile['role'] in ['numeric', 'integer', 'float']:
                anomaly = self.insights['anomalies'][var_name]
                if anomaly['count'] > 0:
                    lines.append("#### Anomaly Detection")
                    lines.append(f"- **Method**: {anomaly['method'].upper()} (threshold: {anomaly['threshold']})")
                    lines.append(f"- **Anomalies Detected**: {anomaly['count']} ({anomaly['percent']:.2f}%)")
                    if anomaly.get('lower_bound') is not None and anomaly.get('upper_bound') is not None:
                        lines.append(f"- **Range**: Values outside [{anomaly['lower_bound']:.2f}, {anomaly['upper_bound']:.2f}] are considered anomalous")
                    
                    # Show a sample of anomalous values if available
                    if anomaly.get('indices') and len(anomaly['indices']) > 0:
                        sample_size = min(3, len(anomaly['indices']))
                        lines.append(f"- **Sample Anomalies**: {', '.join(str(i) for i in anomaly['indices'][:sample_size])}" + 
                                    (f" (and {len(anomaly['indices']) - sample_size} more)" if len(anomaly['indices']) > sample_size else ""))
                    lines.append("")
            
            lines.append("---\n")
        
        # Add anomaly summary
        if 'anomalies' in self.insights and any(a['count'] > 0 for a in self.insights['anomalies'].values()):
            lines.append("## Anomaly Summary\n")
            lines.append("The following columns contain potential anomalies that may require further investigation:\n")
            
            anomaly_columns = [(col, data) for col, data in self.insights['anomalies'].items() 
                             if data['count'] > 0 and col in self.insights['profiles']]
            
            if anomaly_columns:
                lines.append("| Column | Type | Anomalies | Percentage | Method |")
                lines.append("|--------|------|-----------|------------|---------|")
                
                for col, data in sorted(anomaly_columns, key=lambda x: -x[1]['percent']):
                    profile = self.insights['profiles'][col]
                    lines.append(f"| {col} | {profile['dtype']} | {data['count']} | {data['percent']:.2f}% | {data['method'].upper()} |")
                
                lines.append("\n*Note: Anomalies are detected using statistical methods and should be reviewed by a domain expert.*\n")
        
        # Add correlation insights
        if 'correlations' in self.insights and any(self.insights['correlations'].values()):
            lines.append("## 🔗 Correlation Analysis\n")
            
            # Add Pearson correlations if available
            if self.insights['correlations'].get('pearson'):
                lines.append("### Pearson Correlation (Linear Relationships)\n")
                lines.append("The following pairs of variables show strong linear relationships:")
                lines.append("")
                lines.append("| Variables | Correlation | p-value |")
                lines.append("|-----------|-------------|---------|")
                
                for corr in sorted(self.insights['correlations']['pearson'], 
                                   key=lambda x: abs(x['correlation']), reverse=True):
                    p_val = f"{corr['p_value']:.3f}" if corr.get('p_value') is not None else "N/A"
                    lines.append(f"| {corr['pair'][0]} ↔ {corr['pair'][1]} | {corr['correlation']:.3f} | {p_val} |")
                lines.append("")
            
            # Add Spearman correlations if available
            if self.insights['correlations'].get('spearman'):
                lines.append("### Spearman's Rank Correlation (Monotonic Relationships)\n")
                lines.append("The following pairs of variables show strong monotonic relationships:")
                lines.append("")
                lines.append("| Variables | Correlation | p-value |")
                lines.append("|-----------|-------------|---------|")
                
                for corr in sorted(self.insights['correlations']['spearman'], 
                                   key=lambda x: abs(x['correlation']), reverse=True):
                    p_val = f"{corr['p_value']:.3f}" if corr.get('p_value') is not None else "N/A"
                    lines.append(f"| {corr['pair'][0]} ↔ {corr['pair'][1]} | {corr['correlation']:.3f} | {p_val} |")
                lines.append("")
            
            # Add Cramér's V if available
            if self.insights['correlations'].get('cramers_v'):
                lines.append("### Cramér's V (Categorical Associations)\n")
                lines.append("The following pairs of categorical variables show strong associations:")
                lines.append("")
                lines.append("| Variables | Cramér's V |")
                lines.append("|-----------|------------|")
                
                for corr in sorted(self.insights['correlations']['cramers_v'], 
                                   key=lambda x: abs(x['correlation']), reverse=True):
                    lines.append(f"| {corr['pair'][0]} ↔ {corr['pair'][1]} | {corr['correlation']:.3f} |")
                lines.append("")
            
            # Add Theil's U if available
            if self.insights['correlations'].get('theils_u'):
                lines.append("### Theil's U (Asymmetric Categorical Dependencies)\n")
                lines.append("The following variables show asymmetric dependencies (predictive relationships):")
                lines.append("")
                lines.append("| Predictor → Target | Theil's U |")
                lines.append("|---------------------|-----------|")
                
                for corr in sorted(self.insights['correlations']['theils_u'], 
                                   key=lambda x: abs(x['correlation']), reverse=True):
                    lines.append(f"| {corr['pair'][0]} → {corr['pair'][1]} | {corr['correlation']:.3f} |")
                lines.append("")
                
                lines.append("*Note: Theil's U ranges from 0 (no predictive power) to 1 (perfect prediction). "
                           "A value of 0.2 or higher typically indicates a meaningful predictive relationship.*")
                lines.append("")
        
        # Add text analysis insights
        if 'text_analysis' in self.insights and self.insights['text_analysis']:
            lines.append("## 📚 Text Analysis\n")
            
            for col, analysis in self.insights['text_analysis'].items():
                lines.append(f"### {col}\n")
                
                # Basic text statistics
                lines.extend([
                    "#### Text Statistics",
                    f"- **Documents Analyzed**: {analysis['count']}",
                    f"- **Average Length**: {analysis['avg_length']:.0f} characters",
                    f"- **Length Range**: {analysis['min_length']} - {analysis['max_length']} characters",
                ])
                
                # Sentiment analysis
                sentiment_emoji = "😊" if analysis['sentiment'] > 0.1 else "😐" if analysis['sentiment'] > -0.1 else "😞"
                sentiment_label = (
                    "Positive" if analysis['sentiment'] > 0.1 
                    else "Neutral" if analysis['sentiment'] > -0.1 
                    else "Negative"
                )
                
                subjectivity_label = (
                    "Subjective" if analysis['subjectivity'] > 0.5 
                    else "Objective"
                )
                
                lines.extend([
                    "#### Sentiment Analysis",
                    f"- **Overall Sentiment**: {sentiment_emoji} {sentiment_label} ({analysis['sentiment']:.2f})",
                    f"- **Subjectivity**: {subjectivity_label} ({analysis['subjectivity']:.2f})",
                ])
                
                # Readability score if available
                if analysis.get('readability') is not None:
                    readability = analysis['readability']
                    readability_label = (
                        "Very Easy" if readability >= 90 else
                        "Easy" if readability >= 80 else
                        "Fairly Easy" if readability >= 70 else
                        "Standard" if readability >= 60 else
                        "Fairly Difficult" if readability >= 50 else
                        "Difficult" if readability >= 30 else
                        "Very Difficult"
                    )
                    lines.append(f"- **Readability**: {readability:.1f} - {readability_label}")
                
                # Top keywords
                if analysis.get('keywords'):
                    lines.append("\n#### Top Keywords")
                    keywords = ", ".join(f'`{k}`' for k in analysis['keywords'])
                    lines.append(f"{keywords}\n")
                
                # Word cloud if available
                if analysis.get('word_count'):
                    top_words = sorted(
                        analysis['word_count'].items(), 
                        key=lambda x: x[1], 
                        reverse=True
                    )[:10]  # Top 10 words
                    if top_words:
                        lines.append("#### Most Frequent Words")
                        word_lines = []
                        for word, count in top_words:
                            word_lines.append(f"`{word}` ({count})")
                        lines.append(", ".join(word_lines) + "\n")
                
                lines.append("")  # Add extra newline between text columns
        
        # Add timestamp
        lines.append(f"\n*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
        return "\n".join(lines)

    def _generate_text_narrative(self) -> str:
        """Generate a plain text narrative from the analysis results."""
        # Convert markdown to plain text by removing markdown syntax
        markdown = self._generate_markdown_narrative()
        # Simple markdown to text conversion
        text = []
        for line in markdown.split('\n'):
            # Remove headers
            line = line.lstrip('#').lstrip()
            # Remove bold/italic markers
            line = line.replace('**', '').replace('`', '')
            text.append(line)
        return '\n'.join(text)

    def _generate_html_narrative(self) -> str:
        """Generate an HTML narrative from the analysis results."""
        # This is a simplified version - in a real implementation, you might want to use a template engine
        markdown = self._generate_markdown_narrative()
        
        # Simple markdown to HTML conversion
        html = ['<html><head><title>Data Analysis Report</title>']
        html.append('<style>'
                  'body { font-family: Arial, sans-serif; line-height: 1.6; max-width: 900px; margin: 0 auto; padding: 20px; }'
                  'h1 { color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px; }'
                  'h2 { color: #3498db; margin-top: 30px; }'
                  'h3 { color: #2980b9; }'
                  'h4 { color: #16a085; }'
                  'code { background: #f5f5f5; padding: 2px 5px; border-radius: 3px; }'
                  'pre { background: #f8f9fa; padding: 10px; border-radius: 5px; overflow-x: auto; }'
                  'hr { border: 0; height: 1px; background: #eee; margin: 30px 0; }'
                  '</style>'
                  '</head><body>')
        
        # Convert markdown headers and lists to HTML
        in_list = False
        for line in markdown.split('\n'):
            if line.startswith('### '):
                html.append(f'<h3>{line[4:]}</h3>')
            elif line.startswith('## '):
                html.append(f'<h2>{line[3:]}</h2>')
            elif line.startswith('# '):
                html.append(f'<h1>{line[2:]}</h1>')
            elif line.startswith('- '):
                if not in_list:
                    html.append('<ul>')
                    in_list = True
                html.append(f'<li>{line[2:]}</li>')
            else:
                if in_list and not line.strip():
                    html.append('</ul>')
                    in_list = False
                elif line.strip() == '---':
                    html.append('<hr>')
                elif line.strip():
                    html.append(f'<p>{line}</p>')
                else:
                    html.append('')
        
        if in_list:
            html.append('</ul>')
        
        html.append('</body></html>')
        return '\n'.join(html)

    def narrate(self, format: str = 'markdown', ai: bool = False, **kwargs) -> str:
        """
        Generate a natural language narrative from the analysis.
        
        Args:
            format: Output format ('text', 'markdown', 'html', 'json')
            ai: If True, uses AI to generate a natural language summary
            **kwargs: Additional arguments to pass to the narrative generator
                     (e.g., model, temperature, max_tokens)
            
        Returns:
            String containing the narrative in the specified format
            
        Note:
            When using AI (ai=True), the format parameter only affects the output structure,
            not the content generation which is always done by the AI model.
        """
        if not self.insights and not hasattr(self, 'profiler'):
            self.analyze()
        
        # If AI narration is requested, generate a summary using the NarrativeGenerator
        if ai:
            try:
                # Initialize the narrative generator with any provided kwargs
                generator = NarrativeGenerator(**{
                    k: v for k, v in kwargs.items() 
                    if k in ['model', 'temperature', 'max_tokens']
                })
                
                # Generate the AI summary
                ai_summary = generator.generate_summary(
                    insights=self.insights,
                    tone=kwargs.get('tone', 'professional'),
                    max_tokens=kwargs.get('max_tokens', 600)
                )
                
                # Format the AI summary based on the requested format
                if format == 'json':
                    return json.dumps({
                        'ai_summary': ai_summary,
                        'insights': self.insights
                    }, indent=2, default=str)
                elif format == 'html':
                    return f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>AI-Generated Data Analysis Summary</title>
                        <style>
                            body {{ 
                                font-family: Arial, sans-serif; 
                                line-height: 1.6; 
                                max-width: 800px; 
                                margin: 0 auto; 
                                padding: 20px;
                                color: #333;
                            }}
                            h1 {{ color: #2c3e50; }}
                            .summary {{ white-space: pre-line; }}
                        </style>
                    </head>
                    <body>
                        <h1>AI-Generated Data Analysis Summary</h1>
                        <div class="summary">{ai_summary}</div>
                    </body>
                    </html>
                    """
                elif format == 'markdown':
                    return f"# AI-Generated Data Analysis Summary\n\n{ai_summary}"
                else:  # text
                    return ai_summary
                    
            except Exception as e:
                # Fall back to non-AI narration if there's an error
                print(f"Warning: AI narration failed - {str(e)}. Falling back to standard narration.")
        
        # Standard non-AI narration
        format = format.lower()
        if format == 'markdown':
            return self._generate_markdown_narrative()
        elif format == 'html':
            return self._generate_html_narrative()
        elif format == 'json':
            return json.dumps(self.insights, indent=2, default=str)
        else:  # Default to text
            return self._generate_text_narrative()

    def export(self, file_path: Union[str, Path], format: Optional[str] = None) -> None:
        """
        Export the analysis to a file.
        
        Args:
            file_path: Path to save the output file
            format: Output format (inferred from file extension if not provided)
        """
        if format is None:
            format = str(file_path).split('.')[-1].lower()
        
        # Map file extensions to formats
        ext_to_format = {
            'md': 'markdown',
            'html': 'html',
            'htm': 'html',
            'json': 'json',
            'txt': 'text'
        }
        
        # Default to text if format not recognized
        output_format = ext_to_format.get(format, 'text')
        
        content = self.narrate(format=output_format)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
