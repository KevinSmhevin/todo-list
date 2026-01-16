from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator

from todo_list.models import Todo, TodoStatus, TodoPriority

class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid", 
        from_attributes=True,
        str_strip_whitespace=True)

class TodoCreate(Schema):
    """Schema for creating a todo"""
    
    title: str = Field(..., max_length=64, description="title of todo")
    body: str | None = Field(default=None, description="details of todo")
    priority: TodoPriority = Field(default=TodoPriority.low, description="todo priority")
    due_date: datetime | None = Field(default=None, description="due date of todo")
    
    @field_validator('due_date')
    @classmethod
    def validate_timezone_aware(cls, v: datetime | None) -> datetime | None:
        if v is not None and v.tzinfo is None:
            raise ValueError('due_date must be timezone-aware')
        return v
    
    
class TodoUpdate(Schema):
    """Schema for updating a todo"""
    
    title: str | None = Field(default=None)
    body: str | None = Field(default=None)
    status: TodoStatus | None = Field(default=None)
    priority: TodoPriority | None = Field(default=None)
    due_date: datetime | None = Field(default=None)
    
class TodoResponse(Schema):
    """Schema for todo responses"""
    
    id: UUID
    title: str
    body: str | None
    status: TodoStatus
    priority: TodoPriority
    created_at: datetime
    updated_at: datetime
    due_date: datetime | None
    
class TodoListResponse(Schema):
    """Schema for paginated todos"""
    
    todos: list[TodoResponse]
    total: int
    page: int
    page_size: int
    
class SortBy(str, Enum):
    """Enum for sortable fields"""
    created_at = "created_at"
    updated_at = "updated_at"
    due_date = "due_date"
    priority = "priority"
    todo_title = "title"

class SortOrder(str, Enum):
    """Enum for sort order"""
    asc = "asc"
    desc = "desc"

class TodoListFilter(Schema):
    """Schema for filtering todos"""
    
    search: str | None = None
    priority: TodoPriority | None = None
    status: TodoStatus | None = None
    created_after: datetime | None = None
    created_before: datetime | None = None
    due_after: datetime | None = None
    due_before: datetime | None = None
    sort_by: SortBy = Field(default=SortBy.created_at)
    sort_order: SortOrder = Field(default=SortOrder.desc)
    
    @field_validator('created_after', 'created_before', 'due_after', 'due_before')
    @classmethod
    def validate_timezone_aware(cls, v: datetime | None) -> datetime | None:
        if v is not None and v.tzinfo is None:
            raise ValueError('datetime fields must be timezone-aware')
        return v

    