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
            return {"sentiment": "neutral", "score": 0, "explanation": "API key not set"}

        try:
            prompt = f"""Analyze the sentiment of the following text and return a JSON object with these fields:
            - sentiment: "positive", "negative", or "neutral"
            - score: float between -1 and 1
            - explanation: brief explanation of the analysis
            
            Text: {text}"""

            logger.info(f"Sending request to OpenAI for text: {text[:50]}...")
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=150
            )
            
            logger.info(f"OpenAI raw response: {response.choices[0].message.content}")

            try:
                result = json.loads(response.choices[0].message.content)
                logger.info(f"OpenAI parsed result: {json.dumps(result, ensure_ascii=False)}")
                
                if not isinstance(result, dict):
                    raise ValueError("Response is not a dictionary")
                
                # Validate and sanitize result
                if "sentiment" not in result or result["sentiment"] not in ["positive", "negative", "neutral"]:
                    result["sentiment"] = "neutral"
                    
                if "score" not in result or not isinstance(result["score"], (int, float)):
                    result["score"] = 0
                else:
                    result["score"] = max(-1, min(1, float(result["score"])))  # Clamp between -1 and 1
                    
                if "explanation" not in result or not isinstance(result["explanation"], str):
                    result["explanation"] = "No explanation provided"
                
                logger.info(f"Final sentiment result: {json.dumps(result, ensure_ascii=False)}")
                return result
                
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.error(f"Error parsing OpenAI response: {str(e)}")
                return {"sentiment": "neutral", "score": 0, "explanation": "Error parsing response"}

        except Exception as e:
            logger.error(f"Error analyzing sentiment with OpenAI: {str(e)}")
            return {"sentiment": "neutral", "score": 0, "explanation": f"Error: {str(e)}"}

    def analyze_batch(self, texts, max_workers=5):
        """Analyze sentiment for multiple texts in parallel"""
        logger.info(f"Starting batch sentiment analysis for {len(texts)} texts")
        results = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_text = {executor.submit(self.analyze_single, text): text for text in texts}
            for future in as_completed(future_to_text):
                text = future_to_text[future]
                try:
                    result = future.result()
                    results[text] = result
                    logger.info(f"Analyzed text: '{text[:50]}...' - Result: {json.dumps(result, ensure_ascii=False)}")
                except Exception as e:
                    logger.error(f"Error analyzing text '{text}': {str(e)}")
                    results[text] = {"sentiment": "neutral", "score": 0, "explanation": f"Error: {str(e)}"}
        
        logger.info(f"Completed batch analysis. Results: {json.dumps(results, ensure_ascii=False)}")
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