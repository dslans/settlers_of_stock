"""
Educational content models for financial concepts and explanations.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from enum import Enum

from app.core.database import Base


class ConceptType(str, Enum):
    """Types of financial concepts"""
    TECHNICAL_INDICATOR = "technical_indicator"
    FUNDAMENTAL_RATIO = "fundamental_ratio"
    MARKET_CONCEPT = "market_concept"
    TRADING_STRATEGY = "trading_strategy"
    RISK_MANAGEMENT = "risk_management"


class DifficultyLevel(str, Enum):
    """Difficulty levels for educational content"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


# Association table for concept relationships
concept_relationships = Table(
    'concept_relationships',
    Base.metadata,
    Column('parent_id', Integer, ForeignKey('educational_concepts.id'), primary_key=True),
    Column('child_id', Integer, ForeignKey('educational_concepts.id'), primary_key=True)
)


class EducationalConcept(Base):
    """Educational concept database model"""
    __tablename__ = "educational_concepts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    concept_type = Column(String(50), nullable=False)
    difficulty_level = Column(String(20), nullable=False)
    short_description = Column(String(500), nullable=False)
    detailed_explanation = Column(Text, nullable=False)
    practical_example = Column(Text, nullable=True)
    formula = Column(String(200), nullable=True)
    interpretation_guide = Column(Text, nullable=True)
    common_mistakes = Column(Text, nullable=True)
    keywords = Column(String(500), nullable=True)  # Comma-separated keywords
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Self-referential many-to-many relationship for related concepts
    related_concepts = relationship(
        "EducationalConcept",
        secondary=concept_relationships,
        primaryjoin=id == concept_relationships.c.parent_id,
        secondaryjoin=id == concept_relationships.c.child_id,
        back_populates="related_concepts"
    )

    # One-to-many relationship with learning paths
    learning_paths = relationship("LearningPath", back_populates="concepts")


class LearningPath(Base):
    """Learning path database model"""
    __tablename__ = "learning_paths"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    difficulty_level = Column(String(20), nullable=False)
    estimated_duration_minutes = Column(Integer, nullable=False)
    concept_id = Column(Integer, ForeignKey("educational_concepts.id"))
    order_index = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship back to concept
    concepts = relationship("EducationalConcept", back_populates="learning_paths")


class UserLearningProgress(Base):
    """User learning progress tracking"""
    __tablename__ = "user_learning_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    concept_id = Column(Integer, ForeignKey("educational_concepts.id"), nullable=False)
    is_completed = Column(Boolean, default=False)
    completion_date = Column(DateTime, nullable=True)
    difficulty_rating = Column(Integer, nullable=True)  # 1-5 scale
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Pydantic models for API responses
class EducationalConceptBase(BaseModel):
    """Base educational concept schema"""
    name: str
    concept_type: ConceptType
    difficulty_level: DifficultyLevel
    short_description: str
    detailed_explanation: str
    practical_example: Optional[str] = None
    formula: Optional[str] = None
    interpretation_guide: Optional[str] = None
    common_mistakes: Optional[str] = None
    keywords: Optional[str] = None


class EducationalConceptCreate(EducationalConceptBase):
    """Schema for creating educational concepts"""
    pass


class EducationalConceptResponse(EducationalConceptBase):
    """Schema for educational concept responses"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    related_concepts: List['EducationalConceptSummary'] = []

    class Config:
        from_attributes = True


class EducationalConceptSummary(BaseModel):
    """Summary schema for related concepts"""
    id: int
    name: str
    concept_type: ConceptType
    difficulty_level: DifficultyLevel
    short_description: str

    class Config:
        from_attributes = True


class LearningPathBase(BaseModel):
    """Base learning path schema"""
    name: str
    description: str
    difficulty_level: DifficultyLevel
    estimated_duration_minutes: int


class LearningPathCreate(LearningPathBase):
    """Schema for creating learning paths"""
    concept_ids: List[int]


class LearningPathResponse(LearningPathBase):
    """Schema for learning path responses"""
    id: int
    concepts: List[EducationalConceptSummary] = []
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ConceptExplanationRequest(BaseModel):
    """Request schema for concept explanations"""
    concept_name: str
    context: Optional[str] = None  # Context like stock symbol, analysis type
    user_level: Optional[DifficultyLevel] = DifficultyLevel.BEGINNER


class ConceptExplanationResponse(BaseModel):
    """Response schema for concept explanations"""
    concept: EducationalConceptResponse
    contextual_explanation: str
    related_suggestions: List[EducationalConceptSummary] = []
    next_learning_steps: List[str] = []


class UserLearningProgressBase(BaseModel):
    """Base user learning progress schema"""
    concept_id: int
    is_completed: bool
    difficulty_rating: Optional[int] = None


class UserLearningProgressCreate(UserLearningProgressBase):
    """Schema for creating user learning progress"""
    pass


class UserLearningProgressResponse(UserLearningProgressBase):
    """Schema for user learning progress responses"""
    id: int
    user_id: int
    concept: EducationalConceptSummary
    completion_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True