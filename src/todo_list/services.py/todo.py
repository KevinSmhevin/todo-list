from typing import Any
from uuid import UUID
from sqlalchemy.orm import Session

from todo_list.models import Todo, TodoPriority, TodoStatus
from todo_list.models.todo import utcnow
from todo_list.schemas import TodoCreate, TodoUpdate, TodoListFilter
from todo_list.repositories.todo import TodoRepository


# Custom Exceptions
class TodoValidationError(Exception):
    """Raised when todo validation fails."""
    pass


class TodoNotFoundError(Exception):
    """Raised when todo is not found."""
    pass


class InvalidStatusTransitionError(TodoValidationError):
    """Raised when attempting an invalid status transition."""
    pass


class TodoService:
    """
    Orchestrates todo CRUD operations used by API layer
    """
    def __init__(self, session: Session):
        self.repository = TodoRepository(session)
    
    def get_todo(self, id: UUID) -> Todo | None:
        return self.repository.get_by_id(id)
    
    def create_todo(self, todo_create: TodoCreate) -> Todo:
        if todo_create.due_date and todo_create.due_date < utcnow():
            raise TodoValidationError("Cannot create todo with due date in the past")
        
        todo = self.repository.create(todo_create)
        self.repository.session.flush()  # Ensure ID is generated
        return todo
    
    def update_todo(self, todo_id: UUID, todo_update: TodoUpdate) -> Todo | None:
        """Update a todo with validated data."""
        todo = self.get_todo(todo_id)
        
        if todo is None:
            return None
        
        # Convert to dict, excluding unset values
        updates = todo_update.model_dump(exclude_unset=True)
        
        # Business rule: validate due date if being updated
        if 'due_date' in updates and updates['due_date'] is not None:
            if updates['due_date'] < utcnow():
                raise TodoValidationError("Cannot set due date in the past")
        
        # Explicitly set updated_at
        updates['updated_at'] = utcnow()
        
        updated_todo = self.repository.update(todo, updates)
        self.repository.session.flush()  # Ensure changes are flushed
        return updated_todo
    
    def delete_todo(self, todo_id: UUID) -> bool:
        todo = self.get_todo(todo_id)
        
        if todo is None:
            return False
        
        self.repository.delete(todo)
        return True
    
    def list_todos(self, filters: TodoListFilter) -> tuple[list[Todo], int]:
        return self.repository.list(filters)
    
    def get_by_status(self, status: TodoStatus) -> list[Todo]:
        return self.repository.get_by_status(status)
    
    def get_overdue(self) -> list[Todo]:
        return self.repository.get_overdue()
    
    def transition_status(self, todo_id: UUID, new_status: TodoStatus) -> Todo:
        """Transition a todo to a new status with validation."""
        todo = self.get_todo(todo_id)
        
        if todo is None:
            raise TodoNotFoundError(f"Todo with id {todo_id} not found")
        
        # Define valid status transitions
        valid_transitions = {
            TodoStatus.not_started: [TodoStatus.in_progress, TodoStatus.completed],
            TodoStatus.in_progress: [TodoStatus.completed, TodoStatus.not_started],
            TodoStatus.completed: [TodoStatus.not_started, TodoStatus.in_progress],
        }
        
        # Validate transition
        if new_status not in valid_transitions.get(todo.status, []):
            raise InvalidStatusTransitionError(
                f"Cannot transition from {todo.status.value} to {new_status.value}"
            )
        
        updates = {
            'status': new_status,
            'updated_at': utcnow()
        }
        
        updated_todo = self.repository.update(todo, updates)
        self.repository.session.flush()
        return updated_todo
    
    def update_priority(self, todo_id: UUID, new_priority: TodoPriority) -> Todo:
        """Update the priority of a todo."""
        todo = self.get_todo(todo_id)
        
        if todo is None:
            raise TodoNotFoundError(f"Todo with id {todo_id} not found")
        
        updates = {
            'priority': new_priority,
            'updated_at': utcnow()
        }
        
        updated_todo = self.repository.update(todo, updates)
        self.repository.session.flush()
        return updated_todo
    