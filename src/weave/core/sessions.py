"""Conversation session persistence for Weave.

Manages conversation history storage and retrieval.
"""

import os
import time
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class ConversationMessage:
    """A single message in a conversation."""

    role: str  # system, user, assistant, tool
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationMessage":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class ConversationSession:
    """A conversation session with multiple messages."""

    session_id: str
    weave_name: Optional[str] = None
    agent_name: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    messages: List[ConversationMessage] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a message to the session."""
        msg = ConversationMessage(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(msg)
        self.updated_at = time.time()

    def get_messages_for_llm(self) -> List[Dict[str, str]]:
        """Get messages in LLM API format (role + content)."""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.messages
            if msg.role in ["system", "user", "assistant"]
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "weave_name": self.weave_name,
            "agent_name": self.agent_name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "messages": [msg.to_dict() for msg in self.messages],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationSession":
        """Create from dictionary."""
        messages = [ConversationMessage.from_dict(m) for m in data.get("messages", [])]
        return cls(
            session_id=data["session_id"],
            weave_name=data.get("weave_name"),
            agent_name=data.get("agent_name"),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            messages=messages,
            metadata=data.get("metadata", {}),
        )


class SessionManager:
    """Manage conversation session storage and retrieval."""

    def __init__(self, sessions_dir: Optional[Path] = None):
        """Initialize session manager.

        Args:
            sessions_dir: Directory to store sessions (default: ~/.weave/sessions)
        """
        self.sessions_dir = sessions_dir or Path.home() / ".weave" / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        # Secure the sessions directory
        os.chmod(self.sessions_dir, 0o700)

    def save_session(self, session: ConversationSession) -> None:
        """Save a conversation session.

        Args:
            session: Session to save
        """
        session_file = self.sessions_dir / f"{session.session_id}.yaml"

        with open(session_file, "w") as f:
            yaml.safe_dump(session.to_dict(), f, default_flow_style=False)

        # Secure the session file
        os.chmod(session_file, 0o600)

    def load_session(self, session_id: str) -> Optional[ConversationSession]:
        """Load a conversation session.

        Args:
            session_id: Session ID to load

        Returns:
            Session or None if not found
        """
        session_file = self.sessions_dir / f"{session_id}.yaml"

        if not session_file.exists():
            return None

        try:
            with open(session_file) as f:
                data = yaml.safe_load(f)
                return ConversationSession.from_dict(data)
        except Exception:
            return None

    def list_sessions(
        self,
        weave_name: Optional[str] = None,
        agent_name: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[ConversationSession]:
        """List conversation sessions.

        Args:
            weave_name: Filter by weave name
            agent_name: Filter by agent name
            limit: Maximum number of sessions to return

        Returns:
            List of sessions, sorted by most recent first
        """
        sessions = []

        for session_file in self.sessions_dir.glob("*.yaml"):
            try:
                with open(session_file) as f:
                    data = yaml.safe_load(f)
                    session = ConversationSession.from_dict(data)

                    # Apply filters
                    if weave_name and session.weave_name != weave_name:
                        continue
                    if agent_name and session.agent_name != agent_name:
                        continue

                    sessions.append(session)
            except Exception:
                continue

        # Sort by most recent first
        sessions.sort(key=lambda s: s.updated_at, reverse=True)

        # Apply limit
        if limit:
            sessions = sessions[:limit]

        return sessions

    def delete_session(self, session_id: str) -> bool:
        """Delete a conversation session.

        Args:
            session_id: Session ID to delete

        Returns:
            True if deleted, False if not found
        """
        session_file = self.sessions_dir / f"{session_id}.yaml"

        if session_file.exists():
            session_file.unlink()
            return True

        return False

    def create_session(
        self,
        session_id: str,
        weave_name: Optional[str] = None,
        agent_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationSession:
        """Create a new conversation session.

        Args:
            session_id: Unique session ID
            weave_name: Name of the weave
            agent_name: Name of the agent
            metadata: Additional metadata

        Returns:
            New session
        """
        session = ConversationSession(
            session_id=session_id,
            weave_name=weave_name,
            agent_name=agent_name,
            metadata=metadata or {},
        )

        self.save_session(session)
        return session

    def cleanup_old_sessions(self, retention_days: int = 30) -> int:
        """Clean up old sessions.

        Args:
            retention_days: Number of days to retain sessions

        Returns:
            Number of sessions deleted
        """
        cutoff_time = time.time() - (retention_days * 24 * 60 * 60)
        deleted = 0

        for session_file in self.sessions_dir.glob("*.yaml"):
            try:
                with open(session_file) as f:
                    data = yaml.safe_load(f)
                    updated_at = data.get("updated_at", 0)

                    if updated_at < cutoff_time:
                        session_file.unlink()
                        deleted += 1
            except Exception:
                continue

        return deleted


# Global instance
_session_manager = None


def get_session_manager() -> SessionManager:
    """Get global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
