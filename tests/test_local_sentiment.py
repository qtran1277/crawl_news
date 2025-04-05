import unittest
from unittest.mock import patch, Mock
from app.services.local_sentiment_service import LocalSentimentAnalyzer

class TestLocalSentimentAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = LocalSentimentAnalyzer()
        self.test_titles = [
            "Việt Nam đạt thành tích xuất sắc tại SEA Games",  # positive
            "Tai nạn giao thông nghiêm trọng làm 5 người thương vong",  # negative
            "Dự báo thời tiết ngày mai: Nhiệt độ 25-30 độ C",  # neutral
        ]
        
    @patch('requests.post')
    def test_analyze_single_positive(self, mock_post):
        # Mock response for positive sentiment
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': '{"sentiment": "positive", "score": 0.8}'
                }
            }]
        }
        mock_post.return_value = mock_response
        
        result = self.analyzer.analyze_single(self.test_titles[0])
        self.assertEqual(result['sentiment'], 'positive')
        self.assertGreater(result['score'], 0)
        
    @patch('requests.post')
    def test_analyze_single_negative(self, mock_post):
        # Mock response for negative sentiment
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': '{"sentiment": "negative", "score": -0.7}'
                }
            }]
        }
        mock_post.return_value = mock_response
        
        result = self.analyzer.analyze_single(self.test_titles[1])
        self.assertEqual(result['sentiment'], 'negative')
        self.assertLess(result['score'], 0)
        
    @patch('requests.post')
    def test_analyze_single_neutral(self, mock_post):
        # Mock response for neutral sentiment
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': '{"sentiment": "neutral", "score": 0.0}'
                }
            }]
        }
        mock_post.return_value = mock_response
        
        result = self.analyzer.analyze_single(self.test_titles[2])
        self.assertEqual(result['sentiment'], 'neutral')
        self.assertEqual(result['score'], 0.0)
        
    @patch('requests.post')
    def test_analyze_batch(self, mock_post):
        # Mock response for batch analysis
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = [
            {'choices': [{'message': {'content': '{"sentiment": "positive", "score": 0.8}'}}]},
            {'choices': [{'message': {'content': '{"sentiment": "negative", "score": -0.7}'}}]},
            {'choices': [{'message': {'content': '{"sentiment": "neutral", "score": 0.0}'}}]}
        ]
        mock_post.return_value = mock_response
        
        results = self.analyzer.analyze_batch(self.test_titles)
        
        self.assertEqual(len(results), 3)
        self.assertEqual(results[self.test_titles[0]]['sentiment'], 'positive')
        self.assertEqual(results[self.test_titles[1]]['sentiment'], 'negative')
        self.assertEqual(results[self.test_titles[2]]['sentiment'], 'neutral')
        
    @patch('requests.post')
    def test_error_handling(self, mock_post):
        # Test API error
        mock_post.side_effect = Exception("API connection error")
        
        result = self.analyzer.analyze_single("Test title")
        self.assertEqual(result['sentiment'], 'neutral')
        self.assertEqual(result['score'], 0)
        
    @patch('requests.post')
    def test_invalid_response(self, mock_post):
        # Test invalid API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': '{"sentiment": "invalid", "score": 2.0}'
                }
            }]
        }
        mock_post.return_value = mock_response
        
        result = self.analyzer.analyze_single("Test title")
        self.assertEqual(result['sentiment'], 'neutral')  # Should default to neutral
        self.assertEqual(result['score'], 0)  # Should clamp to valid range

if __name__ == '__main__':
    unittest.main() 