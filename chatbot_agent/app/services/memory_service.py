from typing import Dict, List
from google.genai import types
from app.config import settings
from app.schemas.chat import SessionInfo


class MemoryService:
    """
    Manages in-memory conversation history per session_id (SOLID Single Responsibility Principle).
    Demonstrates Phase 2 of Project 1: context window sliding history without an external database.
    """

    def __init__(self, max_turns: int = settings.max_session_turns):
        # Structure: { session_id: [ {"role": "user"|"model", "text": str}, ... ] }
        self._store: Dict[str, List[Dict[str, str]]] = {}
        self.max_turns = max_turns

    def get_history_turns(self, session_id: str) -> List[Dict[str, str]]:
        """Returns raw turn dicts for a session."""
        return self._store.get(session_id, [])

    def get_gemini_contents(self, session_id: str, new_user_message: str) -> List[types.Content]:
        """
        Constructs the list of `types.Content` objects expected by the Gemini API,
        combining past conversation history with the incoming user message.
        """
        history = self._store.get(session_id, [])
        contents: List[types.Content] = []

        # Convert stored turns to Gemini Content objects
        for turn in history:
            contents.append(
                types.Content(
                    role=turn["role"],
                    parts=[types.Part(text=turn["text"])]
                )
            )

        # Append current user query
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part(text=new_user_message)]
            )
        )
        return contents

    def append_turn(self, session_id: str, user_message: str, model_reply: str) -> int:
        """
        Appends a new user-model turn to the session and enforces the max sliding window limit.
        Returns the updated total message count.
        """
        history = self._store.setdefault(session_id, [])
        history.append({"role": "user", "text": user_message})
        history.append({"role": "model", "text": model_reply})

        # Apply sliding window cap (MAX_TURNS pairs = 2 * MAX_TURNS messages)
        max_messages = self.max_turns * 2
        if len(history) > max_messages:
            self._store[session_id] = history[-max_messages:]

        return len(self._store[session_id])

    def clear_session(self, session_id: str) -> bool:
        """Clears all turns for a specific session (idempotent)."""
        if session_id in self._store:
            del self._store[session_id]
        return True

    def get_session_info(self, session_id: str) -> SessionInfo:
        """Returns summary info about a session."""
        msgs = self._store.get(session_id, [])
        return SessionInfo(
            session_id=session_id,
            message_count=len(msgs),
            max_turns=self.max_turns,
        )

    def list_sessions(self) -> List[SessionInfo]:
        """Lists all active sessions."""
        return [
            SessionInfo(session_id=sid, message_count=len(msgs), max_turns=self.max_turns)
            for sid, msgs in self._store.items()
        ]


# Singleton instance
memory_service = MemoryService()
