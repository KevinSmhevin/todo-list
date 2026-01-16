from uuid import UUID

from sqlalchemy.orm import Session

from todo_list.models import Todo

class TodoRepository:

    @staticmethod
    def get_by_id(session: Session, todo_id: UUID) -> Todo | None:
        return session.get(Todo, todo_id)
    
    