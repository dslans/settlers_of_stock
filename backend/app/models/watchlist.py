"""
Watchlist models for tracking user's stock interests.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Numeric, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base

class Watchlist(Base):
    """Watchlist model for organizing stocks."""
    
    __tablename__ = "watchlists"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="watchlists")
    items = relationship("WatchlistItem", back_populates="watchlist", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Watchlist(id={self.id}, name='{self.name}', user_id={self.user_id})>"

class WatchlistItem(Base):
    """Individual stock items in a watchlist."""
    
    __tablename__ = "watchlist_items"
    
    id = Column(Integer, primary_key=True, index=True)
    watchlist_id = Column(Integer, ForeignKey("watchlists.id"), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    company_name = Column(String(255), nullable=True)
    
    # Optional user notes and target prices
    notes = Column(Text, nullable=True)
    target_price = Column(Numeric(10, 2), nullable=True)
    entry_price = Column(Numeric(10, 2), nullable=True)
    
    # Position tracking (optional)
    shares_owned = Column(Numeric(15, 4), nullable=True, default=0)
    
    # Timestamps
    added_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    watchlist = relationship("Watchlist", back_populates="items")
    
    def __repr__(self):
        return f"<WatchlistItem(id={self.id}, symbol='{self.symbol}', watchlist_id={self.watchlist_id})>"