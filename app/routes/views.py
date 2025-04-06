import os
from datetime import datetime
from flask import Blueprint, render_template, request, send_file, redirect, url_for, jsonify, flash, session
from app.config import Config
from app.utils.logger import logger
from app.models.database import get_db, get_search_history, get_search_results, delete_search_history, save_search_results, get_api_key, save_api_key, save_analyzer_settings
from app.services.news_service import news_service
from app.services.sentiment_factory import SentimentAnalyzerFactory, AnalyzerType
from openai import OpenAI
import json

# Create sentiment factory instance
sentiment_factory = SentimentAnalyzerFactory()

def get_openai_client():
    """Get OpenAI client with API key from database"""
    api_key = get_api_key('openai')
    if not api_key:
        return None
    return OpenAI(api_key=api_key)

# Create blueprint
bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Render the home page"""
    print("Getting search history")
    history = get_search_history()
    print(f"History: {history}")
    logger.info(f"History data before rendering: {history}")
    logger.info(f"History type: {type(history)}")
    if history:
        logger.info(f"First item type: {type(history[0])}")
        logger.info(f"First item keys: {history[0].keys() if isinstance(history[0], dict) else 'Not a dict'}")
        logger.info(f"First item values: {history[0]}")
        logger.info(f"History length: {len(history)}")
    else:
        logger.info("History is empty")
    return render_template('index.html', history=history)

@bp.route('/search', methods=['POST'])
def search():
    """Handle search requests"""
    data = request.get_json()
    query = data.get('query', '').strip()
    time_filter = data.get('time_filter', 'all')
    max_results = int(data.get('max_results', '20'))
    
    # Get history for all responses
    history = get_search_history()
    
    # Log the received query for debugging
    logger.info(f"Received search query: '{query}'")
    
    try:
        logger.info(f"Processing search request for: {query}")
        results = news_service.search(query, time_filter, max_results)
        
        # Log the results for debugging
        logger.info(f"Found {len(results)} results for query: {query}")
        
        if not results:
            logger.warning(f"No results found for query: {query}")
            return jsonify({
                'error': "Không tìm thấy kết quả nào",
                'query': query,
                'history': history
            })
        
        try:
            # Save search results to database
            logger.info(f"Saving {len(results)} results to database")
            save_search_results(query, results)
            
            # Get updated history after saving new results
            history = get_search_history()
            
            # Generate report files
            txt_file, json_file = generate_report(query, results)
            
            return jsonify({
                'results': results,
                'query': query,
                'history': history,
                'txt_file': txt_file,
                'json_file': json_file
            })
        except ValueError as e:
            logger.error(f"Error saving search results: {e}")
            return jsonify({
                'error': str(e),
                'query': query,
                'history': history
            })
                             
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({
            'error': f"Có lỗi xảy ra: {str(e)}",
            'history': history
        })

@bp.route('/history/<int:search_id>')
def view_history(search_id):
    """View historical search results"""
    try:
        # Get search results from database
        search_data = get_search_results(search_id)
        
        # Get full history for sidebar
        history = get_search_history()
        
        # Log the data for debugging
        logger.info(f"Search data: {search_data}")
        logger.info(f"History: {history}")
        
        return render_template('index.html',
                             results=search_data['articles'],
                             query=search_data['search_term'],
                             history=history,
                             show_results=True)  # Add flag to show results section
                             
    except Exception as e:
        logger.error(f"Error viewing history: {e}")
        return redirect(url_for('main.index'))

@bp.route('/delete_history/<int:search_id>')
def delete_history(search_id):
    """Delete a search history entry"""
    try:
        delete_search_history(search_id)
        return redirect(url_for('main.index'))
    except Exception as e:
        logger.error(f"Error deleting history: {e}")
        return redirect(url_for('main.index'))

@bp.route('/download/<path:filename>')
def download_file(filename):
    """Download a report file"""
    try:
        return send_file(filename, as_attachment=True)
    except Exception as e:
        logger.error(f"Error downloading file {filename}: {str(e)}")
        return "File not found", 404

def generate_report(company_name, results):
    """Generate report files for search results"""
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
    
    os.makedirs(Config.REPORTS_DIR, exist_ok=True)
    report_filename = f"{Config.REPORTS_DIR}/report_{company_name}_{timestamp}.txt"
    json_filename = f"{Config.REPORTS_DIR}/report_{company_name}_{timestamp}.json"
    
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(report)
    
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    return report_filename, json_filename

@bp.route('/settings')
def settings():
    """Render API settings page"""
    # Lấy API key từ database
    current_api_key = get_api_key('openai')
    return render_template('settings.html', api_key=current_api_key)

@bp.route('/save_settings', methods=['POST'])
def save_settings():
    """Save API settings"""
    try:
        api_key = request.form.get('api_key')
        
        if not api_key:
            flash('API key không được để trống', 'danger')
            return redirect(url_for('main.settings'))
            
        # Kiểm tra định dạng API key
        if not api_key.startswith('sk-'):
            flash('API key không đúng định dạng. API key phải bắt đầu bằng "sk-"', 'danger')
            return redirect(url_for('main.settings'))
        
        # Lưu API key vào database
        if save_api_key('openai', api_key):
            # Kiểm tra kết nối với API key mới
            client = OpenAI(api_key=api_key)
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
            flash('Có lỗi xảy ra khi lưu cài đặt', 'danger')
            return redirect(url_for('main.settings'))
        
        return redirect(url_for('main.index'))
        
    except Exception as e:
        logger.error(f"Error saving settings: {str(e)}")
        flash('Có lỗi xảy ra khi lưu cài đặt', 'danger')
        return redirect(url_for('main.settings'))

@bp.route('/handle_analyzer_settings', methods=['POST'])
def handle_analyzer_settings():
    """Handle analyzer settings changes"""
    try:
        analyzer_type = request.form.get('analyzer_type')
        if not analyzer_type:
            return jsonify({'error': 'Analyzer type is required'}), 400
            
        # Kiểm tra loại analyzer hợp lệ
        if analyzer_type not in ['openai', 'local']:
            return jsonify({'error': 'Invalid analyzer type'}), 400
            
        # Lưu vào database
        if not save_analyzer_settings(analyzer_type):
            return jsonify({'error': 'Failed to save settings'}), 500
        
        # Cập nhật factory và news service
        sentiment_factory.set_analyzer_type(AnalyzerType(analyzer_type))
        news_service.set_analyzer_type(AnalyzerType(analyzer_type))
        
        return jsonify({'message': 'Settings saved successfully'}), 200
    except Exception as e:
        logger.error(f"Error saving analyzer settings: {e}")
        return jsonify({'error': str(e)}), 500 