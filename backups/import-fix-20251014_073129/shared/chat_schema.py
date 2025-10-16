"""
VERITAS Chat Persistence Schema
===============================

Pydantic-Modelle für Chat-Sessions und Nachrichten.

Version: v3.20.0
Author: VERITAS Team
Date: 12. Oktober 2025
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4


class ChatMessage(BaseModel):
    """Einzelne Chat-Nachricht in einer Session"""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    """Eindeutige Message-ID"""
    
    role: str = Field(..., description="Rolle: 'user' oder 'assistant'")
    """Nachrichtenrolle"""
    
    content: str = Field(..., description="Nachrichteninhalt")
    """Textinhalt der Nachricht"""
    
    timestamp: datetime = Field(default_factory=datetime.now)
    """Zeitstempel der Nachricht"""
    
    attachments: List[str] = Field(default_factory=list)
    """Liste von Datei-Pfaden (für Drag & Drop)"""
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    """Zusätzliche Metadaten (z.B. confidence, sources, agents)"""
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChatSession(BaseModel):
    """Vollständige Chat-Session mit Metadaten"""
    
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    """Eindeutige Session-ID"""
    
    created_at: datetime = Field(default_factory=datetime.now)
    """Erstellungszeitpunkt"""
    
    updated_at: datetime = Field(default_factory=datetime.now)
    """Letztes Update"""
    
    title: str = Field(default="Neue Konversation")
    """Session-Titel (wird aus erster User-Message generiert)"""
    
    llm_model: str = Field(default="llama3.1:8b")
    """Verwendetes LLM-Modell"""
    
    messages: List[ChatMessage] = Field(default_factory=list)
    """Liste aller Nachrichten"""
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    """Session-Metadaten (z.B. tags, category, statistics)"""
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def add_message(self, role: str, content: str, 
                   attachments: List[str] = None, 
                   metadata: Dict[str, Any] = None):
        """Fügt neue Nachricht zur Session hinzu"""
        message = ChatMessage(
            role=role,
            content=content,
            attachments=attachments or [],
            metadata=metadata or {}
        )
        self.messages.append(message)
        self.updated_at = datetime.now()
        
        # Auto-generate title from first user message
        if role == "user" and self.title == "Neue Konversation":
            self.title = self._generate_title_from_message(content)
    
    def _generate_title_from_message(self, content: str, max_length: int = 50) -> str:
        """Generiert Session-Titel aus erster User-Message"""
        # Kürze langen Text
        title = content.strip()
        if len(title) > max_length:
            title = title[:max_length] + "..."
        
        # Entferne Zeilenumbrüche
        title = title.replace("\n", " ").replace("\r", "")
        
        return title
    
    def get_message_count(self) -> int:
        """Gibt Anzahl der Nachrichten zurück"""
        return len(self.messages)
    
    def get_last_message(self) -> Optional[ChatMessage]:
        """Gibt letzte Nachricht zurück"""
        return self.messages[-1] if self.messages else None
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert Session zu Dictionary (für JSON-Export)"""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "title": self.title,
            "llm_model": self.llm_model,
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "attachments": msg.attachments,
                    "metadata": msg.metadata
                }
                for msg in self.messages
            ],
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatSession":
        """Erstellt Session aus Dictionary (für JSON-Import)"""
        # Parse datetime strings
        created_at = datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
        updated_at = datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat()))
        
        # Parse messages
        messages = []
        for msg_data in data.get("messages", []):
            msg_timestamp = datetime.fromisoformat(msg_data.get("timestamp", datetime.now().isoformat()))
            messages.append(ChatMessage(
                id=msg_data.get("id", str(uuid4())),
                role=msg_data["role"],
                content=msg_data["content"],
                timestamp=msg_timestamp,
                attachments=msg_data.get("attachments", []),
                metadata=msg_data.get("metadata", {})
            ))
        
        # Create session
        return cls(
            session_id=data.get("session_id", str(uuid4())),
            created_at=created_at,
            updated_at=updated_at,
            title=data.get("title", "Neue Konversation"),
            llm_model=data.get("llm_model", "llama3.1:8b"),
            messages=messages,
            metadata=data.get("metadata", {})
        )


# Example Usage
if __name__ == "__main__":
    # Create new session
    session = ChatSession()
    
    # Add messages
    session.add_message("user", "Was ist das BImSchG?")
    session.add_message("assistant", "Das Bundes-Immissionsschutzgesetz (BImSchG)...", 
                       metadata={"confidence": 0.887, "sources": 8})
    
    # Export to dict
    session_dict = session.to_dict()
    print(f"Session: {session.title}")
    print(f"Messages: {session.get_message_count()}")
    print(f"Last update: {session.updated_at}")
    
    # Import from dict
    restored_session = ChatSession.from_dict(session_dict)
    print(f"Restored: {restored_session.title}")
