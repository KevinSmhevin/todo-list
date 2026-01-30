from flask import Blueprint, request, jsonify
from uuid import UUID
from datetime import datetime
from pydantic import ValidationError

from todo_list.api.dependencies import transaction, get_db
from todo_list.services import TodoService, TodoNotFoundError, TodoValidationError
from todo_list.schemas import TodoCreate, TodoUpdate, TodoResponse
from todo_list.models import TodoStatus, TodoPriority

todos_bp = Blueprint('todos', __name__, url_prefix='/api/v1/todos')

@todos_bp.route('/<uuid:todo_id>', methods=['GET'])
def get_todo(todo_id: UUID):
    """Get a single todo by ID."""
    session = get_db()
    service = TodoService(session)
    todo = service.get_todo(todo_id)
    
    if todo is None:
        return jsonify({"error": "Not Found", "message": "Todo not found"}), 404
    
    return jsonify(TodoResponse.model_validate(todo).model_dump(mode='json')), 200

@todos_bp.route('', methods=['GET'])
def list_todos():
    """
    List todos with optional filters.
    
    Query Parameters:
        - search: str - Search in title/body
        - status: str - Filter by status (not_started, in_progress, completed)
        - priority: str - Filter by priority (low, medium, high)
        - created_after: ISO datetime string
        - created_before: ISO datetime string
        - due_after: ISO datetime string
        - due_before: ISO datetime string
        - sort_by: str - Sort field (created_at, updated_at, due_date, priority)
        - sort_order: str - Sort direction (asc, desc)
        - limit: int - Items per page (1-100)
        - offset: int - Offset for pagination
    """
    
    try:
        # Build filter dict from query parameters
        filter_data = {}
        
        if request.args.get('search'):
            filter_data['search'] = request.args.get('search')
            
        if request.args.get('status'):
            filter_data['status'] = TodoStatus(request.args.get('status'))
            
        if request.args.get('priority'):
            filter_data['priority'] = TodoStatus(request.args.get('priority'))
            
        for date_field in ['created_after', 'created_before', 'due_after', 'due_before']:
            date_value = request.args.get(date_field)
            if date_value:
                filter_data[date_field] = datetime.fromisoformat(date_value)
            
    except ValueError as e:
        return jsonify({
            "error": "Invalid Filter",
            "message": f"Invalid parameter value: {str(e)}"
        }), 400


# class TodoListFilter(Schema):
#     """Schema for filtering todos"""
    
#     search: str | None = None
#     priority: TodoPriority | None = None
#     status: TodoStatus | None = None
#     created_after: datetime | None = None
#     created_before: datetime | None = None
#     due_after: datetime | None = None
#     due_before: datetime | None = None
#     sort_by: SortBy = Field(default=SortBy.created_at)
#     sort_order: SortOrder = Field(default=SortOrder.desc)
#     limit: int = Field(default=10, ge=1, le=100)
#     offset: int = Field(default=0, ge=0)