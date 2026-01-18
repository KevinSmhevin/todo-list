# src/todo_list/extensions.py
"""Flask extensions initialization."""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize extensions without app context
db = SQLAlchemy()
migrate = Migrate()