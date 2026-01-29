import logging

from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from todo_list.config import settings
from todo_list.extensions import db, migrate
from todo_list.api.dependencies import init_dependencies


"""Flask application factory"""

def create_app():
    app = Flask(__name__)
    
    # ─────────────────────────────────────────────────────────────────
    # Configuration
    # ─────────────────────────────────────────────────────────────────
    
    app.config.from_mapping(
        SECRET_KEY=settings.secret_key,
        SQLALCHEMY_DATABASE_URI=settings.database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=settings.sqlalchemy_track_modifications,
        SQLALCHEMY_ECHO=settings.sqlalchemy_echo,
        DEBUG=settings.debug,
    )
    
    # ─────────────────────────────────────────────────────────────────
    # Logging
    # ─────────────────────────────────────────────────────────────────
    
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # ─────────────────────────────────────────────────────────────────
    # Extensions
    # ─────────────────────────────────────────────────────────────────
    
    db.init_app(app)
    migrate.init_app(app, db)
    
    # CORS
    CORS(app, origins=settings.cors_origins)
    
    # Dependencies
    init_dependencies(app)
    
    # ─────────────────────────────────────────────────────────────────
    # Register Blueprints
    # ─────────────────────────────────────────────────────────────────
    
    
    # ─────────────────────────────────────────────────────────────────
    # Error Handlers
    # ─────────────────────────────────────────────────────────────────
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle HTTP exceptions."""
        response = {
            "error": error.name,
            "message": error.description,
            "status": error.code
        }
        return jsonify(response), error.code
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle unexpected exceptions."""
        app.logger.error(f"Unhandled exception: {error}", exc_info=True)
        
        # Don't reveal internal errors in production
        if settings.is_production:
            message = "An internal error occurred"
        else:
            message = str(error)
        
        response = {
            "error": "Internal Server Error",
            "message": message,
            "status": 500
        }
        return jsonify(response), 500
    
    # ─────────────────────────────────────────────────────────────────
    # Health Check Route
    # ─────────────────────────────────────────────────────────────────
    
    @app.route("/health")
    def health_check():
        """Health check endpoint."""
        return jsonify({
            "status": "healthy",
            "environment": settings.environment
        }), 200
    
    @app.route("/")
    def index():
        """Root endpoint."""
        return jsonify({
            "name": "Todo List API",
            "version": "1.0.0",
            "status": "running"
        }), 200
    
    return app