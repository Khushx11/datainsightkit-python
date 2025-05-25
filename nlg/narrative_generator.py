"""
Natural Language Generation module for DataInsightKit.

This module provides AI-powered narrative generation using LLMs to convert
raw data insights into human-readable summaries and explanations.
"""

import os
import json
import openai
from typing import Dict, Any, Optional

class NarrativeGenerator:
    """
    Generates natural language narratives from data insights using LLMs.
    
    This class provides methods to convert raw analysis results into
    human-readable summaries using OpenAI's language models.
    """
    
    def __init__(self, model: str = "gpt-3.5-turbo"):
        """
        Initialize the NarrativeGenerator with a specific LLM model.
        
        Args:
            model: The name of the OpenAI model to use (default: "gpt-3.5-turbo")
            
        Note:
            The OPENAI_API_KEY environment variable must be set with a valid
            OpenAI API key before initializing this class.
        """
        self.model = model
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."
                "You can get a key at https://platform.openai.com/account/api-keys"
            )
        openai.api_key = self.api_key

    def generate_summary(
        self, 
        insights: Dict[str, Any], 
        tone: str = "professional",
        max_tokens: int = 600,
        temperature: float = 0.5
    ) -> str:
        """
        Generate a natural language summary from raw insights using an LLM.
        
        Args:
            insights: Dictionary containing the analysis results
            tone: Desired tone for the summary (e.g., "professional", "casual", "technical")
            max_tokens: Maximum number of tokens in the generated summary
            temperature: Controls randomness (0.0 = deterministic, 1.0 = creative)
            
        Returns:
            str: A natural language summary of the insights
            
        Raises:
            openai.error.OpenAIError: If there's an error with the OpenAI API
        """
        try:
            # Prepare the prompt with context and instructions
            prompt = (
                "You are a senior data analyst with expertise in explaining complex data insights\n\n"
                f"TONE: {tone.capitalize()}, clear, and concise\n\n"
                "TASK: Analyze the following dataset insights and generate a comprehensive summary that highlights "
                "the most important findings, patterns, and recommendations. Focus on actionable insights "
                "and business implications.\n\n"
                "INSIGHTS DATA:\n"
                f"{json.dumps(insights, indent=2)}\n\n"
                "STRUCTURE YOUR RESPONSE WITH THESE SECTIONS:\n"
                "1. **Overview**: 2-3 sentence summary of the dataset and key findings\n"
                "2. **Key Insights**: 3-5 bullet points of the most important findings\n"
                "3. **Recommendations**: Actionable suggestions based on the data\n"
                "4. **Next Steps**: Suggested follow-up analyses or data collection"
            )
            
            # Make the API call
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful data analyst assistant that explains data insights in a clear and professional manner."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            # Extract and return the generated text
            return response['choices'][0]['message']['content'].strip()
            
        except Exception as e:
            raise Exception(f"Failed to generate narrative: {str(e)}")

    def explain_insight(
        self, 
        insight_type: str, 
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a detailed explanation for a specific insight type.
        
        Args:
            insight_type: Type of insight (e.g., 'correlation', 'anomaly', 'trend')
            data: The specific insight data to explain
            context: Additional context about the dataset or analysis
            
        Returns:
            str: A natural language explanation of the insight
        """
        try:
            explanations = {
                "correlation": self._explain_correlation,
                "anomaly": self._explain_anomaly,
                "trend": self._explain_trend,
                "distribution": self._explain_distribution,
                "text_analysis": self._explain_text_analysis
            }
            
            explainer = explanations.get(insight_type.lower(), self._explain_generic)
            return explainer(data, context or {})
            
        except Exception as e:
            return f"Unable to generate explanation: {str(e)}"
    
    def _explain_correlation(self, data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Generate explanation for correlation insights."""
        prompt = (
            f"Explain the correlation between {data.get('variables', ['variable1', 'variable2'])} "
            f"with a coefficient of {data.get('coefficient', 0.0):.2f}. "
            f"The p-value is {data.get('p_value', 0.0):.4f}. "
            "Provide a business interpretation of this relationship."
        )
        return self._call_llm(prompt)
    
    def _explain_anomaly(self, data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Generate explanation for anomaly detection."""
        prompt = (
            f"Explain this anomaly found in {data.get('variable', 'the data')} at index {data.get('index', 'N/A')}. "
            f"The value is {data.get('value', 'N/A')} which is {data.get('deviation', 'significantly')} different "
            "from the expected range. Provide potential reasons and business impact."
        )
        return self._call_llm(prompt)
    
    def _explain_trend(self, data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Generate explanation for trend analysis."""
        prompt = (
            f"Explain the trend in {data.get('variable', 'the data')} showing a "
            f"{data.get('trend_type', 'trend')} from {data.get('start_value', 'start')} to {data.get('end_value', 'end')}. "
            "Provide business context and potential implications."
        )
        return self._call_llm(prompt)
    
    def _explain_distribution(self, data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Generate explanation for data distribution."""
        prompt = (
            f"Describe the distribution of {data.get('variable', 'the data')} with the following statistics: "
            f"mean={data.get('mean', 'N/A')}, median={data.get('median', 'N/A')}, "
            f"std={data.get('std', 'N/A')}, min={data.get('min', 'N/A')}, max={data.get('max', 'N/A')}. "
            "Explain what this means in simple terms and potential implications."
        )
        return self._call_llm(prompt)
    
    def _explain_text_analysis(self, data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Generate explanation for text analysis results."""
        prompt = (
            f"Summarize the text analysis results showing {data.get('sentiment', 'a sentiment')} sentiment "
            f"with a score of {data.get('sentiment_score', 0):.2f}. "
            f"Key phrases include: {', '.join(data.get('key_phrases', []))}. "
            "Provide a concise interpretation of these findings."
        )
        return self._call_llm(prompt)
    
    def _explain_generic(self, data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Generate a generic explanation for unsupported insight types."""
        prompt = (
            f"Explain the following data insight in simple terms: {str(data)}. "
            "Focus on what it means and why it might be important."
        )
        return self._call_llm(prompt)
    
    def _call_llm(self, prompt: str) -> str:
        """Helper method to call the LLM with error handling."""
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful data analyst that explains insights in clear, non-technical terms."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            return response['choices'][0]['message']['content'].strip()
        except Exception as e:
            return f"Unable to generate explanation: {str(e)}"
