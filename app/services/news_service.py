import time
import urllib.parse
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import json

from app.config import Config
from app.utils.logger import logger
from app.utils.webdriver import WebDriverManager
from app.services.sentiment_factory import SentimentAnalyzerFactory, AnalyzerType
from app.models.database import get_analyzer_settings

class NewsService:
    def __init__(self):
        """Initialize news service with analyzer type from database"""
        analyzer_type = get_analyzer_settings()
        self.sentiment_analyzer = SentimentAnalyzerFactory.get_analyzer(AnalyzerType(analyzer_type))
        
    def set_analyzer_type(self, analyzer_type: AnalyzerType):
        """Change the sentiment analyzer type"""
        self.sentiment_analyzer = SentimentAnalyzerFactory.get_analyzer(analyzer_type)
        
    def search(self, query, time_filter="all", max_results=20):
        """Search for news articles"""
        logger.info(f"Starting search for: {query} with max_results: {max_results}")
        
        driver = None
        try:
            driver = WebDriverManager.get_driver()
            articles_data = self._fetch_articles(driver, query, time_filter, max_results)
            return self._process_articles(articles_data)
        except Exception as e:
            logger.error(f"Error in search_news: {e}")
            raise
        finally:
            # Không đóng driver ở đây nữa, để WebDriverManager quản lý
            pass
    
    def _fetch_articles(self, driver, query, time_filter, max_results):
        """Fetch articles from Google News"""
        try:
            # Construct Google News URL
            base_url = "https://www.google.com/search"
            encoded_query = urllib.parse.quote(query)
            params = f"?q={encoded_query}&tbm=nws&hl=vi&gl=VN&num={max_results}"
            
            # Add time filter if specified
            if time_filter != "all":
                if time_filter == "1h":
                    params += "&tbs=qdr:h"
                elif time_filter == "1d":
                    params += "&tbs=qdr:d"
                elif time_filter == "7d":
                    params += "&tbs=qdr:w"
                elif time_filter == "1m":
                    params += "&tbs=qdr:m"
            
            url = base_url + params
            logger.info(f"HTTP Request to: {url}")
            
            driver.get(url)
            time.sleep(3)  # Initial wait for page load
            
            # Scroll to load more results
            scroll_attempts = 0
            max_scroll_attempts = 5
            while scroll_attempts < max_scroll_attempts:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                scroll_attempts += 1
            
            # Wait for news articles to be present
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.SoaBEf"))
                )
            except Exception as e:
                logger.warning(f"Timeout waiting for articles: {e}")
            
            # Parse the page
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            articles = soup.find_all('div', class_='SoaBEf')
            
            logger.info(f"Found {len(articles)} articles in HTML")
            return articles[:max_results]
            
        except Exception as e:
            logger.error(f"Error fetching articles: {e}")
            raise
    
    def _process_articles(self, articles):
        """Process fetched articles and analyze sentiments"""
        results = []
        titles_to_analyze = []
        articles_data = []
        
        for article in articles:
            try:
                # Extract article details
                title_elem = article.find('div', class_='n0jPhd')
                if not title_elem:
                    continue
                    
                title = title_elem.text.strip()
                
                # Get the actual link
                link_elem = title_elem.find_parent('a')
                if not link_elem:
                    continue
                    
                link = link_elem.get('href', '')
                
                # Get description
                desc_elem = article.find('div', class_='GI74Re')
                description = desc_elem.text.strip() if desc_elem else ''
                
                # Get source and date
                source_elem = article.find('div', class_='MgUUmf')
                source = source_elem.text.strip() if source_elem else 'Unknown'
                
                date_elem = article.find('div', class_='LfVVr')
                date = date_elem.text.strip() if date_elem else ''
                
                # Create article data
                article_data = {
                    'title': title,
                    'description': description,
                    'link': link,
                    'source': source,
                    'date': date
                }
                
                # Validate article data
                if not all([title, description, link]):
                    logger.warning(f"Skipping invalid article: {article_data}")
                    continue
                
                articles_data.append(article_data)
                titles_to_analyze.append(title)
                
            except Exception as e:
                logger.error(f"Error processing article: {e}")
                continue
        
        # Analyze sentiments for all titles
        if titles_to_analyze:
            logger.info(f"Analyzing sentiments for {len(titles_to_analyze)} articles")
            sentiment_results = self.sentiment_analyzer.analyze_batch(titles_to_analyze)
            logger.info(f"Received sentiment results: {json.dumps(sentiment_results, ensure_ascii=False)}")
            
            # Combine article data with sentiment results
            for article_data in articles_data:
                title = article_data['title']
                if title in sentiment_results:
                    sentiment_data = sentiment_results[title]
                    article_data['sentiment'] = sentiment_data['sentiment']
                    article_data['sentiment_score'] = sentiment_data['score']
                    article_data['sentiment_explanation'] = sentiment_data.get('explanation', '')
                    results.append(article_data)
                    logger.info(f"Added article with sentiment: {article_data['title']} - {article_data['sentiment']} ({article_data['sentiment_score']})")
        
        if not results:
            logger.warning("No valid articles found after processing")
            return []  # Return empty list instead of default article
        
        logger.info(f"Processed {len(results)} valid articles")
        return results

# Create global news service instance
news_service = NewsService() 