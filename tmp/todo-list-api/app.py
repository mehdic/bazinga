"""Flask REST API for Todo List management."""
from flask import Flask, jsonify, request
from models import TodoStorage
from validators import validate_todo_data

app = Flask(__name__)
storage = TodoStorage()


@app.route('/todos', methods=['POST'])
def create_todo():
    """Create a new todo item.

    Request JSON:
        {
            "title": "string (required)",
            "description": "string (optional)",
            "status": "string (optional, default: pending)"
        }

    Returns:
        201: Created todo
        400: Validation error
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    title = data.get("title")
    description = data.get("description", "")
    status = data.get("status", "pending")

    # Validate input
    is_valid, errors = validate_todo_data(title, description, status)
    if not is_valid:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    # Create todo
    todo = storage.create(title, description, status)
    return jsonify(todo.to_dict()), 201


@app.route('/todos', methods=['GET'])
def list_todos():
    """List all todo items.

    Query parameters:
        status (optional): Filter by status

    Returns:
        200: List of todos
    """
    todos = storage.get_all()

    # Optional filtering by status
    status_filter = request.args.get('status')
    if status_filter:
        todos = [t for t in todos if t.status == status_filter]

    return jsonify([todo.to_dict() for todo in todos]), 200


@app.route('/todos/<int:todo_id>', methods=['GET'])
def get_todo(todo_id: int):
    """Get a specific todo by ID.

    Args:
        todo_id: Todo ID

    Returns:
        200: Todo item
        404: Todo not found
    """
    todo = storage.get(todo_id)

    if not todo:
        return jsonify({"error": f"Todo with ID {todo_id} not found"}), 404

    return jsonify(todo.to_dict()), 200


@app.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id: int):
    """Update a todo item.

    Args:
        todo_id: Todo ID

    Request JSON:
        {
            "title": "string (optional)",
            "description": "string (optional)",
            "status": "string (optional)"
        }

    Returns:
        200: Updated todo
        400: Validation error
        404: Todo not found
    """
    todo = storage.get(todo_id)

    if not todo:
        return jsonify({"error": f"Todo with ID {todo_id} not found"}), 404

    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    title = data.get("title")
    description = data.get("description")
    status = data.get("status")

    # Validate input (title not required for update)
    is_valid, errors = validate_todo_data(
        title, description, status, require_title=False
    )
    if not is_valid:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    # Update todo
    updated_todo = storage.update(todo_id, title, description, status)
    return jsonify(updated_todo.to_dict()), 200


@app.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id: int):
    """Delete a todo item.

    Args:
        todo_id: Todo ID

    Returns:
        204: Todo deleted
        404: Todo not found
    """
    success = storage.delete(todo_id)

    if not success:
        return jsonify({"error": f"Todo with ID {todo_id} not found"}), 404

    return '', 204


@app.route('/todos/<int:todo_id>/complete', methods=['PATCH'])
def mark_todo_complete(todo_id: int):
    """Mark a todo as completed.

    Args:
        todo_id: Todo ID

    Returns:
        200: Updated todo
        404: Todo not found
    """
    updated_todo = storage.mark_complete(todo_id)

    if not updated_todo:
        return jsonify({"error": f"Todo with ID {todo_id} not found"}), 404

    return jsonify(updated_todo.to_dict()), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
