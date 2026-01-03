"""Input validation functions for Todo API."""
from typing import Optional, Tuple


VALID_STATUSES = {"pending", "in_progress", "completed"}
MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 1000


def validate_title(title: Optional[str]) -> Tuple[bool, Optional[str]]:
    """Validate todo title.

    Args:
        title: Title to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if title is None or title == "":
        return False, "Title is required"

    if not isinstance(title, str):
        return False, "Title must be a string"

    if len(title) > MAX_TITLE_LENGTH:
        return False, f"Title must not exceed {MAX_TITLE_LENGTH} characters"

    return True, None


def validate_description(description: Optional[str]) -> Tuple[bool, Optional[str]]:
    """Validate todo description.

    Args:
        description: Description to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if description is None or description == "":
        return True, None  # Description is optional

    if not isinstance(description, str):
        return False, "Description must be a string"

    if len(description) > MAX_DESCRIPTION_LENGTH:
        return False, f"Description must not exceed {MAX_DESCRIPTION_LENGTH} characters"

    return True, None


def validate_status(status: Optional[str]) -> Tuple[bool, Optional[str]]:
    """Validate todo status.

    Args:
        status: Status to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if status is None or status == "":
        return True, None  # Status is optional (defaults to pending)

    if not isinstance(status, str):
        return False, "Status must be a string"

    if status not in VALID_STATUSES:
        return False, f"Status must be one of: {', '.join(VALID_STATUSES)}"

    return True, None


def validate_todo_data(
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    require_title: bool = True
) -> Tuple[bool, list[str]]:
    """Validate all todo data fields.

    Args:
        title: Title to validate
        description: Description to validate
        status: Status to validate
        require_title: Whether title is required

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    if require_title:
        is_valid, error = validate_title(title)
        if not is_valid:
            errors.append(error)
    elif title is not None:
        is_valid, error = validate_title(title)
        if not is_valid:
            errors.append(error)

    if description is not None:
        is_valid, error = validate_description(description)
        if not is_valid:
            errors.append(error)

    if status is not None:
        is_valid, error = validate_status(status)
        if not is_valid:
            errors.append(error)

    return len(errors) == 0, errors
