"""
Chat models for conversation history and context management.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from ..core.database import Base

class MessageType(PyEnum):
    """Types of chat messages."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    ERROR = "error"

class MessageStatus(PyEnum):
    """Status of message processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ChatSession(Base):
    """Chat session model for organizing conversations."""
    
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Session metadata
    title = Column(String(255), nullable=True)  # Auto-generated or user-defined
    description = Column(Text, nullable=True)
    
    # Session state
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Context tracking
    primary_symbols = Column(JSON, nullable=True, default=[])  # Main stocks discussed
    analysis_types = Column(JSON, nullable=True, default=[])   # Types of analysis performed
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_message_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ChatSession(id={self.id}, user_id={self.user_id}, title='{self.title}')>"

class ChatMessage(Base):
    """Individual chat messages within a session."""
    
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False, index=True)
    
    # Message content
    message_type = Column(Enum(MessageType), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(Enum(MessageStatus), default=MessageStatus.COMPLETED, nullable=False)
    
    # Message metadata
    message_metadata = Column(JSON, nullable=True, default={})  # Store analysis results, charts, etc.
    
    # Context information
    symbols_mentioned = Column(JSON, nullable=True, default=[])  # Stocks mentioned in this message
    analysis_performed = Column(JSON, nullable=True, default=[]) # Analysis types in this message
    
    # Processing information
    processing_time_ms = Column(Integer, nullable=True)  # Time taken to generate response
    token_count = Column(Integer, nullable=True)         # Token count for AI responses
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, type='{self.message_type}', session_id={self.session_id})>"

class ChatContext(Base):
    """Persistent context storage for chat sessions."""
    
    __tablename__ = "chat_contexts"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False, index=True)
    
    # Context data
    context_key = Column(String(100), nullable=False, index=True)  # e.g., 'stock_analysis', 'user_preferences'
    context_data = Column(JSON, nullable=False)  # Serialized context information
    
    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<ChatContext(id={self.id}, session_id={self.session_id}, key='{self.context_key}')>"