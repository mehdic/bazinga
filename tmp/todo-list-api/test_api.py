"""Unit tests for Todo List API."""
import pytest
from app import app, storage


@pytest.fixture
def client():
    """Create test client and clean storage."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        storage.clear()
        yield client
        storage.clear()


class TestCreateTodo:
    """Tests for POST /todos endpoint."""

    def test_create_todo_success(self, client):
        """Test creating a todo with valid data."""
        response = client.post('/todos', json={
            "title": "Test Todo",
            "description": "Test Description",
            "status": "pending"
        })
        assert response.status_code == 201
        data = response.get_json()
        assert data["title"] == "Test Todo"
        assert data["description"] == "Test Description"
        assert data["status"] == "pending"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_todo_minimal(self, client):
        """Test creating a todo with only required fields."""
        response = client.post('/todos', json={
            "title": "Minimal Todo"
        })
        assert response.status_code == 201
        data = response.get_json()
        assert data["title"] == "Minimal Todo"
        assert data["description"] == ""
        assert data["status"] == "pending"

    def test_create_todo_missing_title(self, client):
        """Test creating a todo without title fails."""
        response = client.post('/todos', json={
            "description": "No title"
        })
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_create_todo_empty_title(self, client):
        """Test creating a todo with empty title fails."""
        response = client.post('/todos', json={
            "title": ""
        })
        assert response.status_code == 400

    def test_create_todo_title_too_long(self, client):
        """Test creating a todo with title exceeding max length fails."""
        response = client.post('/todos', json={
            "title": "x" * 201
        })
        assert response.status_code == 400
        data = response.get_json()
        assert "200 characters" in str(data)

    def test_create_todo_description_too_long(self, client):
        """Test creating a todo with description exceeding max length fails."""
        response = client.post('/todos', json={
            "title": "Valid Title",
            "description": "x" * 1001
        })
        assert response.status_code == 400
        data = response.get_json()
        assert "1000 characters" in str(data)

    def test_create_todo_invalid_status(self, client):
        """Test creating a todo with invalid status fails."""
        response = client.post('/todos', json={
            "title": "Valid Title",
            "status": "invalid_status"
        })
        assert response.status_code == 400
        data = response.get_json()
        assert "Status must be one of" in str(data)

    def test_create_todo_no_body(self, client):
        """Test creating a todo without request body fails."""
        response = client.post('/todos')
        # Flask returns 415 when Content-Type is not application/json
        assert response.status_code == 415


class TestListTodos:
    """Tests for GET /todos endpoint."""

    def test_list_todos_empty(self, client):
        """Test listing todos when none exist."""
        response = client.get('/todos')
        assert response.status_code == 200
        data = response.get_json()
        assert data == []

    def test_list_todos_multiple(self, client):
        """Test listing multiple todos."""
        client.post('/todos', json={"title": "Todo 1"})
        client.post('/todos', json={"title": "Todo 2"})
        client.post('/todos', json={"title": "Todo 3"})

        response = client.get('/todos')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 3

    def test_list_todos_filter_by_status(self, client):
        """Test filtering todos by status."""
        client.post('/todos', json={"title": "Todo 1", "status": "pending"})
        client.post('/todos', json={"title": "Todo 2", "status": "completed"})
        client.post('/todos', json={"title": "Todo 3", "status": "pending"})

        response = client.get('/todos?status=pending')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2
        assert all(todo["status"] == "pending" for todo in data)


class TestGetTodo:
    """Tests for GET /todos/<id> endpoint."""

    def test_get_todo_success(self, client):
        """Test getting a specific todo by ID."""
        create_response = client.post('/todos', json={"title": "Test Todo"})
        todo_id = create_response.get_json()["id"]

        response = client.get(f'/todos/{todo_id}')
        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == todo_id
        assert data["title"] == "Test Todo"

    def test_get_todo_not_found(self, client):
        """Test getting a non-existent todo returns 404."""
        response = client.get('/todos/999')
        assert response.status_code == 404
        data = response.get_json()
        assert "not found" in data["error"].lower()


class TestUpdateTodo:
    """Tests for PUT /todos/<id> endpoint."""

    def test_update_todo_title(self, client):
        """Test updating todo title."""
        create_response = client.post('/todos', json={"title": "Original Title"})
        todo_id = create_response.get_json()["id"]

        response = client.put(f'/todos/{todo_id}', json={
            "title": "Updated Title"
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data["title"] == "Updated Title"

    def test_update_todo_description(self, client):
        """Test updating todo description."""
        create_response = client.post('/todos', json={"title": "Test"})
        todo_id = create_response.get_json()["id"]

        response = client.put(f'/todos/{todo_id}', json={
            "description": "New Description"
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data["description"] == "New Description"

    def test_update_todo_status(self, client):
        """Test updating todo status."""
        create_response = client.post('/todos', json={"title": "Test"})
        todo_id = create_response.get_json()["id"]

        response = client.put(f'/todos/{todo_id}', json={
            "status": "in_progress"
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "in_progress"

    def test_update_todo_multiple_fields(self, client):
        """Test updating multiple fields at once."""
        create_response = client.post('/todos', json={"title": "Original"})
        todo_id = create_response.get_json()["id"]

        response = client.put(f'/todos/{todo_id}', json={
            "title": "Updated Title",
            "description": "Updated Description",
            "status": "completed"
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data["title"] == "Updated Title"
        assert data["description"] == "Updated Description"
        assert data["status"] == "completed"

    def test_update_todo_not_found(self, client):
        """Test updating non-existent todo returns 404."""
        response = client.put('/todos/999', json={"title": "Updated"})
        assert response.status_code == 404

    def test_update_todo_invalid_status(self, client):
        """Test updating with invalid status fails."""
        create_response = client.post('/todos', json={"title": "Test"})
        todo_id = create_response.get_json()["id"]

        response = client.put(f'/todos/{todo_id}', json={
            "status": "invalid"
        })
        assert response.status_code == 400

    def test_update_todo_no_body(self, client):
        """Test updating without request body fails."""
        create_response = client.post('/todos', json={"title": "Test"})
        todo_id = create_response.get_json()["id"]

        response = client.put(f'/todos/{todo_id}')
        # Flask returns 415 when Content-Type is not application/json
        assert response.status_code == 415


class TestDeleteTodo:
    """Tests for DELETE /todos/<id> endpoint."""

    def test_delete_todo_success(self, client):
        """Test deleting a todo successfully."""
        create_response = client.post('/todos', json={"title": "To Delete"})
        todo_id = create_response.get_json()["id"]

        response = client.delete(f'/todos/{todo_id}')
        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(f'/todos/{todo_id}')
        assert get_response.status_code == 404

    def test_delete_todo_not_found(self, client):
        """Test deleting non-existent todo returns 404."""
        response = client.delete('/todos/999')
        assert response.status_code == 404


class TestMarkComplete:
    """Tests for PATCH /todos/<id>/complete endpoint."""

    def test_mark_complete_success(self, client):
        """Test marking a todo as completed."""
        create_response = client.post('/todos', json={
            "title": "To Complete",
            "status": "pending"
        })
        todo_id = create_response.get_json()["id"]

        response = client.patch(f'/todos/{todo_id}/complete')
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "completed"

    def test_mark_complete_not_found(self, client):
        """Test marking non-existent todo as completed returns 404."""
        response = client.patch('/todos/999/complete')
        assert response.status_code == 404


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_todo_id_increments(self, client):
        """Test that todo IDs increment correctly."""
        response1 = client.post('/todos', json={"title": "First"})
        response2 = client.post('/todos', json={"title": "Second"})

        id1 = response1.get_json()["id"]
        id2 = response2.get_json()["id"]

        assert id2 == id1 + 1

    def test_updated_at_changes(self, client):
        """Test that updated_at changes on update."""
        create_response = client.post('/todos', json={"title": "Test"})
        todo_id = create_response.get_json()["id"]
        original_updated_at = create_response.get_json()["updated_at"]

        # Small delay to ensure timestamp differs
        import time
        time.sleep(0.01)

        update_response = client.put(f'/todos/{todo_id}', json={
            "title": "Updated"
        })
        new_updated_at = update_response.get_json()["updated_at"]

        assert new_updated_at > original_updated_at

    def test_invalid_endpoint(self, client):
        """Test accessing invalid endpoint returns 404."""
        response = client.get('/invalid')
        assert response.status_code == 404
