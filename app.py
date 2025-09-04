from flask import Flask, jsonify
from models import db, Task, SyncQueue
from routes import tasks_bp, sync_bp
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Database configuration - Railway will provide DATABASE_URL automatically
    database_url = os.getenv("DATABASE_URL")
    if database_url and database_url.startswith("postgres://"):
        # Railway uses postgres://, but SQLAlchemy 1.4+ requires postgresql://
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "sqlite:///database.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Initialize database
    db.init_app(app)

    # Create tables
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully!")
        except Exception as e:
            print(f"Error creating tables: {e}")

    # Register blueprints
    app.register_blueprint(tasks_bp)
    app.register_blueprint(sync_bp)

    # Health check endpoint
    @app.route("/health")
    def health():
        try:
            # Test database connection
            db.session.execute(db.text('SELECT 1'))
            db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        return jsonify({
            "ok": True, 
            "message": "Task Sync API is running",
            "database": db_status,
            "environment": os.getenv("FLASK_ENV", "production")
        })

    # Root endpoint with API information
    @app.route("/")
    def root():
        return jsonify({
            "name": "Task Sync API",
            "version": "1.0.0",
            "status": "running",
            "endpoints": {
                "tasks": "/api/tasks",
                "sync": "/api/sync",
                "health": "/health"
            },
            "docs": "https://github.com/yourusername/your-repo"
        })

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Endpoint not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500

    return app

# For Railway deployment
app = create_app()

if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_ENV") == "development"
    port = int(os.getenv("PORT", 5000))
    app.run(debug=debug_mode, host="0.0.0.0", port=port)