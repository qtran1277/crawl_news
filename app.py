from flask import Flask, render_template, request, send_file, jsonify, redirect, url_for, session, flash
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os
import logging
import json
import urllib.parse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
import time
from urllib.parse import urlparse, parse_qs
from openai import OpenAI
from database import init_db, save_search_results, get_search_history, get_search_results, delete_search_history, get_api_key, save_api_key
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.services.sentiment_factory import SentimentAnalyzerFactory, AnalyzerType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

# Initialize sentiment analyzer factory
sentiment_factory = SentimentAnalyzerFactory()

# Default analyzer type
DEFAULT_ANALYZER = AnalyzerType.OPENAI

# Get OpenAI API key from environment variable
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

def setup_driver():
    try:
        firefox_options = Options()
        firefox_options.add_argument("--headless")
        firefox_options.add_argument("--width=1920")
        firefox_options.add_argument("--height=1080")
        
        service = Service(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=firefox_options)
        return driver
    except Exception as e:
        logging.error(f"Error setting up WebDriver: {str(e)}")
        raise

def analyze_sentiment(title):
    """Analyze the sentiment of a news title using OpenAI API"""
    try:
        # Clean and prepare the title
        title = title.strip()
        if not title:
            return {"sentiment": "neutral", "score": 0}
            
        prompt = f"""Analyze the sentiment of this Vietnamese news title: "{title}"
        First, classify it as one of: positive (tích cực), negative (tiêu cực), or neutral (trung lập).
        Then, give it a score:
        - For positive sentiment: score from 1 to 10 (higher means more positive)
        - For negative sentiment: score from -1 to -10 (lower means more negative)
        - For neutral sentiment: score is 0
        
        Respond in this exact format:
        sentiment: [positive/negative/neutral]
        score: [number]
        
        Consider the context and nuance of Vietnamese language."""
        
        # Get appropriate client using analyzer type from factory
        analyzer_type = sentiment_factory.get_current_analyzer_type()
        client = get_client(analyzer_type.value)
        if not client:
            logger.error("Could not get client")
            return {"sentiment": "neutral", "score": 0}
            
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a sentiment analysis expert. Analyze Vietnamese news titles and respond with sentiment and score in the exact format specified."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=50
        )
        
        result = response.choices[0].message.content.strip().lower()
        
        # Parse the response
        sentiment = "neutral"
        score = 0
        
        try:
            # Extract sentiment and score from response
            for line in result.split('\n'):
                if 'sentiment:' in line:
                    sentiment = line.split(':')[1].strip()
                elif 'score:' in line:
                    score = float(line.split(':')[1].strip())
            
            # Validate sentiment
            if sentiment not in ['positive', 'negative', 'neutral']:
                sentiment = 'neutral'
                score = 0
                
            # Validate score based on sentiment
            if sentiment == 'positive' and (score < 1 or score > 10):
                score = 5
            elif sentiment == 'negative' and (score > -1 or score < -10):
                score = -5
            elif sentiment == 'neutral' and score != 0:
                score = 0
                
        except:
            sentiment = 'neutral'
            score = 0
            
        return {"sentiment": sentiment, "score": score}
            
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {str(e)}")
        return {"sentiment": "neutral", "score": 0}

def analyze_sentiment_batch(titles, max_workers=5):
    """Analyze sentiments for multiple titles concurrently"""
    results = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_title = {executor.submit(analyze_sentiment, title): title for title in titles}
        
        # Get results as they complete
        for future in as_completed(future_to_title):
            title = future_to_title[future]
            try:
                results[title] = future.result()
            except Exception as e:
                logger.error(f"Error analyzing sentiment for title: {title[:50]}... Error: {str(e)}")
                results[title] = {"sentiment": "neutral", "score": 0}
    
    return results

