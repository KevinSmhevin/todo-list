from flask import Blueprint, request, jsonify
from uuid import UUID
from datetime import datetime
from pydantic import ValidationError

from todo_list.api.dependencies import transaction, get_db, get_repository
from todo_list.services import TodoService, TodoNotFoundError, TodoValidationError
from todo_list.schemas import TodoCreate, TodoUpdate, TodoResponse, TodoListFilter, TodoListResponse
from todo_list.models import TodoStatus, TodoPriority
from todo_list.repositories.todo import TodoRepository

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
        
        #filters
        
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
            
        #sorting
        
        if request.args.get('sort_by'):
            filter_data['sort_by'] = request.args.get('sort_by')
            
        if request.args.get('sort_order'):
            filter_data['sort_order'] = request.args.get('sort_order')
            
        #pagination
        
        if request.args.get('limit'):
            limit_value = request.args.get('limit')
            if limit_value:
                filter_data['limit'] = int(limit_value)
                
        if request.args.get('offset'):
            offset_value = request.args.get('offset')
            if offset_value:
                filter_data['offset'] = int(offset_value)
                
        #validate with pydantic scheme
        
        filters = TodoListFilter(**filter_data)
            
    except ValueError as e:
        return jsonify({
            "error": "Invalid Filter",
            "message": f"Invalid parameter value: {str(e)}"
        }), 400
        
    # Query with filters
        
    repo = get_repository(TodoRepository)
    todos, total = repo.list(filters)
    
    #Build response
    
    page = (filters.offset // filters.limit) + 1
    
    response = TodoListResponse(
        todos=[TodoResponse.model_validate(t) for t in todos],
        total=total,
        page=page,
        page_size=filters.limit
    )
    
    return jsonify(response.model_dump(mode='json')), 200


@todos_bp.route('', methods=['POST'])
def create_todo():
    """Create a new todo"""
    
    data = request.get_json()
    todo_create = TodoCreate(**data)
    
    with transaction() as session:
        service = TodoService(session)
        todo = service.create_todo(todo_create)
        
    return jsonify(TodoListResponse.model_validate(todo).model_dump(mode='json')), 201

@todos_bp.route('/<uuid:todo_id>', methods=['PATCH'])
def update_todo(todo_id: UUID):
    """Update a todo"""
    
    data = request.get_json()
    
    todo_update = TodoUpdate(**data)
    
    with transaction() as session:
        service = TodoService(session)
        
        todo = service.update_todo(todo_id, todo_update)
        
        if todo is None:
            return jsonify({"error": "Not Found", "message": "Todo not found"})
    
    return jsonify(TodoResponse.model_validate(todo).model_dump(mode='json')), 200


@todos_bp.route('/<uuid:todo_id>', methods=['DELETE'])
def delete_todo(todo_id: UUID):
    """Delete a todo"""
    
    with transaction() as session:
        service = TodoService(session)
        
        deleted = service.delete_todo(todo_id)
        
        if not deleted:
            return jsonify({"error": "Not Found", "message": "Todo not found"}), 404
        
    return '', 204
            
        