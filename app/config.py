import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # OpenAI API Key
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Database
    DATABASE = 'news_search.db'
    
    # Reports directory
    REPORTS_DIR = 'reports'
    
    # Logging
    LOG_FILE = 'app.log'
    
    # Search settings
    DEFAULT_MAX_RESULTS = 20
    DEFAULT_TIME_FILTER = 'all'
    
    # API endpoints
    NEWS_API_ENDPOINT = 'https://newsapi.org/v2/everything'
    GOOGLE_NEWS_ENDPOINT = 'https://news.google.com/rss/search'
    
    # Application Settings
    MAX_RESULTS = 20
    DEBUG = True
    
    # Selenium Configuration
    SELENIUM_OPTIONS = {
        'headless': True,
        'width': 1920,
        'height': 1080
    }
    
    # Logging Configuration
    LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    
    # File Paths
    TEMPLATES_DIR = 'templates'
    STATIC_DIR = 'static' 