"""
Educational content API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.education import (
    ConceptType, DifficultyLevel,
    EducationalConceptResponse, ConceptExplanationRequest, ConceptExplanationResponse,
    LearningPathResponse, UserLearningProgressResponse
)
from app.services.education_service import EducationService
from app.services.vertex_ai_service import VertexAIService

router = APIRouter(prefix="/education", tags=["education"])


def get_education_service(db: Session = Depends(get_db)) -> EducationService:
    """Get education service instance"""
    vertex_ai_service = VertexAIService()
    return EducationService(db, vertex_ai_service)


@router.get("/concepts/search", response_model=List[EducationalConceptResponse])
async def search_concepts(
    query: str = Query(..., description="Search query for concepts"),
    concept_type: Optional[ConceptType] = Query(None, description="Filter by concept type"),
    difficulty_level: Optional[DifficultyLevel] = Query(None, description="Filter by difficulty level"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    education_service: EducationService = Depends(get_education_service)
):
    """Search educational concepts"""
    try:
        concepts = await education_service.search_concepts(
            query=query,
            concept_type=concept_type,
            difficulty_level=difficulty_level,
            limit=limit
        )
        return concepts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching concepts: {str(e)}")


@router.get("/concepts/{concept_name}", response_model=EducationalConceptResponse)
async def get_concept(
    concept_name: str,
    education_service: EducationService = Depends(get_education_service)
):
    """Get educational concept by name"""
    try:
        concept = await education_service.get_concept_by_name(concept_name)
        if not concept:
            raise HTTPException(status_code=404, detail="Concept not found")
        return concept
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving concept: {str(e)}")


@router.post("/explain", response_model=ConceptExplanationResponse)
async def explain_concept(
    request: ConceptExplanationRequest,
    education_service: EducationService = Depends(get_education_service)
):
    """Get contextual explanation for a concept"""
    try:
        explanation = await education_service.get_contextual_explanation(
            concept_name=request.concept_name,
            context=request.context,
            user_level=request.user_level or DifficultyLevel.BEGINNER
        )
        
        if not explanation:
            raise HTTPException(status_code=404, detail="Concept not found")
        
        return explanation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating explanation: {str(e)}")


@router.post("/extract-concepts")
async def extract_concepts_from_text(
    text: str,
    education_service: EducationService = Depends(get_education_service)
):
    """Extract financial concepts mentioned in text"""
    try:
        concepts = await education_service.extract_concepts_from_text(text)
        return {"concepts": concepts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting concepts: {str(e)}")


@router.get("/learning-paths/suggestions")
async def get_learning_path_suggestions(
    user_level: DifficultyLevel = Query(DifficultyLevel.BEGINNER, description="User's experience level"),
    interests: Optional[List[ConceptType]] = Query(None, description="Areas of interest"),
    education_service: EducationService = Depends(get_education_service)
):
    """Get learning path suggestions"""
    try:
        suggestions = await education_service.get_learning_path_suggestions(
            user_level=user_level,
            interests=interests
        )
        return {"suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting suggestions: {str(e)}")


@router.post("/progress/{concept_id}")
async def track_learning_progress(
    concept_id: int,
    completed: bool = True,
    difficulty_rating: Optional[int] = Query(None, ge=1, le=5, description="Difficulty rating 1-5"),
    current_user: User = Depends(get_current_user),
    education_service: EducationService = Depends(get_education_service)
):
    """Track user's learning progress for a concept"""
    try:
        progress = await education_service.track_user_progress(
            user_id=current_user.id,
            concept_id=concept_id,
            completed=completed,
            difficulty_rating=difficulty_rating
        )
        return progress
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tracking progress: {str(e)}")


@router.get("/progress", response_model=List[UserLearningProgressResponse])
async def get_user_progress(
    current_user: User = Depends(get_current_user),
    education_service: EducationService = Depends(get_education_service)
):
    """Get user's learning progress"""
    try:
        progress = await education_service.get_user_progress(current_user.id)
        return progress
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving progress: {str(e)}")


@router.get("/concepts/types", response_model=List[str])
async def get_concept_types():
    """Get available concept types"""
    return [concept_type.value for concept_type in ConceptType]


@router.get("/difficulty-levels", response_model=List[str])
async def get_difficulty_levels():
    """Get available difficulty levels"""
    return [level.value for level in DifficultyLevel]