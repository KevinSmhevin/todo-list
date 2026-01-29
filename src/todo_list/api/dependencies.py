"""Database dependency management for Flask-SQLAlchemy 3.x."""

from contextlib import contextmanager
from typing import Type, TypeVar, Generator
from sqlalchemy.orm import Session
from flask import Flask, g
from todo_list.extensions import db

T = TypeVar('T')


# ─────────────────────────────────────────────────────────────────
# Pattern 1: Direct Session Access
# ─────────────────────────────────────────────────────────────────

def get_db() -> Session:
    """
    Get database session for current request.
    
    Flask-SQLAlchemy 3.x session lifecycle:
    - ✅ Creates session at start of request (app context)
    - ✅ Cleans up session after request completes
    - ❌ Does NOT auto-commit (you must call db.session.commit())
    - ✅ Auto-rollback on exceptions (if commit wasn't called)
    
    Use this for direct database access when repository methods
    don't provide what you need. Remember to commit!
    
    Usage:
        @app.route('/todos/<id>')
        def get_todo(id):
            session = get_db()
            todo = session.get(Todo, id)
            # No commit needed for read operations
            return todo.to_dict() if todo else {"error": "Not found"}, 404
    """
    return db.session


# ─────────────────────────────────────────────────────────────────
# Pattern 2: Repository Injection (Recommended)
# ─────────────────────────────────────────────────────────────────

def get_repository(repo_class: Type[T]) -> T:
    """
    Get repository instance with Flask-SQLAlchemy session.
    
    Repositories are cached per request to avoid recreation.
    You must still call db.session.commit() after repository operations.
    
    This is the recommended pattern for most routes as it:
    - Keeps routes clean and focused on HTTP concerns
    - Encapsulates database logic in testable repositories
    - Leverages your existing repository layer
    
    Usage:
        from todo_list.repositories.todo import TodoRepository
        
        @app.route('/todos', methods=['POST'])
        def create_todo():
            repo = get_repository(TodoRepository)
            todo = repo.create(todo_data)
            db.session.commit()  # Required!
            return {"id": str(todo.id)}, 201
    """
    cache_key = f'repo_{repo_class.__name__}'
    
    if not hasattr(g, cache_key):
        g[cache_key] = repo_class(db.session)
    
    return g[cache_key]


# ─────────────────────────────────────────────────────────────────
# Pattern 3: Managed Transaction Context (Best for Routes)
# ─────────────────────────────────────────────────────────────────

@contextmanager
def transaction() -> Generator[Session, None, None]:
    """
    Provide a managed transaction context for route handlers.
    
    Automatically commits on success or rolls back on exception.
    This is the cleanest pattern for route handlers as it eliminates
    the need to manually call commit() and handles errors properly.
    
    Usage:
        @app.route('/todos', methods=['POST'])
        def create_todo():
            with transaction() as session:
                repo = TodoRepository(session)
                todo = repo.create(todo_data)
                # Auto-commits on success, auto-rollback on exception
            return {"id": str(todo.id)}, 201
        
        # Or with get_repository:
        @app.route('/todos', methods=['POST'])
        def create_todo():
            with transaction():
                repo = get_repository(TodoRepository)
                todo = repo.create(todo_data)
            return {"id": str(todo.id)}, 201
    """
    try:
        yield db.session
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


# ─────────────────────────────────────────────────────────────────
# Initialization
# ─────────────────────────────────────────────────────────────────

def init_dependencies(app: Flask) -> None:
    """
    Initialize database dependency management with Flask app.
    
    Note: Flask-SQLAlchemy 3.x automatically handles:
    - Session lifecycle (creation, cleanup, removal)
    - Rollback on exceptions
    - Clearing request context (including g object)
    
    This function is provided for future extensibility, but currently
    no additional setup is required beyond Flask-SQLAlchemy's init_app().
    
    Usage:
        from todo_list.api.dependencies import init_dependencies
        
        def create_app():
            app = Flask(__name__)
            # ... configure app ...
            init_dependencies(app)
            return app
    """
    # Flask-SQLAlchemy handles all cleanup automatically
    # This function can be used to add custom teardown logic if needed
    pass