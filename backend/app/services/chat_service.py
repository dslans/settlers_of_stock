"""
Chat service for handling conversational interactions with stock analysis.
Integrates with Vertex AI service for natural language responses.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import redis
from pydantic import BaseModel

from app.services.vertex_ai_service import VertexAIService, ConversationContext, AnalysisResult
from app.services.education_service import EducationService
from app.services.disclaimer_service import disclaimer_service, DisclaimerContext
from app.core.config import get_settings

logger = logging.getLogger(__name__)

class ChatMessage(BaseModel):
    """Chat message data structure"""
    id: str
    user_id: str
    type: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime = datetime.now()
    metadata: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    """Response from chat service"""
    message: str
    message_type: str = "assistant"
    analysis_data: Optional[Dict[str, Any]] = None
    suggestions: List[str] = []
    requires_follow_up: bool = False

class UserPreferences(BaseModel):
    """User preferences for personalized responses"""
    risk_tolerance: str = "moderate"  # conservative, moderate, aggressive
    investment_horizon: str = "medium"  # short, medium, long
    preferred_analysis: List[str] = ["fundamental", "technical"]
    notification_settings: Dict[str, bool] = {}

class ChatService:
    """Service for handling conversational stock analysis interactions"""
    
    def __init__(self, testing_mode: bool = False, db_session=None):
        self.settings = get_settings()
        self.testing_mode = testing_mode
        self.db_session = db_session
        
        # Initialize Vertex AI service
        try:
            self.vertex_ai = VertexAIService(testing_mode=testing_mode)
        except ValueError as e:
            if testing_mode:
                # Create a mock vertex AI service for testing
                self.vertex_ai = None
                logger.info("Initialized Chat Service in testing mode without Vertex AI")
            else:
                raise e
        
        # Initialize Education service if database session is available
        if db_session and not testing_mode:
            self.education_service = EducationService(db_session, self.vertex_ai)
        else:
            self.education_service = None
        
        # Initialize Redis for context storage
        if not testing_mode:
            try:
                self.redis_client = redis.Redis(
                    host=self.settings.REDIS_HOST,
                    port=self.settings.REDIS_PORT,
                    decode_responses=True
                )
                self.redis_client.ping()  # Test connection
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Context will not persist.")
                self.redis_client = None
        else:
            self.redis_client = None
        
        if not testing_mode:
            logger.info("Initialized Chat Service with Vertex AI integration")
        else:
            logger.info("Initialized Chat Service in testing mode")
    
    async def process_message(
        self, 
        user_id: str, 
        message: str, 
        analysis_result: Optional[AnalysisResult] = None
    ) -> ChatResponse:
        """
        Process user message and generate intelligent response
        
        Args:
            user_id: Unique identifier for the user
            message: User's message/query
            analysis_result: Optional analysis result to base response on
            
        Returns:
            ChatResponse with generated message and metadata
        """
        try:
            # Get or create conversation context
            context = await self.get_conversation_context(user_id)
            
            # Check if message contains educational concepts that need explanation
            educational_concepts = []
            if self.education_service:
                educational_concepts = await self.education_service.extract_concepts_from_text(message)
            
            # Determine message type and generate appropriate response
            if analysis_result:
                # Generate response based on analysis
                response_text = await self.vertex_ai.generate_stock_analysis_response(
                    analysis_result, message, context
                )
                
                # Add educational explanations if concepts were mentioned
                if educational_concepts:
                    response_text = await self._enhance_response_with_education(
                        response_text, educational_concepts, analysis_result.symbol
                    )
                
                # Determine disclaimer context based on response content
                disclaimer_context = self._determine_disclaimer_context(response_text, analysis_result)
                
                # Add disclaimers to response
                response_with_disclaimers = disclaimer_service.add_disclaimers_to_response(
                    response_text,
                    disclaimer_context,
                    risk_level=getattr(analysis_result, 'risk_level', None),
                    volatility=getattr(analysis_result, 'volatility', None),
                    symbol=analysis_result.symbol,
                    compact=True
                )
                
                chat_response = ChatResponse(
                    message=response_with_disclaimers,
                    analysis_data={
                        "symbol": analysis_result.symbol,
                        "recommendation": analysis_result.recommendation,
                        "confidence": analysis_result.confidence,
                        "educational_concepts": educational_concepts,
                        "disclaimer_metadata": disclaimer_service.get_disclaimer_metadata(disclaimer_context)
                    },
                    suggestions=self._generate_follow_up_suggestions(analysis_result)
                )
            else:
                # Check if this is a direct educational question
                if self._is_educational_question(message):
                    response_text = await self._handle_educational_question(message, context)
                else:
                    # Handle as follow-up or general question
                    response_text = await self.vertex_ai.handle_follow_up_question(message, context)
                
                # Add educational explanations if concepts were mentioned
                if educational_concepts:
                    response_text = await self._enhance_response_with_education(
                        response_text, educational_concepts
                    )
                
                # Add disclaimers for general chat responses
                response_with_disclaimers = disclaimer_service.add_disclaimers_to_response(
                    response_text,
                    DisclaimerContext.CHAT_RESPONSE,
                    compact=True
                )
                
                chat_response = ChatResponse(
                    message=response_with_disclaimers,
                    suggestions=self._generate_general_suggestions(context),
                    metadata={"educational_concepts": educational_concepts} if educational_concepts else None
                )
            
            # Store the conversation
            await self.store_chat_message(user_id, ChatMessage(
                id=f"user_{datetime.now().timestamp()}",
                user_id=user_id,
                type="user",
                content=message
            ))
            
            await self.store_chat_message(user_id, ChatMessage(
                id=f"assistant_{datetime.now().timestamp()}",
                user_id=user_id,
                type="assistant",
                content=chat_response.message,
                metadata=chat_response.analysis_data
            ))
            
            # Update context in Redis
            await self.store_conversation_context(user_id, context)
            
            return chat_response
            
        except Exception as e:
            logger.error(f"Error processing message for user {user_id}: {str(e)}")
            return ChatResponse(
                message="I'm having trouble processing your request right now. Please try again in a moment.",
                message_type="error"
            )
    
    async def get_conversation_context(self, user_id: str) -> ConversationContext:
        """Retrieve or create conversation context for user"""
        try:
            if self.redis_client:
                context_data = self.redis_client.get(f"chat_context:{user_id}")
                if context_data:
                    context_dict = json.loads(context_data)
                    return ConversationContext(**context_dict)
            
            # Create new context if none exists
            return ConversationContext(user_id=user_id)
            
        except Exception as e:
            logger.error(f"Error retrieving context for user {user_id}: {str(e)}")
            return ConversationContext(user_id=user_id)
    
    async def store_conversation_context(self, user_id: str, context: ConversationContext) -> None:
        """Store conversation context in Redis with TTL"""
        try:
            if self.redis_client:
                context_data = context.model_dump_json()
                # Store with 24 hour TTL
                self.redis_client.setex(f"chat_context:{user_id}", 86400, context_data)
                
        except Exception as e:
            logger.error(f"Error storing context for user {user_id}: {str(e)}")
    
    async def store_chat_message(self, user_id: str, message: ChatMessage) -> None:
        """Store chat message for history (could be extended to use Firestore)"""
        try:
            if self.redis_client:
                # Store recent messages in Redis list (keep last 50 messages)
                message_data = message.model_dump_json()
                pipe = self.redis_client.pipeline()
                pipe.lpush(f"chat_history:{user_id}", message_data)
                pipe.ltrim(f"chat_history:{user_id}", 0, 49)  # Keep only last 50
                pipe.expire(f"chat_history:{user_id}", 86400)  # 24 hour TTL
                pipe.execute()
                
        except Exception as e:
            logger.error(f"Error storing message for user {user_id}: {str(e)}")
    
    async def get_chat_history(self, user_id: str, limit: int = 20) -> List[ChatMessage]:
        """Retrieve recent chat history for user"""
        try:
            if self.redis_client:
                messages_data = self.redis_client.lrange(f"chat_history:{user_id}", 0, limit - 1)
                messages = []
                for msg_data in reversed(messages_data):  # Reverse to get chronological order
                    try:
                        msg_dict = json.loads(msg_data)
                        messages.append(ChatMessage(**msg_dict))
                    except Exception as e:
                        logger.warning(f"Error parsing message: {e}")
                        continue
                return messages
            
            return []
            
        except Exception as e:
            logger.error(f"Error retrieving chat history for user {user_id}: {str(e)}")
            return []
    
    async def clear_conversation(self, user_id: str) -> None:
        """Clear conversation history and context for user"""
        try:
            if self.redis_client:
                self.redis_client.delete(f"chat_context:{user_id}")
                self.redis_client.delete(f"chat_history:{user_id}")
            
            # Clear Vertex AI chat session
            self.vertex_ai.clear_chat_session(user_id)
            
            logger.info(f"Cleared conversation for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error clearing conversation for user {user_id}: {str(e)}")
    
    def _generate_follow_up_suggestions(self, analysis_result: AnalysisResult) -> List[str]:
        """Generate contextual follow-up suggestions based on analysis"""
        suggestions = []
        
        if analysis_result.recommendation == "BUY":
            suggestions.extend([
                f"What are the main risks with {analysis_result.symbol}?",
                f"How does {analysis_result.symbol} compare to its competitors?",
                "What's a good entry point for this stock?"
            ])
        elif analysis_result.recommendation == "SELL":
            suggestions.extend([
                f"Why is {analysis_result.symbol} declining?",
                "Are there any catalysts that could turn this around?",
                "What are some alternatives to consider?"
            ])
        else:  # HOLD
            suggestions.extend([
                f"What would make {analysis_result.symbol} a buy?",
                "How long should I hold this position?",
                "What key metrics should I watch?"
            ])
        
        # Add general suggestions
        suggestions.extend([
            "Show me the technical analysis",
            "What's the latest news?",
            "Compare this to the sector average"
        ])
        
        return suggestions[:4]  # Return top 4 suggestions
    
    def _generate_general_suggestions(self, context: ConversationContext) -> List[str]:
        """Generate general suggestions based on conversation context"""
        suggestions = [
            "Analyze a stock symbol",
            "Show me market trends",
            "Find investment opportunities",
            "Explain a financial term"
        ]
        
        # Add context-specific suggestions
        if context.current_stocks:
            recent_stock = context.current_stocks[-1]
            suggestions.insert(0, f"Get an update on {recent_stock}")
            suggestions.insert(1, f"Compare {recent_stock} to similar stocks")
        
        return suggestions[:4]
    
    async def get_user_preferences(self, user_id: str) -> UserPreferences:
        """Get user preferences (placeholder for future database integration)"""
        try:
            if self.redis_client:
                prefs_data = self.redis_client.get(f"user_prefs:{user_id}")
                if prefs_data:
                    prefs_dict = json.loads(prefs_data)
                    return UserPreferences(**prefs_dict)
            
            return UserPreferences()  # Return defaults
            
        except Exception as e:
            logger.error(f"Error retrieving preferences for user {user_id}: {str(e)}")
            return UserPreferences()
    
    async def update_user_preferences(self, user_id: str, preferences: UserPreferences) -> None:
        """Update user preferences"""
        try:
            if self.redis_client:
                prefs_data = preferences.model_dump_json()
                self.redis_client.setex(f"user_prefs:{user_id}", 86400 * 30, prefs_data)  # 30 day TTL
                
        except Exception as e:
            logger.error(f"Error updating preferences for user {user_id}: {str(e)}")
    
    def _is_educational_question(self, message: str) -> bool:
        """Check if message is asking for educational content"""
        educational_keywords = [
            "what is", "what does", "explain", "how does", "define", "meaning of",
            "what means", "help me understand", "can you explain", "tell me about"
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in educational_keywords)
    
    async def _handle_educational_question(self, message: str, context: ConversationContext) -> str:
        """Handle direct educational questions"""
        if not self.education_service:
            return "I'd be happy to help explain financial concepts, but the educational service is not available right now."
        
        try:
            # Extract potential concept name from question
            concept_name = self._extract_concept_from_question(message)
            if concept_name:
                explanation = await self.education_service.get_contextual_explanation(
                    concept_name=concept_name,
                    context=f"User question: {message}",
                    user_level="beginner"  # Default to beginner, could be personalized
                )
                
                if explanation:
                    response = f"{explanation.contextual_explanation}\n\n"
                    
                    if explanation.related_suggestions:
                        response += "**Related concepts you might find interesting:**\n"
                        for concept in explanation.related_suggestions[:3]:
                            response += f"• {concept.name}: {concept.short_description}\n"
                    
                    if explanation.next_learning_steps:
                        response += "\n**Next steps to deepen your understanding:**\n"
                        for step in explanation.next_learning_steps[:2]:
                            response += f"• {step}\n"
                    
                    return response
            
            # If no specific concept found, provide general educational guidance
            return await self.vertex_ai.handle_follow_up_question(message, context)
            
        except Exception as e:
            logger.error(f"Error handling educational question: {str(e)}")
            return "I'm having trouble accessing educational content right now. Please try asking again."
    
    def _extract_concept_from_question(self, message: str) -> Optional[str]:
        """Extract concept name from educational question"""
        # Simple extraction - could be enhanced with NLP
        message_lower = message.lower()
        
        # Common patterns for asking about concepts
        patterns = [
            r"what is (?:a |an |the )?(.+?)(?:\?|$)",
            r"what does (.+?) mean",
            r"explain (.+?)(?:\?|$)",
            r"tell me about (.+?)(?:\?|$)",
            r"define (.+?)(?:\?|$)"
        ]
        
        import re
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                concept = match.group(1).strip()
                # Clean up common words
                concept = re.sub(r'\b(the|a|an|is|are|was|were)\b', '', concept).strip()
                return concept
        
        return None
    
    async def _enhance_response_with_education(
        self, 
        response: str, 
        concepts: List[str], 
        context_symbol: Optional[str] = None
    ) -> str:
        """Enhance response with educational explanations for mentioned concepts"""
        if not self.education_service or not concepts:
            return response
        
        try:
            enhanced_response = response + "\n\n"
            
            # Add explanations for up to 2 concepts to avoid overwhelming
            for concept_name in concepts[:2]:
                explanation = await self.education_service.get_contextual_explanation(
                    concept_name=concept_name,
                    context=f"Stock analysis context: {context_symbol}" if context_symbol else None,
                    user_level="beginner"
                )
                
                if explanation:
                    enhanced_response += f"**📚 Quick explanation - {concept_name}:**\n"
                    # Use a shorter version of the explanation
                    short_explanation = explanation.contextual_explanation.split('\n')[0]
                    enhanced_response += f"{short_explanation}\n\n"
            
            if len(concepts) > 2:
                enhanced_response += f"*I also noticed mentions of {', '.join(concepts[2:])}. Ask me about any of these for more details!*\n"
            
            return enhanced_response
            
        except Exception as e:
            logger.error(f"Error enhancing response with education: {str(e)}")
            return response
    
    def _determine_disclaimer_context(self, response_text: str, analysis_result: Optional[AnalysisResult] = None) -> DisclaimerContext:
        """Determine the appropriate disclaimer context based on response content."""
        response_lower = response_text.lower()
        
        # Check for recommendation keywords
        recommendation_keywords = ['recommend', 'buy', 'sell', 'hold', 'should invest', 'suggest']
        if any(keyword in response_lower for keyword in recommendation_keywords):
            return DisclaimerContext.RECOMMENDATION
        
        # Check if this is an analysis result
        if analysis_result:
            return DisclaimerContext.ANALYSIS_RESULT
        
        # Default to chat response
        return DisclaimerContext.CHAT_RESPONSE