def search_news(query, time_filter="all", max_results=20):
    logger.info(f"Starting search for: {query} with max_results: {max_results}")
    
    # Configure Selenium
    service = Service(GeckoDriverManager().install())
    options = webdriver.FirefoxOptions()
    options.add_argument('--headless')
    options.add_argument('--width=1920')
    options.add_argument('--height=1080')
    driver = webdriver.Firefox(service=service, options=options)
    
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
        
        results = []
        titles_to_analyze = []
        articles_data = []
        
        for article in articles[:max_results]:
            try:
                # Extract article details
                title_elem = article.find('div', class_='n0jPhd')
                if not title_elem:
                    continue
                    
                title = title_elem.text.strip()
                
                # Get the actual link
                link_elem = title_elem.find_parent('a')
                link = link_elem['href'] if link_elem else ""
                
                # Clean up Google redirect URL if present
                if link and "google.com/url?" in link:
                    try:
                        parsed = urlparse(link)
                        actual_url = parse_qs(parsed.query)['url'][0]
                        link = actual_url
                    except:
                        pass
                
                # Get description
                description = ""
                desc_elem = article.find('div', class_='GI74Re')
                if desc_elem:
                    description = desc_elem.text.strip()
                
                # Get source and date
                source = ""
                date = ""
                meta_elem = article.find('div', class_='OSrXXb')
                if meta_elem:
                    meta_text = meta_elem.text.strip()
                    parts = [p.strip() for p in meta_text.split('·') if p.strip()]
                    if len(parts) >= 2:
                        date = parts[0]  # First part is date
                        source = parts[1]  # Second part is source
                    elif len(parts) == 1:
                        # If only one part, check if it's a date or source
                        if any(time_indicator in parts[0].lower() for time_indicator in ['phút', 'giờ', 'ngày', 'tuần', 'tháng', 'năm', 'thg']):
                            date = parts[0]
                        else:
                            source = parts[0]
                
                # Ensure we have a date
                if not date:
                    date = "Không rõ thời gian"
                
                # Backup plan: If no source found, try to get from link
                if not source and link:
                    try:
                        parsed_url = urlparse(link)
                        source = parsed_url.netloc.replace('www.', '')
                    except:
                        pass
                
                # Store article data and title for batch sentiment analysis
                articles_data.append({
                    'title': title,
                    'description': description,
                    'link': link,
                    'source': source,
                    'date': date
                })
                titles_to_analyze.append(title)
                
            except Exception as e:
                logger.error(f"Error processing article: {e}")
                continue
        
        if titles_to_analyze:
            # Perform batch sentiment analysis
            sentiment_results = analyze_sentiment_batch(titles_to_analyze)
            
            # Combine article data with sentiment results
            for article_data in articles_data:
                title = article_data['title']
                if title in sentiment_results:
                    article_data.update({
                        'sentiment': sentiment_results[title]['sentiment'],
                        'sentiment_score': sentiment_results[title]['score']
                    })
                    results.append(article_data)
        
        if not results:
            logger.warning("No results were processed successfully")
        else:
            logger.info(f"Successfully processed {len(results)} articles")
            
        return results
        
    except Exception as e:
        logger.error(f"Error in search_news: {e}")
        raise
        
    finally:
        try:
            driver.quit()
        except Exception as e:
            logger.error(f"Error closing driver: {e}")

def generate_report(company_name, results):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    report = f"BÁO CÁO TIN TỨC - {company_name}\n"
    report += f"Ngày: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    report += f"Tổng số tin tức: {len(results)}\n\n"
    
    sources = {}
    for item in results:
        source = item['source']
        if source not in sources:
            sources[source] = []
        sources[source].append(item)
    
    for source, items in sources.items():
        report += f"=== TIN TỨC TỪ {source} ===\n"
        for i, item in enumerate(items, 1):
            report += f"{i}. Tiêu đề: {item['title']}\n"
            report += f"   Mô tả: {item['description']}\n"
            report += f"   Ngày đăng: {item['date']}\n"
            report += f"   Link: {item['link']}\n\n"
    
    os.makedirs('reports', exist_ok=True)
    report_filename = f"reports/report_{company_name}_{timestamp}.txt"
    json_filename = f"reports/report_{company_name}_{timestamp}.json"
    
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(report)
    
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    return report_filename, json_filename

