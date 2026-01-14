import uuid
import enum as py_enum
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    String,
    Text,
    Index,
    Enum as sqlEnum,
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class TodoStatus(str, py_enum.Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"
    
class TodoPriority(str, py_enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"

class Todo(Base):
    __tablename__ = "todos"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default = uuid.uuid4,
        unique=True,
        index=True,
        nullable=False,
    )
    
    title: Mapped[str] = mapped_column(String(64), index=True)
    
    body: Mapped[str] = mapped_column(Text, nullable=True)
    
    status: Mapped[TodoStatus] = mapped_column(
        sqlEnum(TodoStatus, name="todo_status"), 
        index=True, default=TodoStatus.not_started)
    
    priority: Mapped[TodoPriority] = mapped_column(
        sqlEnum(TodoPriority, name="todo_priority"), 
        index=True, default=TodoPriority.low)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True)
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    
    due_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    __table_args__ = (
        Index("ix_todos_status_created", "status", "created_at")
    )
    
    
    