from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from app.utils.logger import logger
import os

class WebDriverManager:
    _driver = None
    
    @classmethod
    def get_driver(cls):
        """Get or create WebDriver instance"""
        if cls._driver is None:
            try:
                # Set up Firefox options
                options = Options()
                options.add_argument('--headless')  # Run in headless mode
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                
                # Use geckodriver from drivers directory
                current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                geckodriver_path = os.path.join(current_dir, 'drivers', 'geckodriver')
                
                # Make sure geckodriver is executable
                os.chmod(geckodriver_path, 0o755)
                
                service = Service(executable_path=geckodriver_path)
                cls._driver = webdriver.Firefox(service=service, options=options)
                
                logger.info("WebDriver initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing WebDriver: {e}")
                raise
        
        return cls._driver
    
    @classmethod
    def quit_driver(cls):
        """Quit WebDriver instance if it exists"""
        if cls._driver:
            try:
                cls._driver.quit()
                cls._driver = None
                logger.info("WebDriver quit successfully")
            except Exception as e:
                logger.error(f"Error quitting WebDriver: {e}")
                raise 