@app.route('/')
def index():
    # Get search history
    history = get_search_history()
    logger.info("Rendering index template with history")
    try:
        template_path = os.path.join(app.template_folder, 'index.html')
        logger.info(f"Template path: {template_path}")
        logger.info(f"Template exists: {os.path.exists(template_path)}")
        return render_template('index.html', history=history)
    except Exception as e:
        logger.error(f"Error rendering template: {str(e)}")
        return str(e), 500

@app.route('/settings')
def settings():
    """Render API settings page"""
    # Lấy API key từ database
    current_api_key = get_api_key('openai')
    return render_template('settings.html', api_key=current_api_key)

@app.route('/save_settings', methods=['POST'])
def save_settings():
    """Save API settings"""
    try:
        api_key = request.form.get('api_key')
        
        if not api_key:
            flash('API key không được để trống', 'danger')
            return redirect(url_for('settings'))
            
        # Kiểm tra định dạng API key
        if not api_key.startswith('sk-'):
            flash('API key không đúng định dạng. API key phải bắt đầu bằng "sk-"', 'danger')
            return redirect(url_for('settings'))
        
        # Lưu API key vào database
        if save_api_key('openai', api_key):
            # Kiểm tra kết nối với API key mới
            client = get_openai_client()
            if client:
                try:
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": "Hello"}],
                        max_tokens=5
                    )
                    flash('Cài đặt đã được lưu và kết nối thành công', 'success')
                except Exception as e:
                    logger.error(f"Error testing API key: {str(e)}")
                    flash('API key đã được lưu nhưng không thể kết nối. Vui lòng kiểm tra lại API key.', 'warning')
            else:
                flash('Cài đặt đã được lưu thành công', 'success')
        else:
            flash('Có lỗi xảy ra khi lưu cài đặt', 'danger')
            return redirect(url_for('settings'))
        
        return redirect(url_for('index'))
        
    except Exception as e:
        logger.error(f"Error saving settings: {str(e)}")
        flash('Có lỗi xảy ra khi lưu cài đặt', 'danger')
        return redirect(url_for('settings'))

@app.route('/analyzer_settings')
def analyzer_settings():
    """Render analyzer settings page"""
    # Get current analyzer type from session or use default
    current_analyzer = session.get('analyzer_type', DEFAULT_ANALYZER.value)
    
    # Check OpenAI connection
    openai_status = False
    try:
        # Get OpenAI client
        client = get_client(AnalyzerType.OPENAI.value)
        if client:
            # Try a simple API call to check connection
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            openai_status = True
    except Exception as e:
        logger.error(f"OpenAI connection error: {str(e)}")
    
    # Check LM Studio connection
    local_status = False
    try:
        # Get local client
        client = get_client(AnalyzerType.LOCAL.value)
        if client:
            # Try a simple API call to check connection
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            local_status = True
    except Exception as e:
        logger.error(f"LM Studio connection error: {str(e)}")
    
    return render_template(
        'analyzer_settings.html',
        current_analyzer=current_analyzer,
        openai_status=openai_status,
        local_status=local_status
    )

