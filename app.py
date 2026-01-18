# app.py
"""Entry point for running the Flask application."""

from todo_list import create_app
from todo_list.config import settings

app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=settings.debug
    )