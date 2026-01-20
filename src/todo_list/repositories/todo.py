from uuid import UUID

from sqlalchemy import select, or_, func
from sqlalchemy.orm import Session

from todo_list.models import Todo
from todo_list.schemas import TodoListFilter, SortBy, SortOrder


class TodoRepository:
    def __init__(self, session: Session):
        self.session = session
    # ─────────────────────────────────────────────────────────────────
    # Basic CRUD
    # ─────────────────────────────────────────────────────────────────

    def get_by_id(self, todo_id: UUID) -> Todo | None:
        return self.session.get(Todo, todo_id)

    def add(self, todo: Todo) -> None:
        self.session.add(todo)
        
    def delete(self, todo: Todo) -> None:
        self.session.delete(todo)
        
    def update(self, todo: Todo, updates: dict) -> Todo:
        for field, value in updates.items():
            setattr(todo, field, value)
        return todo
    
    def list(self, filters: TodoListFilter) -> tuple[list[Todo], int]:
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
            if filters.sort_order == SortOrder.desc:
                sort_column = sort_column.desc()
            stmt = stmt.order_by(sort_column)
            
            # Pagination using filters.offset and filters.limit
            stmt = stmt.offset(filters.offset).limit(filters.limit)
            
            # Execute
            todos = self.session.execute(stmt).scalars().all()
            
            return list(todos), total