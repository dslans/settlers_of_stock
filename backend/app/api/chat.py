"""
Chat API endpoints for conversational stock analysis.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from app.services.chat_service import ChatService, ChatMessage, ChatResponse, UserPreferences
from app.services.vertex_ai_service import AnalysisResult
from app.core.dependencies import get_current_user
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize chat service
import os

def get_chat_service(db: Session = Depends(get_db)):
    """Get chat service instance with database session"""
    testing_mode = os.getenv("TESTING_MODE", "false").lower() == "true"
    return ChatService(testing_mode=testing_mode, db_session=db)

# Request/Response models
class ChatRequest(BaseModel):
    """Request model for chat messages"""
    message: str
    analysis_data: Optional[Dict[str, Any]] = None

class ChatHistoryResponse(BaseModel):
    """Response model for chat history"""
    messages: List[ChatMessage]
    total_count: int

class UserPreferencesRequest(BaseModel):
    """Request model for updating user preferences"""
    risk_tolerance: Optional[str] = None
    investment_horizon: Optional[str] = None
    preferred_analysis: Optional[List[str]] = None
    notification_settings: Optional[Dict[str, bool]] = None

@router.post("/chat", response_model=ChatResponse)
async def send_chat_message(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Send a chat message and get AI-powered response
    
    Args:
        request: Chat message request with optional analysis data
        current_user: Current authenticated user
        
    Returns:
        ChatResponse with AI-generated message and suggestions
    """
    try:
        user_id = current_user["sub"]  # User ID from JWT token
        
        # Convert analysis data to AnalysisResult if provided
        analysis_result = None
        if request.analysis_data:
            try:
                analysis_result = AnalysisResult(**request.analysis_data)
            except Exception as e:
                logger.warning(f"Invalid analysis data format: {e}")
                # Continue without analysis data
        
        # Process the message
        response = await chat_service.process_message(
            user_id=user_id,
            message=request.message,
            analysis_result=analysis_result
        )
        
        logger.info(f"Processed chat message for user {user_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat message"
        )

@router.get("/chat/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Get chat history for the current user
    
    Args:
        limit: Maximum number of messages to return
        current_user: Current authenticated user
        
    Returns:
        ChatHistoryResponse with recent messages
    """
    try:
        user_id = current_user["sub"]
        
        # Get chat history
        messages = await chat_service.get_chat_history(user_id, limit)
        
        return ChatHistoryResponse(
            messages=messages,
            total_count=len(messages)
        )
        
    except Exception as e:
        logger.error(f"Error retrieving chat history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat history"
        )

@router.delete("/chat/history")
async def clear_chat_history(
    current_user: dict = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Clear chat history and conversation context for the current user
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    try:
        user_id = current_user["sub"]
        
        # Clear conversation
        await chat_service.clear_conversation(user_id)
        
        return {"message": "Chat history cleared successfully"}
        
    except Exception as e:
        logger.error(f"Error clearing chat history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear chat history"
        )

@router.get("/chat/preferences", response_model=UserPreferences)
async def get_user_preferences(
    current_user: dict = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Get user preferences for personalized responses
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        UserPreferences object
    """
    try:
        user_id = current_user["sub"]
        
        preferences = await chat_service.get_user_preferences(user_id)
        return preferences
        
    except Exception as e:
        logger.error(f"Error retrieving user preferences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user preferences"
        )

@router.put("/chat/preferences", response_model=UserPreferences)
async def update_user_preferences(
    request: UserPreferencesRequest,
    current_user: dict = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Update user preferences for personalized responses
    
    Args:
        request: Updated preference values
        current_user: Current authenticated user
        
    Returns:
        Updated UserPreferences object
    """
    try:
        user_id = current_user["sub"]
        
        # Get current preferences
        current_prefs = await chat_service.get_user_preferences(user_id)
        
        # Update only provided fields
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(current_prefs, field):
                setattr(current_prefs, field, value)
        
        # Save updated preferences
        await chat_service.update_user_preferences(user_id, current_prefs)
        
        return current_prefs
        
    except Exception as e:
        logger.error(f"Error updating user preferences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user preferences"
        )

@router.post("/chat/explain/{indicator}")
async def explain_technical_indicator(
    indicator: str,
    value: float,
    symbol: str,
    current_user: dict = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Get explanation of a technical indicator
    
    Args:
        indicator: Name of the technical indicator
        value: Current value of the indicator
        symbol: Stock symbol
        current_user: Current authenticated user
        
    Returns:
        Explanation of the technical indicator
    """
    try:
        user_id = current_user["sub"]
        
        # Get conversation context for personalized explanation
        context = await chat_service.get_conversation_context(user_id)
        
        # Get explanation from Vertex AI
        explanation = await chat_service.vertex_ai.explain_technical_indicator(
            indicator, value, symbol, context
        )
        
        return {"explanation": explanation}
        
    except Exception as e:
        logger.error(f"Error explaining technical indicator: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to explain technical indicator"
        )

@router.get("/chat/market-summary")
async def get_market_summary(
    current_user: dict = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Get AI-generated market summary
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Market summary text
    """
    try:
        # This would typically get real market data
        # For now, using placeholder data
        market_data = [
            {"symbol": "SPY", "change": 0.5, "volume": 75000000},
            {"symbol": "QQQ", "change": -0.2, "volume": 45000000},
            {"symbol": "IWM", "change": 1.2, "volume": 30000000}
        ]
        
        # Get conversation context
        user_id = current_user["sub"]
        context = await chat_service.get_conversation_context(user_id)
        
        # Generate market summary
        summary = await chat_service.vertex_ai.generate_market_summary(market_data, context)
        
        return {"summary": summary}
        
    except Exception as e:
        logger.error(f"Error generating market summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate market summary"
        )

@router.get("/chat/health")
async def chat_health_check(
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Health check endpoint for chat service
    
    Returns:
        Service status and active sessions count
    """
    try:
        active_sessions = chat_service.vertex_ai.get_active_sessions_count() if chat_service.vertex_ai else 0
        
        return {
            "status": "healthy",
            "service": "chat",
            "active_sessions": active_sessions,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Chat health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat service is unhealthy"
        )