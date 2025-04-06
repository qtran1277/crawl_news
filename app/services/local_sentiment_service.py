from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import json
from app.config import Config
from app.utils.logger import logger

class LocalSentimentAnalyzer:
    def __init__(self):
        """Initialize Local LM Studio client"""
        self.api_url = "http://localhost:1234/v1/chat/completions"  # LM Studio default URL
    
    def analyze_batch(self, titles, max_workers=5):
        """Analyze sentiments for multiple titles concurrently"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_title = {
                executor.submit(self.analyze_single, title): title 
                for title in titles
            }
            
            # Get results as they complete
            for future in as_completed(future_to_title):
                title = future_to_title[future]
                try:
                    results[title] = future.result()
                except Exception as e:
                    logger.error(f"Error analyzing sentiment for title: {title[:50]}... Error: {str(e)}")
                    results[title] = {"sentiment": "neutral", "score": 0}
        
        return results
    
    def analyze_single(self, title):
        """Analyze sentiment for a single title"""
        try:
            # Clean and prepare the title
            cleaned_title = title.strip()
            
            # Construct the prompt
            prompt = f"""Analyze the sentiment of this Vietnamese news title: "{cleaned_title}"
            Classify it as one of: positive, negative, or neutral.
            Also provide a sentiment score from -1 (most negative) to 1 (most positive).
            Return ONLY a JSON object in this format: {{"sentiment": "positive/negative/neutral", "score": float}}
            Do not include any explanation or additional text."""
            
            # Prepare the request payload
            payload = {
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "max_tokens": 100,
                "stream": False
            }
            
            # Make request to local LM Studio API
            headers = {"Content-Type": "application/json"}
            response = requests.post(self.api_url, json=payload, headers=headers)
            
            if response.status_code != 200:
                raise Exception(f"API call failed with status code: {response.status_code}")
            
            # Parse response
            response_data = response.json()
            content = response_data['choices'][0]['message']['content']
            
            # Remove markdown formatting if present
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            elif content.startswith('```'):
                content = content.replace('```', '').strip()
                
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON response from LM Studio: {content}")
                return {"sentiment": "neutral", "score": 0}
            
            # Validate sentiment
            if result['sentiment'] not in ['positive', 'negative', 'neutral']:
                result['sentiment'] = 'neutral'
            
            # Validate score
            score = float(result['score'])
            if not -1 <= score <= 1:
                score = 0
            result['score'] = score
            
            return result
            
        except Exception as e:
            logger.error(f"Error in local sentiment analysis: {str(e)}")
            return {"sentiment": "neutral", "score": 0}

# Create global local sentiment analyzer instance
local_sentiment_analyzer = LocalSentimentAnalyzer() 