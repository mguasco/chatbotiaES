# models/chat_models.py
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class ChatMessage:
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class ChatSession:
    session_id: str
    messages: List[ChatMessage]
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class SearchResult:
    success: bool
    context: Optional[str]
    results_count: int = 0
    error: Optional[str] = None

@dataclass
class ChatResponse:
    response: str
    full_conversation: str
    error: Optional[str] = None
