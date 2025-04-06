import unittest
import pytest
from unittest.mock import patch, Mock, MagicMock
from app.services.sentiment_factory import SentimentAnalyzerFactory, AnalyzerType, OpenAISentimentAnalyzer
from app.services.local_sentiment_service import LocalSentimentAnalyzer

class TestSentimentAnalyzerFactory(unittest.TestCase):
    def setUp(self):
        self.factory = SentimentAnalyzerFactory()
        
    def test_singleton_pattern(self):
        """Test that factory is a singleton"""
        factory2 = SentimentAnalyzerFactory()
        self.assertIs(self.factory, factory2)
        
    def test_get_openai_analyzer(self):
        """Test getting OpenAI analyzer"""
        analyzer = SentimentAnalyzerFactory.get_analyzer(AnalyzerType.OPENAI)
        self.assertIsInstance(analyzer, OpenAISentimentAnalyzer)
        
    def test_get_local_analyzer(self):
        """Test getting Local analyzer"""
        analyzer = SentimentAnalyzerFactory.get_analyzer(AnalyzerType.LOCAL)
        self.assertIsInstance(analyzer, LocalSentimentAnalyzer)
        
    def test_analyzer_caching(self):
        """Test that analyzer is cached and reused"""
        analyzer1 = SentimentAnalyzerFactory.get_analyzer(AnalyzerType.OPENAI)
        analyzer2 = SentimentAnalyzerFactory.get_analyzer(AnalyzerType.OPENAI)
        self.assertIs(analyzer1, analyzer2)
        
    def test_analyzer_switching(self):
        """Test switching between analyzer types"""
        openai_analyzer = SentimentAnalyzerFactory.get_analyzer(AnalyzerType.OPENAI)
        local_analyzer = SentimentAnalyzerFactory.get_analyzer(AnalyzerType.LOCAL)
        self.assertIsNot(openai_analyzer, local_analyzer)
        
    def test_invalid_analyzer_type(self):
        """Test handling of invalid analyzer type"""
        with self.assertRaises(ValueError):
            SentimentAnalyzerFactory.get_analyzer("invalid")
            
    @patch('app.services.sentiment_service.OpenAISentimentAnalyzer.analyze_single')
    def test_openai_analyzer_functionality(self, mock_analyze):
        """Test OpenAI analyzer functionality"""
        mock_analyze.return_value = {"sentiment": "positive", "score": 0.8}
        analyzer = SentimentAnalyzerFactory.get_analyzer(AnalyzerType.OPENAI)
        result = analyzer.analyze_single("Test title")
        self.assertEqual(result["sentiment"], "positive")
        self.assertEqual(result["score"], 0.8)
        
    @patch('app.services.local_sentiment_service.LocalSentimentAnalyzer.analyze_single')
    def test_local_analyzer_functionality(self, mock_analyze):
        """Test Local analyzer functionality"""
        mock_analyze.return_value = {"sentiment": "negative", "score": -0.5}
        analyzer = SentimentAnalyzerFactory.get_analyzer(AnalyzerType.LOCAL)
        result = analyzer.analyze_single("Test title")
        self.assertEqual(result["sentiment"], "negative")
        self.assertEqual(result["score"], -0.5)

if __name__ == '__main__':
    unittest.main() 