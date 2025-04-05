import unittest
from unittest.mock import patch, Mock
from app.services.news_service import NewsService
from app.services.sentiment_factory import AnalyzerType

class TestNewsService(unittest.TestCase):
    def setUp(self):
        self.news_service = NewsService()
        
    def test_init_with_default_analyzer(self):
        """Test initialization with default analyzer (OpenAI)"""
        self.assertEqual(self.news_service.sentiment_analyzer.__class__.__name__, 'OpenAISentimentAnalyzer')
        
    def test_init_with_local_analyzer(self):
        """Test initialization with local analyzer"""
        news_service = NewsService(analyzer_type=AnalyzerType.LOCAL)
        self.assertEqual(news_service.sentiment_analyzer.__class__.__name__, 'LocalSentimentAnalyzer')
        
    def test_set_analyzer_type(self):
        """Test changing analyzer type"""
        self.news_service.set_analyzer_type(AnalyzerType.LOCAL)
        self.assertEqual(self.news_service.sentiment_analyzer.__class__.__name__, 'LocalSentimentAnalyzer')
        
        self.news_service.set_analyzer_type(AnalyzerType.OPENAI)
        self.assertEqual(self.news_service.sentiment_analyzer.__class__.__name__, 'OpenAISentimentAnalyzer')
        
    @patch('app.services.news_service.WebDriverManager')
    @patch('app.services.news_service.NewsService._process_articles')
    def test_search_with_openai_analyzer(self, mock_process, mock_driver_manager):
        """Test search functionality with OpenAI analyzer"""
        # Mock WebDriver
        mock_driver = Mock()
        mock_driver.page_source = "<html><body><div class='SoaBEf'>Test Article</div></body></html>"
        mock_driver_manager.get_driver.return_value = mock_driver
        
        # Mock process_articles
        mock_process.return_value = [{'title': 'Test Title', 'url': 'http://test.com'}]
        
        results = self.news_service.search('test query')
        self.assertIsNotNone(results)
        mock_process.assert_called_once()
        
    @patch('app.services.news_service.WebDriverManager')
    @patch('app.services.news_service.NewsService._process_articles')
    def test_search_with_local_analyzer(self, mock_process, mock_driver_manager):
        """Test search functionality with Local analyzer"""
        news_service = NewsService(analyzer_type=AnalyzerType.LOCAL)
        
        # Mock WebDriver
        mock_driver = Mock()
        mock_driver.page_source = "<html><body><div class='SoaBEf'>Test Article</div></body></html>"
        mock_driver_manager.get_driver.return_value = mock_driver
        
        # Mock process_articles
        mock_process.return_value = [{'title': 'Test Title', 'url': 'http://test.com'}]
        
        results = news_service.search('test query')
        self.assertIsNotNone(results)
        mock_process.assert_called_once()

if __name__ == '__main__':
    unittest.main() 