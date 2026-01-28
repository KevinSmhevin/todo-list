from typing import Any
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.orm import Session

from src.todo_list.models import Todo, TodoPriority
from src.todo_list.schemas import TodoCreate
from src.todo_list.repositories.todo import TodoRepository

def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TodoService:
    """
    Orchestrates todo CRUD operations used by API layer
    """
    def __init__(self, session: Session):
        self.repository = TodoRepository(session)
    
    def get_todo(self, id: UUID) -> Todo | None:
        return self.repository.get_by_id(id)
    
    def create_todo(self, todo_create: TodoCreate) -> Todo:
        return self.repository.create(todo_create)
    
    def update_todo(self, todo_id: UUID, updates: dict[str, Any]) -> Todo | None:
        todo = self.get_todo(todo_id)
        
        if todo is None:
            return None
        
        return self.repository.update(todo, updates)
    
    def delete_todo(self, todo_id: UUID) -> bool:
        todo = self.get_todo(todo_id)
        
        if todo is None:
            return False
        
        self.repository.delete(todo)
        return True
    
    
        