"""Todo data model and in-memory storage."""
from datetime import datetime
from typing import Dict, Optional


class Todo:
    """Todo item model."""

    def __init__(
        self,
        todo_id: int,
        title: str,
        description: str = "",
        status: str = "pending"
    ):
        """Initialize a Todo item.

        Args:
            todo_id: Unique identifier
            title: Todo title (required)
            description: Todo description (optional)
            status: Todo status (pending, in_progress, completed)
        """
        self.id = todo_id
        self.title = title
        self.description = description
        self.status = status
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert Todo to dictionary representation.

        Returns:
            Dictionary with all Todo fields
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    def update(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None
    ) -> None:
        """Update Todo fields.

        Args:
            title: New title (if provided)
            description: New description (if provided)
            status: New status (if provided)
        """
        if title is not None:
            self.title = title
        if description is not None:
            self.description = description
        if status is not None:
            self.status = status
        self.updated_at = datetime.utcnow()


class TodoStorage:
    """In-memory storage for Todo items."""

    def __init__(self):
        """Initialize empty storage."""
        self._todos: Dict[int, Todo] = {}
        self._next_id: int = 1

    def create(self, title: str, description: str = "", status: str = "pending") -> Todo:
        """Create a new Todo item.

        Args:
            title: Todo title
            description: Todo description
            status: Todo status

        Returns:
            Created Todo instance
        """
        todo = Todo(self._next_id, title, description, status)
        self._todos[self._next_id] = todo
        self._next_id += 1
        return todo

    def get(self, todo_id: int) -> Optional[Todo]:
        """Get a Todo by ID.

        Args:
            todo_id: Todo ID

        Returns:
            Todo instance or None if not found
        """
        return self._todos.get(todo_id)

    def get_all(self) -> list[Todo]:
        """Get all Todo items.

        Returns:
            List of all Todos
        """
        return list(self._todos.values())

    def update(
        self,
        todo_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None
    ) -> Optional[Todo]:
        """Update a Todo by ID.

        Args:
            todo_id: Todo ID
            title: New title
            description: New description
            status: New status

        Returns:
            Updated Todo or None if not found
        """
        todo = self._todos.get(todo_id)
        if todo:
            todo.update(title, description, status)
        return todo

    def delete(self, todo_id: int) -> bool:
        """Delete a Todo by ID.

        Args:
            todo_id: Todo ID

        Returns:
            True if deleted, False if not found
        """
        if todo_id in self._todos:
            del self._todos[todo_id]
            return True
        return False

    def mark_complete(self, todo_id: int) -> Optional[Todo]:
        """Mark a Todo as completed.

        Args:
            todo_id: Todo ID

        Returns:
            Updated Todo or None if not found
        """
        return self.update(todo_id, status="completed")

    def clear(self) -> None:
        """Clear all todos (useful for testing)."""
        self._todos.clear()
        self._next_id = 1
