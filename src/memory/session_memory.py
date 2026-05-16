from typing import Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path
import uuid
from ..logger import get_logger

logger = get_logger(__name__)

class SessionMemory:
    """
    In-memory conversation store. 
    In production this can be replaced with Redis, PostgreSQL, or MongoDB.
    """
    def __init__(self, max_history: int = 10): #previous 10 chat messages, thiswill increase context window size
        self._store: Dict[str, List[Dict]] = {} #this will act as the production-grade MongoDB or PostgreSQL
        self.max_history = max_history
    
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Add a message to conversation history."""
        if session_id not in self._store:
            self._store[session_id] = [] #create new session id
        self._store[session_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "uuid": uuid.uuid4()
        })
        # Trim to max_history (keep last N exchanges)
        max_messages = self.max_history * 2  # user + assistant per exchange
        if len(self._store[session_id]) > max_messages:
            self._store[session_id] = self._store[session_id][-max_messages:]
    
    def get_history(self, session_id: str) -> List[Dict]:
        """Return full conversation history."""
        return self._store.get(session_id, [])
    
    def get_last_n_messages(self, session_id: str, n: int = 4) -> List[Dict]:
        """Return last n messages for context injection."""
        history = self.get_history(session_id)
        return history[-n:] if history else []
    
    def clear_session(self, session_id: str) -> None:
        """Clear all messages for a session."""
        if session_id in self._store:
            del self._store[session_id]
    
    def save_to_file(self, filepath: str = "conversations.json") -> None:
        """Persist all conversations to disk (for development)."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self._store, f, indent=2, ensure_ascii=False)
    
    def load_from_file(self, filepath: str = "conversations.json") -> None:
        """Load conversations from disk."""
        if Path(filepath).exists():
            with open(filepath, "r", encoding="utf-8") as f:
                self._store = json.load(f)

# Global instance
memory = SessionMemory(max_history=10)