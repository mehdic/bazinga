"""
JSON file-based StateBackend implementation.

Provides persistence using JSON files instead of SQLite.
Useful for Copilot environments where SQLite may not be accessible.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

from bazinga.platform.interfaces import ReasoningData, SessionData, TaskGroupData
from bazinga.platform.state_backend.base import BaseStateBackend


class FileBackend(BaseStateBackend):
    """
    JSON file-based StateBackend for Copilot environments.

    Stores each session as a separate JSON file in the state directory.
    Thread-safe for parallel agent execution.

    File structure:
        base_dir/
            sessions/
                bazinga_xxx.json
            interactions/
                bazinga_xxx.json
            reasoning/
                bazinga_xxx.json

    Usage:
        backend = FileBackend(Path("bazinga/state"))
        backend.create_session(SessionData(...))
    """

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        """
        Initialize file-based backend.

        Args:
            base_dir: Base directory for state files. Defaults to bazinga/state.
        """
        self._base_dir = base_dir or Path.cwd() / "bazinga" / "state"
        self._lock = Lock()
        self._interaction_counter = 0
        self._reasoning_counter = 0

        # Ensure directories exist
        self._sessions_dir = self._base_dir / "sessions"
        self._interactions_dir = self._base_dir / "interactions"
        self._reasoning_dir = self._base_dir / "reasoning"

        for dir_path in [
            self._sessions_dir,
            self._interactions_dir,
            self._reasoning_dir,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def is_persistent(self) -> bool:
        """File backend provides persistence."""
        return True

    def supports_transactions(self) -> bool:
        """File backend does not support atomic transactions."""
        return False

    def _get_session_path(self, session_id: str) -> Path:
        """Get path to session file."""
        return self._sessions_dir / f"{session_id}.json"

    def _get_interactions_path(self, session_id: str) -> Path:
        """Get path to interactions file."""
        return self._interactions_dir / f"{session_id}.json"

    def _get_reasoning_path(self, session_id: str) -> Path:
        """Get path to reasoning file."""
        return self._reasoning_dir / f"{session_id}.json"

    def _read_json(self, path: Path) -> Optional[Dict[str, Any]]:
        """Read JSON file safely with thread lock."""
        with self._lock:
            if not path.exists():
                return None
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return None

    def _write_json(self, path: Path, data: Dict[str, Any]) -> None:
        """Write JSON file atomically."""
        temp_path = path.with_suffix(".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            temp_path.replace(path)
        except OSError:
            if temp_path.exists():
                temp_path.unlink()
            raise

    def create_session(self, data: SessionData) -> Dict[str, Any]:
        """
        Create a new session file.

        Args:
            data: Session data.

        Returns:
            Dict with creation result.
        """
        self._validate_session_id(data.session_id)

        with self._lock:
            session_path = self._get_session_path(data.session_id)
            if session_path.exists():
                return {
                    "success": False,
                    "error": f"Session {data.session_id} already exists",
                }

            now = datetime.now()
            session_dict = self._session_to_dict(data)
            session_dict["created_at"] = self._format_timestamp(now)
            session_dict["updated_at"] = self._format_timestamp(now)
            session_dict["task_groups"] = {}

            self._write_json(session_path, session_dict)

        return {"success": True, "session_id": data.session_id}

    def get_session(self, session_id: str) -> Optional[SessionData]:
        """
        Get a session by ID.

        Args:
            session_id: Session identifier.

        Returns:
            SessionData if found.
        """
        session_path = self._get_session_path(session_id)
        session_dict = self._read_json(session_path)
        if session_dict is None:
            return None
        return self._dict_to_session(session_dict)

    def update_session(
        self, session_id: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a session.

        Args:
            session_id: Session identifier.
            updates: Fields to update.

        Returns:
            Dict with update result.
        """
        with self._lock:
            session_path = self._get_session_path(session_id)
            session_dict = self._read_json(session_path)

            if session_dict is None:
                return {"success": False, "error": f"Session {session_id} not found"}

            session_dict.update(updates)
            session_dict["updated_at"] = self._format_timestamp()
            self._write_json(session_path, session_dict)

        return {"success": True, "session_id": session_id}

    def create_task_group(self, data: TaskGroupData) -> Dict[str, Any]:
        """
        Create a new task group.

        Args:
            data: Task group data.

        Returns:
            Dict with creation result.
        """
        self._validate_session_id(data.session_id)
        self._validate_group_id(data.group_id)

        with self._lock:
            session_path = self._get_session_path(data.session_id)
            session_dict = self._read_json(session_path)

            if session_dict is None:
                return {
                    "success": False,
                    "error": f"Session {data.session_id} not found",
                }

            if "task_groups" not in session_dict:
                session_dict["task_groups"] = {}

            if data.group_id in session_dict["task_groups"]:
                return {
                    "success": False,
                    "error": f"Task group {data.group_id} already exists",
                }

            now = datetime.now()
            group_dict = self._task_group_to_dict(data)
            group_dict["created_at"] = self._format_timestamp(now)
            group_dict["updated_at"] = self._format_timestamp(now)

            session_dict["task_groups"][data.group_id] = group_dict
            session_dict["updated_at"] = self._format_timestamp(now)
            self._write_json(session_path, session_dict)

        return {
            "success": True,
            "session_id": data.session_id,
            "group_id": data.group_id,
        }

    def get_task_groups(self, session_id: str) -> List[TaskGroupData]:
        """
        Get all task groups for a session.

        Args:
            session_id: Session identifier.

        Returns:
            List of TaskGroupData.
        """
        session_path = self._get_session_path(session_id)
        session_dict = self._read_json(session_path)

        if session_dict is None:
            return []

        groups = session_dict.get("task_groups", {})
        return [self._dict_to_task_group(g) for g in groups.values()]

    def update_task_group(
        self, session_id: str, group_id: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a task group.

        Args:
            session_id: Session identifier.
            group_id: Group identifier.
            updates: Fields to update.

        Returns:
            Dict with update result.
        """
        with self._lock:
            session_path = self._get_session_path(session_id)
            session_dict = self._read_json(session_path)

            if session_dict is None:
                return {"success": False, "error": f"Session {session_id} not found"}

            groups = session_dict.get("task_groups", {})
            if group_id not in groups:
                return {"success": False, "error": f"Group {group_id} not found"}

            groups[group_id].update(updates)
            groups[group_id]["updated_at"] = self._format_timestamp()
            session_dict["updated_at"] = self._format_timestamp()
            self._write_json(session_path, session_dict)

        return {"success": True, "session_id": session_id, "group_id": group_id}

    def log_interaction(
        self, session_id: str, agent_type: str, content: str, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Log an agent interaction.

        Args:
            session_id: Session identifier.
            agent_type: Type of agent.
            content: Interaction content.
            **kwargs: Additional metadata.

        Returns:
            Dict with log result.
        """
        with self._lock:
            interactions_path = self._get_interactions_path(session_id)
            interactions = self._read_json(interactions_path) or {"logs": []}

            self._interaction_counter += 1
            log_entry = {
                "id": self._interaction_counter,
                "session_id": session_id,
                "agent_type": agent_type,
                "content": content,
                "timestamp": self._format_timestamp(),
                **kwargs,
            }
            interactions["logs"].append(log_entry)
            self._write_json(interactions_path, interactions)

        return {"success": True, "log_id": self._interaction_counter}

    def save_reasoning(self, data: ReasoningData) -> Dict[str, Any]:
        """
        Save agent reasoning.

        Args:
            data: Reasoning data.

        Returns:
            Dict with save result.
        """
        with self._lock:
            reasoning_path = self._get_reasoning_path(data.session_id)
            reasoning = self._read_json(reasoning_path) or {"logs": []}

            self._reasoning_counter += 1
            reasoning_dict = self._reasoning_to_dict(data)
            reasoning_dict["id"] = self._reasoning_counter
            reasoning_dict["created_at"] = self._format_timestamp()
            reasoning["logs"].append(reasoning_dict)
            self._write_json(reasoning_path, reasoning)

        return {"success": True, "log_id": self._reasoning_counter}

    def get_reasoning(
        self,
        session_id: str,
        group_id: Optional[str] = None,
        agent_type: Optional[str] = None,
        phase: Optional[str] = None,
    ) -> List[ReasoningData]:
        """
        Get reasoning entries with filters.

        Args:
            session_id: Session identifier.
            group_id: Optional group filter.
            agent_type: Optional agent type filter.
            phase: Optional phase filter.

        Returns:
            List of matching ReasoningData.
        """
        reasoning_path = self._get_reasoning_path(session_id)
        reasoning = self._read_json(reasoning_path)

        if reasoning is None:
            return []

        results = []
        for r in reasoning.get("logs", []):
            if group_id and r.get("group_id") != group_id:
                continue
            if agent_type and r.get("agent_type") != agent_type:
                continue
            if phase and r.get("phase") != phase:
                continue
            results.append(self._dict_to_reasoning(r))

        return results

    def get_dashboard_snapshot(self, session_id: str) -> Dict[str, Any]:
        """
        Get dashboard snapshot for a session.

        Args:
            session_id: Session identifier.

        Returns:
            Dict with session state.
        """
        session_path = self._get_session_path(session_id)
        session_dict = self._read_json(session_path)

        if session_dict is None:
            return {"error": f"Session {session_id} not found"}

        interactions_path = self._get_interactions_path(session_id)
        interactions = self._read_json(interactions_path) or {"logs": []}

        reasoning_path = self._get_reasoning_path(session_id)
        reasoning = self._read_json(reasoning_path) or {"logs": []}

        task_groups = session_dict.pop("task_groups", {})

        return {
            "session": session_dict,
            "task_groups": list(task_groups.values()),
            "interactions": interactions.get("logs", []),
            "reasoning": reasoning.get("logs", []),
        }
