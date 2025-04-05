import os
from datetime import datetime
from flask import Blueprint, render_template, request, send_file, redirect, url_for
from app.config import Config
from app.utils.logger import logger
from app.models.database import get_db, get_search_history, get_search_results, delete_search_history, save_search_results
from app.services.news_service import news_service
import json

# Create blueprint
bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Render the home page"""
    history = get_search_history()
    return render_template('index.html', history=history)

@bp.route('/search', methods=['POST'])
def search():
    """Handle search requests"""
    query = request.form.get('query', '').strip()
    time_filter = request.form.get('time', 'all')
    max_results = int(request.form.get('max_results', '20'))
    
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
            return render_template('index.html', 
                                error="Không tìm thấy kết quả nào",
                                query=query,
                                history=history)
        
        try:
            # Save search results to database
            logger.info(f"Saving {len(results)} results to database")
            save_search_results(query, results)
            
            # Get updated history after saving new results
            history = get_search_history()
            
            # Generate report files
            txt_file, json_file = generate_report(query, results)
            
            return render_template('index.html', 
                                 results=results, 
                                 query=query,
                                 history=history,
                                 txt_file=txt_file,
                                 json_file=json_file)
        except ValueError as e:
            logger.error(f"Error saving search results: {e}")
            return render_template('index.html',
                                 error=str(e),
                                 query=query,
                                 history=history)
                             
    except Exception as e:
        logger.error(f"Search error: {e}")
        return render_template('index.html', 
                             error=f"Có lỗi xảy ra: {str(e)}",
                             history=history)

@bp.route('/history/<int:search_id>')
def view_history(search_id):
    """View historical search results"""
    try:
        # Get search results from database
        search_data = get_search_results(search_id)
        
        # Get full history for sidebar
        history = get_search_history()
        
        return render_template('index.html',
                             results=search_data['articles'],
                             query=search_data['search_term'],
                             history=history)
                             
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