from enum import Enum
from app.services.sentiment_analyzer import SentimentAnalyzerInterface
from app.services.sentiment_service import OpenAISentimentAnalyzer
from app.services.local_sentiment_service import LocalSentimentAnalyzer

class AnalyzerType(Enum):
    OPENAI = "openai"
    LOCAL = "local"

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