@app.route('/save_analyzer_settings', methods=['POST'])
def save_analyzer_settings():
    """Save analyzer settings"""
    try:
        analyzer_type = request.form.get('analyzer_type')
        
        if analyzer_type not in [AnalyzerType.OPENAI.value, AnalyzerType.LOCAL.value]:
            return jsonify({'error': 'Loại analyzer không hợp lệ'}), 400
        
        # Save to session
        session['analyzer_type'] = analyzer_type
        
        # Update factory
        sentiment_factory.set_analyzer_type(AnalyzerType(analyzer_type))
        
        return jsonify({'message': 'Cài đặt đã được lưu thành công'})
        
    except Exception as e:
        logger.error(f"Error saving analyzer settings: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        query = data.get('query')
        time_filter = data.get('time_filter', 'all')
        max_results = int(data.get('max_results', 20))
        analyzer_type = data.get('analyzer_type', AnalyzerType.OPENAI.value)
        
        if not query:
            return jsonify({'error': 'Vui lòng nhập từ khóa tìm kiếm'}), 400
            
        # Tìm kiếm tin tức
        results = search_news(query, time_filter, max_results)
        
        # Lưu kết quả vào database
        search_id = save_search_results(query, results)
        
        return jsonify({
            'results': results,
            'search_id': search_id
        })
        
    except Exception as e:
        logger.error(f"Error in search: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/view_history/<int:search_id>')
def view_history(search_id):
    """View historical search results"""
    try:
        # Get current search results
        data = get_search_results(search_id)
        if not data:
            flash('Không tìm thấy kết quả tìm kiếm', 'warning')
            return redirect(url_for('index'))
            
        # Get all search history
        history = get_search_history()
        
        # Parse the results JSON
        articles = json.loads(data['results'])
        
        # Add articles count to history items
        for item in history:
            if item['id'] == search_id:
                item['articles'] = articles
            else:
                # Get articles count for other history items
                other_data = get_search_results(item['id'])
                if other_data:
                    item['articles'] = json.loads(other_data['results'])
                else:
                    item['articles'] = []
        
        return render_template('view_history.html', 
                             results=articles,
                             history=history,
                             current_search_id=search_id)
        
    except Exception as e:
        logger.error(f"Error viewing history: {str(e)}")
        flash('Có lỗi xảy ra khi xem lịch sử', 'danger')
        return redirect(url_for('index'))

@app.route('/delete_history/<int:search_id>')
def delete_history(search_id):
    """Delete historical search results"""
    try:
        delete_search_history(search_id)
        flash('Đã xóa kết quả tìm kiếm thành công', 'success')
    except Exception as e:
        logger.error(f"Error deleting history: {str(e)}")
        flash('Có lỗi xảy ra khi xóa lịch sử', 'danger')
        
    return redirect(url_for('index'))

def get_openai_client():
    """Get OpenAI client with current configuration"""
    try:
        # Lấy API key từ database
        api_key = get_api_key('openai')
        logger.info(f"API key from database: {api_key[:30] if api_key else 'None'}...")
        
        # Kiểm tra nếu không có API key
        if not api_key:
            logger.error("No API key found in database")
            return None
            
        # Tạo client với base URL mặc định là OpenAI
        return OpenAI(
            api_key=api_key,
            base_url="https://api.openai.com/v1"
        )
    except Exception as e:
        logger.error(f"Error creating OpenAI client: {str(e)}")
        return None

def get_local_client():
    """Get local LM Studio client"""
    try:
        # Lấy API key từ database
        api_key = get_api_key('openai')
        logger.info(f"API key from database: {api_key[:30] if api_key else 'None'}...")
        
        # Kiểm tra nếu không có API key
        if not api_key:
            logger.error("No API key found in database")
            return None
            
        # Tạo client với base URL là local LM Studio
        return OpenAI(
            api_key=api_key,
            base_url="http://localhost:1234/v1"
        )
    except Exception as e:
        logger.error(f"Error creating local client: {str(e)}")
        return None

def get_client(analyzer_type=None):
    """Get appropriate client based on analyzer type"""
    try:
        # Use passed analyzer_type or default
        if analyzer_type is None:
            analyzer_type = DEFAULT_ANALYZER.value
        logger.info(f"Using analyzer type: {analyzer_type}")
        
        if analyzer_type == AnalyzerType.LOCAL.value:
            return get_local_client()
        else:
            return get_openai_client()
    except Exception as e:
        logger.error(f"Error getting client: {str(e)}")
        return None

if __name__ == '__main__':
    init_db()
    app.run(debug=True) 