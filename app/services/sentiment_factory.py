from enum import Enum
from app.services.sentiment_analyzer import SentimentAnalyzerInterface
from app.services.local_sentiment_service import LocalSentimentAnalyzer
from openai import OpenAI
from app.utils.logger import logger
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

class AnalyzerType(Enum):
    OPENAI = "openai"
    LOCAL = "local"

class OpenAISentimentAnalyzer(SentimentAnalyzerInterface):
    def __init__(self):
        """Initialize OpenAI client with API key from environment variable"""
        self.client = None
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            logger.error("OPENAI_API_KEY environment variable is not set")

    def analyze_single(self, text):
        """Analyze sentiment of a single text using OpenAI API"""
        if not self.client:
            logger.error("OpenAI client not initialized. Please set API key first.")
            return None

        try:
            prompt = f"""Analyze the sentiment of the following Vietnamese text and return a JSON object with these fields:
            - sentiment: "positive", "negative", or "neutral"
            - score: float between -1 and 1
            
            Text: {text}
            
            Consider the context and nuance of Vietnamese language. For example:
            - Positive: good news, achievements, success
            - Negative: problems, issues, failures
            - Neutral: factual statements, announcements
            
            Return ONLY the JSON object, no additional text."""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=150
            )

            try:
                result = json.loads(response.choices[0].message.content)
                if not isinstance(result, dict):
                    logger.error(f"Invalid response format: {response.choices[0].message.content}")
                    return None
                
                # Validate sentiment
                if "sentiment" not in result or result["sentiment"] not in ["positive", "negative", "neutral"]:
                    logger.error(f"Invalid sentiment value: {result.get('sentiment')}")
                    return None
                    
                # Validate score
                if "score" not in result or not isinstance(result["score"], (int, float)):
                    logger.error(f"Invalid score value: {result.get('score')}")
                    return None
                    
                # Ensure score is within range
                result["score"] = max(min(float(result["score"]), 1.0), -1.0)
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse OpenAI response: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {str(e)}")
            return None

    def analyze_batch(self, texts, max_workers=5):
        """Analyze sentiments for multiple texts concurrently"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_text = {executor.submit(self.analyze_single, text): text for text in texts}
            
            # Get results as they complete
            for future in as_completed(future_to_text):
                text = future_to_text[future]
                try:
                    result = future.result()
                    if result:  # Only add valid results
                        results[text] = result
                except Exception as e:
                    logger.error(f"Error analyzing sentiment for text: {text[:50]}... Error: {str(e)}")
        
        return results

class SentimentAnalyzerFactory:
    _instance = None
    _analyzer = None
    _analyzer_type = AnalyzerType.OPENAI  # Default analyzer type
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SentimentAnalyzerFactory, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def get_current_analyzer_type(cls) -> AnalyzerType:
        """
        Get current analyzer type
        Returns:
            AnalyzerType: Current analyzer type
        """
        return cls._analyzer_type
    
    @classmethod
    def get_analyzer(cls, analyzer_type: AnalyzerType = AnalyzerType.OPENAI) -> SentimentAnalyzerInterface:
        """
        Get sentiment analyzer instance based on type
        Args:
            analyzer_type: Type of analyzer to use (OPENAI or LOCAL)
        Returns:
            SentimentAnalyzerInterface instance
        """
        if cls._analyzer is None or cls._analyzer_type != analyzer_type:
            if analyzer_type == AnalyzerType.OPENAI:
                cls._analyzer = OpenAISentimentAnalyzer()
            elif analyzer_type == AnalyzerType.LOCAL:
                cls._analyzer = LocalSentimentAnalyzer()
            else:
                raise ValueError(f"Unknown analyzer type: {analyzer_type}")
            cls._analyzer_type = analyzer_type
        return cls._analyzer
    
    @classmethod
    def set_analyzer_type(cls, analyzer_type: AnalyzerType):
        """
        Change the analyzer type
        Args:
            analyzer_type: New analyzer type to use
        """
        cls._analyzer = None  # Force recreation of analyzer
        cls.get_analyzer(analyzer_type)

    @staticmethod
    def create_analyzer(analyzer_type: AnalyzerType) -> SentimentAnalyzerInterface:
        """Create a sentiment analyzer based on the specified type"""
        if analyzer_type == AnalyzerType.LOCAL:
            return LocalSentimentAnalyzer()
        elif analyzer_type == AnalyzerType.OPENAI:
            return OpenAISentimentAnalyzer()
        else:
            raise ValueError(f"Unknown analyzer type: {analyzer_type}")

# Create factory instance
sentiment_factory = SentimentAnalyzerFactory() 