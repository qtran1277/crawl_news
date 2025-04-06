from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from app.utils.logger import logger
import os
import time

class WebDriverManager:
    _driver = None
    _last_used = 0
    
    @classmethod
    def get_driver(cls):
        """Get or create WebDriver instance"""
        current_time = time.time()
        
        # Nếu driver đã tồn tại và đã được sử dụng gần đây (trong vòng 30 giây), sử dụng lại
        if cls._driver is not None and (current_time - cls._last_used) < 30:
            cls._last_used = current_time
            return cls._driver
            
        # Nếu driver đã tồn tại nhưng không được sử dụng gần đây, đóng nó
        if cls._driver is not None:
            try:
                cls._driver.quit()
                logger.info("Closed existing WebDriver due to inactivity")
            except Exception as e:
                logger.error(f"Error closing existing WebDriver: {e}")
            cls._driver = None
        
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
            cls._last_used = current_time
            
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