from concurrent.futures import ThreadPoolExecutor, as_completed
import openai
from app.config import Config
from app.utils.logger import logger
from app.services.sentiment_analyzer import SentimentAnalyzerInterface

class OpenAISentimentAnalyzer(SentimentAnalyzerInterface):
    def __init__(self):
        """Initialize OpenAI client"""
        openai.api_key = Config.OPENAI_API_KEY
    
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
            Format the response as JSON: {{"sentiment": "positive/negative/neutral", "score": float}}"""
            
            # Get completion from OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=100
            )
            
            # Parse response
            result = eval(response.choices[0].message.content)
            
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
            logger.error(f"Error in OpenAI sentiment analysis: {str(e)}")
            return {"sentiment": "neutral", "score": 0}

# Create global sentiment analyzer instance
sentiment_analyzer = OpenAISentimentAnalyzer() 