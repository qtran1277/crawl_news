import sqlite3
import json
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

def get_db():
    db = sqlite3.connect('news_search.db')
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    cursor = db.cursor()
    
    # Create searches table with all fields
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS searches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        search_term TEXT NOT NULL,
        search_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        results TEXT NOT NULL
    )
    ''')
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
    ''')
    
    # Create default admin user if not exists
    cursor.execute('SELECT * FROM users WHERE username = ?', ('admin',))
    if not cursor.fetchone():
        from werkzeug.security import generate_password_hash
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                      ('admin', generate_password_hash('admin123')))
    
    db.commit()
    db.close()

def save_search_results(search_term, articles):
    """Save search results to database"""
    if not articles:
        raise ValueError("Không thể lưu kết quả tìm kiếm rỗng")
    
    # Convert results to JSON string
    try:
        articles_json = json.dumps(articles, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error converting results to JSON: {e}")
        raise ValueError("Không thể chuyển đổi kết quả tìm kiếm thành JSON")
    
    conn = sqlite3.connect('news_search.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO searches (search_term, search_time, results) VALUES (?, CURRENT_TIMESTAMP, ?)",
                  (search_term, articles_json))
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Error saving to database: {e}")
        raise
    finally:
        conn.close()

def get_search_history():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
    SELECT id, search_term, search_time
    FROM searches
    ORDER BY search_time DESC
    LIMIT 50
    ''')
    history = cursor.fetchall()
    db.close()
    return history

def get_search_results(search_id):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT search_term, results FROM searches WHERE id = ?', (search_id,))
    result = cursor.fetchone()
    
    if result:
        search_term = result['search_term']
        articles = json.loads(result['results']) if result['results'] else []
    else:
        search_term = ''
        articles = []
    
    db.close()
    return {'search_term': search_term, 'articles': articles}

def delete_search_history(search_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM searches WHERE id = ?', (search_id,))
    db.commit()
    db.close()

def save_api_key(provider, api_key):
    conn = sqlite3.connect('news_search.db')
    c = conn.cursor()
    
    # Check if provider already exists
    c.execute("SELECT id FROM api_keys WHERE provider = ?", (provider,))
    existing = c.fetchone()
    
    if existing:
        # Update existing key
        c.execute("""UPDATE api_keys 
                    SET api_key = ?, timestamp = ?
                    WHERE provider = ?""",
                 (api_key, datetime.now(), provider))
    else:
        # Insert new key
        c.execute("""INSERT INTO api_keys (provider, api_key, timestamp)
                    VALUES (?, ?, ?)""",
                 (provider, api_key, datetime.now()))
    
    conn.commit()
    conn.close()

def get_api_key(provider):
    conn = sqlite3.connect('news_search.db')
    c = conn.cursor()
    c.execute("SELECT api_key FROM api_keys WHERE provider = ?", (provider,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def get_all_api_keys():
    conn = sqlite3.connect('news_search.db')
    c = conn.cursor()
    c.execute("SELECT provider, api_key, timestamp FROM api_keys ORDER BY provider")
    keys = c.fetchall()
    conn.close()
    return keys 