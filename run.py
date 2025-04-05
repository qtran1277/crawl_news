from app import create_app
from database import init_db

if __name__ == "__main__":
    # Initialize database
    init_db()
    
    # Create and run application
    app = create_app()
    app.run(debug=True) 