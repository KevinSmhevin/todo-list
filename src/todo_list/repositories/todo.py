"""Todo repository for database operations."""

from typing import Any
from uuid import UUID

from sqlalchemy import select, or_, func
from sqlalchemy.orm import Session

from todo_list.models import Todo, TodoStatus
from todo_list.schemas import TodoCreate, TodoListFilter


class TodoRepository:
    """Repository for Todo model database operations."""
    
    def __init__(self, session: Session):
        self.session = session
    # ─────────────────────────────────────────────────────────────────
    # Basic CRUD
    # ─────────────────────────────────────────────────────────────────
    
    def create(self, todo_data: TodoCreate) -> Todo:
        """Create a new todo from schema data."""
        todo = Todo(**todo_data.model_dump(exclude_unset=True))
        self.session.add(todo)
        return todo
    
    def get_by_id(self, todo_id: UUID) -> Todo | None:
        """Get a todo by its ID."""
        return self.session.get(Todo, todo_id)
    
    def update(self, todo: Todo, updates: dict[str, Any]) -> Todo:
        """Update a todo with provided fields."""
        for field, value in updates.items():
            if hasattr(todo, field):
                setattr(todo, field, value)
        return todo
    
    def delete(self, todo: Todo) -> None:
        """Delete a todo."""
        self.session.delete(todo)
    
    # ─────────────────────────────────────────────────────────────────
    # Query Methods
    # ─────────────────────────────────────────────────────────────────
    
    def list(self, filters: TodoListFilter) -> tuple[list[Todo], int]:
        """List todos with filtering, sorting, and pagination."""
        stmt = select(Todo)
        
        # Text search
        if filters.search is not None:
            search_filter = f"%{filters.search}%"
            
            stmt = stmt.where(
                or_(
                    Todo.title.ilike(search_filter),
                    Todo.body.ilike(search_filter)
                )
            )
        
        # Filters
        if filters.priority is not None:
            stmt = stmt.where(Todo.priority == filters.priority)
            
        if filters.status is not None:
            stmt = stmt.where(Todo.status == filters.status)
            
        if filters.created_after is not None:
            stmt = stmt.where(Todo.created_at >= filters.created_after)
            
        if filters.created_before is not None:
            stmt = stmt.where(Todo.created_at <= filters.created_before)
            
        if filters.due_after is not None:
            stmt = stmt.where(Todo.due_date >= filters.due_after)
            
        if filters.due_before is not None:
            stmt = stmt.where(Todo.due_date <= filters.due_before)
        
        # Count total before pagination
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.session.execute(count_stmt).scalar() or 0
            
        # Sorting
        sort_column = getattr(Todo, filters.sort_by.value)
        if filters.sort_order.value == "desc":
            sort_column = sort_column.desc()
        stmt = stmt.order_by(sort_column)
        
        # Pagination
        stmt = stmt.offset(filters.offset).limit(filters.limit)
        
        # Execute
        todos = self.session.execute(stmt).scalars().all()
        
        return list(todos), total
    
    def get_by_status(self, status: TodoStatus) -> list[Todo]:
        """Get all todos with a specific status."""
        stmt = select(Todo).where(Todo.status == status)
        return list(self.session.execute(stmt).scalars().all())
    
    def get_overdue(self) -> list[Todo]:
        """Get all overdue todos that are not completed."""
        from datetime import datetime, timezone
        
        now = datetime.now(timezone.utc)
        stmt = (
            select(Todo)
            .where(
                Todo.due_date < now,
                Todo.status != TodoStatus.completed
            )
            .order_by(Todo.due_date.asc())
        )
        return list(self.session.execute(stmt).scalars().all())