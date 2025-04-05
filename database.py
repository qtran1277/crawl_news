import sqlite3
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the SQLite database."""
    conn = sqlite3.connect('news_search.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database and create tables if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create search history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            search_term TEXT NOT NULL,
            search_time DATETIME NOT NULL,
            results TEXT NOT NULL
        )
    ''')
    
    # Create api_keys table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider TEXT NOT NULL UNIQUE,
            api_key TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def save_search_results(search_term, results):
    """Save search results to database"""
    if not results:
        raise ValueError("Không thể lưu kết quả tìm kiếm rỗng")
    
    # Convert results to JSON string
    try:
        # Đảm bảo tất cả các trường cần thiết đều có
        for result in results:
            if 'date' not in result:
                result['date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if 'sentiment_score' not in result:
                result['sentiment_score'] = 0
            if 'sentiment' not in result:
                result['sentiment'] = 'neutral'
        
        results_json = json.dumps(results, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error converting results to JSON: {e}")
        raise ValueError("Không thể chuyển đổi kết quả tìm kiếm thành JSON")
    
    conn = sqlite3.connect('news_search.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO searches (search_term, search_time, results) VALUES (?, CURRENT_TIMESTAMP, ?)",
                  (search_term, results_json))
        conn.commit()
        return c.lastrowid
    except Exception as e:
        conn.rollback()
        logger.error(f"Error saving to database: {e}")
        raise
    finally:
        conn.close()

def get_search_history():
    conn = sqlite3.connect('news_search.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, search_term, search_time FROM searches ORDER BY search_time DESC")
    history = []
    for row in c.fetchall():
        # Convert search_time string to datetime object
        search_time = datetime.strptime(row['search_time'], '%Y-%m-%d %H:%M:%S')
        history.append({
            'id': row['id'],
            'search_term': row['search_term'],
            'search_time': search_time
        })
    conn.close()
    return history

def get_search_results(search_id):
    """Get search results by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT search_term, results FROM searches WHERE id = ?", (search_id,))
        row = cursor.fetchone()
        if row:
            return {
                'search_term': row['search_term'],
                'results': row['results']
            }
        return None
    except Exception as e:
        logger.error(f"Error getting search results: {str(e)}")
        return None
    finally:
        conn.close()

def delete_search_history(search_id):
    conn = sqlite3.connect('news_search.db')
    c = conn.cursor()
    c.execute("DELETE FROM searches WHERE id = ?", (search_id,))
    conn.commit()
    conn.close()

def save_api_key(provider, api_key):
    """Save API key for a provider"""
    try:
        # Kiểm tra định dạng API key
        if provider == 'openai' and not api_key.startswith('sk-'):
            logger.error(f"Invalid OpenAI API key format: {api_key[:30]}...")
            return False
            
        conn = sqlite3.connect('news_search.db')
        cursor = conn.cursor()
        
        # Log API key trước khi lưu
        logger.info(f"Saving API key for {provider}: {api_key[:30] if api_key else 'None'}...")
        
        try:
            # Thử xóa API key cũ nếu có
            cursor.execute("DELETE FROM api_keys WHERE provider = ?", (provider,))
            
            # Thêm API key mới
            cursor.execute("""
                INSERT INTO api_keys (provider, api_key, created_at)
                VALUES (?, ?, datetime('now'))
            """, (provider, api_key))
            
            conn.commit()
            logger.info(f"API key saved successfully for {provider}")
            return True
            
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Database error while saving API key: {str(e)}")
            return False
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Error saving API key for {provider}: {str(e)}")
        return False

def get_api_key(provider):
    """Get API key for a provider"""
    try:
        conn = sqlite3.connect('news_search.db')
        cursor = conn.cursor()
        cursor.execute('SELECT api_key FROM api_keys WHERE provider = ?', (provider,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            logger.info(f"Found API key for provider {provider} in database")
            return result[0]
        else:
            logger.info(f"No API key found for provider {provider} in database")
            return None
    except Exception as e:
        logger.error(f"Error getting API key for {provider}: {str(e)}")
        return None

def get_all_api_keys():
    conn = sqlite3.connect('news_search.db')
    c = conn.cursor()
    c.execute("SELECT provider, api_key, timestamp FROM api_keys ORDER BY provider")
    keys = c.fetchall()
    conn.close()
    return keys 