"""Database dependency management for Flask-SQLAlchemy."""

from typing import Type, TypeVar
from sqlalchemy.orm import Session
from flask import Flask, g
from todo_list.extensions import db

T = TypeVar('T')


# ─────────────────────────────────────────────────────────────────
# Session Access
# ─────────────────────────────────────────────────────────────────

def get_db() -> Session:
    """
    Get database session for current request.
    
    Flask-SQLAlchemy automatically handles session lifecycle:
    - Creates session at start of request
    - Commits at end of successful request
    - Rolls back on exceptions
    - Cleans up after request completes
    
    Use this for direct database access when repository methods
    don't provide what you need.
    
    Usage:
        @app.route('/todos/<id>')
        def get_todo(id):
            session = get_db()
            todo = session.get(Todo, id)
            return todo.to_dict() if todo else {"error": "Not found"}, 404
    """
    return db.session


# ─────────────────────────────────────────────────────────────────
# Repository Injection (Recommended)
# ─────────────────────────────────────────────────────────────────

def get_repository(repo_class: Type[T]) -> T:
    """
    Get repository instance with Flask-SQLAlchemy session.
    
    Repositories are cached per request to avoid recreation.
    Flask-SQLAlchemy handles all transaction management automatically.
    
    This is the recommended pattern for most routes as it:
    - Keeps routes clean and focused on HTTP concerns
    - Encapsulates database logic in testable repositories
    - Leverages your existing repository layer
    
    Usage:
        from todo_list.repositories.todo import TodoRepository
        
        @app.route('/todos')
        def list_todos():
            repo = get_repository(TodoRepository)
            todos, total = repo.list(filters)
            return {"todos": [t.to_dict() for t in todos], "total": total}
    """
    cache_key = f'repo_{repo_class.__name__}'
    
    if cache_key not in g:
        g[cache_key] = repo_class(db.session)
    
    return g[cache_key]


# ─────────────────────────────────────────────────────────────────
# Initialization
# ─────────────────────────────────────────────────────────────────

def init_dependencies(app: Flask) -> None:
    """
    Initialize database dependency management with Flask app.
    
    Registers teardown handlers for proper cleanup.
    Call this from your create_app() factory.
    
    Usage:
        from todo_list.api.dependencies import init_dependencies
        
        def create_app():
            app = Flask(__name__)
            # ... configure app ...
            init_dependencies(app)
            return app
    """
    
    @app.teardown_appcontext
    def cleanup_repositories(exception=None):
        """
        Clean up request-scoped repository cache.
        
        Note: Flask-SQLAlchemy handles session cleanup automatically,
        but we clear our repository cache for good measure.
        """
        # Clear all cached repositories from Flask's g object
        repo_keys = [key for key in g.keys() if key.startswith('repo_')]
        for key in repo_keys:
            g.pop(key, None)