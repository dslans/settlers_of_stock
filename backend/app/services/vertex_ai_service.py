"""
Vertex AI service for generating conversational responses about stock analysis.
Integrates with Google Cloud Vertex AI Gemini models for natural language generation.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

import vertexai
from vertexai.generative_models import GenerativeModel, ChatSession
from google.cloud import aiplatform
from pydantic import BaseModel

from app.core.config import get_settings

logger = logging.getLogger(__name__)

class ConversationContext(BaseModel):
    """Context for maintaining conversation state"""
    user_id: str
    previous_messages: List[Dict[str, str]] = []
    current_stocks: List[str] = []
    analysis_history: List[Dict[str, Any]] = []
    user_preferences: Dict[str, Any] = {}
    session_start: datetime = datetime.now()

class AnalysisResult(BaseModel):
    """Stock analysis result data structure"""
    symbol: str
    recommendation: str
    confidence: int
    reasoning: List[str]
    risks: List[str]
    targets: Dict[str, float] = {}
    analysis_type: str = "combined"
    timestamp: datetime = datetime.now()

class VertexAIService:
    """Service for generating conversational responses using Vertex AI Gemini models"""
    
    def __init__(self, project_id: Optional[str] = None, location: str = "us-central1", testing_mode: bool = False):
        """Initialize Vertex AI service with project configuration"""
        self.settings = get_settings()
        self.project_id = project_id or self.settings.GCP_PROJECT_ID
        self.location = location
        self.testing_mode = testing_mode
        
        if not self.project_id and not testing_mode:
            raise ValueError("GCP_PROJECT_ID must be set in configuration")
        
        # Initialize Vertex AI only if not in testing mode
        if not testing_mode:
            vertexai.init(project=self.project_id, location=self.location)
            # Use cost-effective Gemini Flash model for most responses
            self.model = GenerativeModel("gemini-1.5-flash")
        else:
            # Mock model for testing
            self.model = None
        
        # Keep track of active chat sessions for context
        self.chat_sessions: Dict[str, ChatSession] = {}
        
        if not testing_mode:
            logger.info(f"Initialized Vertex AI service for project {self.project_id}")
        else:
            logger.info("Initialized Vertex AI service in testing mode")
    
    async def generate_stock_analysis_response(
        self, 
        analysis_data: AnalysisResult, 
        user_query: str,
        context: Optional[ConversationContext] = None
    ) -> str:
        """
        Generate conversational response about stock analysis
        
        Args:
            analysis_data: The stock analysis results
            user_query: The user's original query
            context: Conversation context for follow-up questions
            
        Returns:
            Natural language response explaining the analysis
        """
        try:
            # Build context-aware prompt
            prompt = self._build_analysis_prompt(analysis_data, user_query, context)
            
            # Get or create chat session for context continuity
            if context and context.user_id in self.chat_sessions:
                chat_session = self.chat_sessions[context.user_id]
                response = await chat_session.send_message_async(prompt)
            else:
                response = await self.model.generate_content_async(prompt)
                
                # Create new chat session if context provided
                if context:
                    self.chat_sessions[context.user_id] = self.model.start_chat()
            
            response_text = response.text
            
            # Update conversation context
            if context:
                context.previous_messages.append({
                    "user": user_query,
                    "assistant": response_text,
                    "timestamp": datetime.now().isoformat()
                })
                if analysis_data.symbol not in context.current_stocks:
                    context.current_stocks.append(analysis_data.symbol)
            
            logger.info(f"Generated analysis response for {analysis_data.symbol}")
            return response_text
            
        except Exception as e:
            logger.error(f"Error generating analysis response: {str(e)}")
            return self._get_fallback_response(analysis_data, user_query)
    
    async def generate_market_summary(
        self, 
        market_data: List[Dict[str, Any]], 
        context: Optional[ConversationContext] = None
    ) -> str:
        """Generate market overview summary"""
        try:
            prompt = f"""
            You are a knowledgeable stock market analyst. Based on the following market data,
            provide a conversational summary of current market conditions.
            
            Market Data:
            {json.dumps(market_data, indent=2, default=str)}
            
            Provide a brief, conversational summary that highlights:
            - Overall market sentiment and trends
            - Notable movers (both up and down)
            - Any significant patterns or concerns
            - Keep it accessible for both novice and experienced investors
            
            Limit response to 3-4 sentences.
            """
            
            response = await self.model.generate_content_async(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating market summary: {str(e)}")
            return "I'm having trouble accessing market data right now. Please try again in a moment."
    
    async def explain_technical_indicator(
        self, 
        indicator: str, 
        value: float, 
        symbol: str,
        context: Optional[ConversationContext] = None
    ) -> str:
        """Explain what a technical indicator means in context"""
        try:
            prompt = f"""
            You are a patient financial educator. Explain the technical indicator {indicator} 
            with a current value of {value} for stock {symbol}.
            
            Provide a clear explanation that includes:
            - What this indicator measures
            - What the current value suggests about the stock
            - How traders typically interpret this indicator
            - Any important caveats or limitations
            
            Use simple language and avoid jargon. Make it educational but practical.
            Keep response to 2-3 sentences.
            """
            
            response = await self.model.generate_content_async(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Error explaining technical indicator: {str(e)}")
            return f"The {indicator} indicator is currently at {value} for {symbol}. This is a technical measure used by traders to analyze price trends."
    
    async def handle_follow_up_question(
        self, 
        question: str, 
        context: ConversationContext
    ) -> str:
        """Handle follow-up questions using conversation context"""
        try:
            # Build context-aware prompt for follow-up
            recent_context = ""
            if context.previous_messages:
                recent_messages = context.previous_messages[-3:]  # Last 3 exchanges
                recent_context = "\n".join([
                    f"User: {msg['user']}\nAssistant: {msg['assistant']}"
                    for msg in recent_messages
                ])
            
            current_stocks_context = ""
            if context.current_stocks:
                current_stocks_context = f"Currently discussing stocks: {', '.join(context.current_stocks)}"
            
            prompt = f"""
            You are continuing a conversation about stock analysis. Here's the recent context:
            
            {recent_context}
            
            {current_stocks_context}
            
            User's follow-up question: {question}
            
            Provide a helpful response that builds on the previous conversation.
            If the question is about a stock we've discussed, reference the previous analysis.
            If it's a new topic, acknowledge the context shift naturally.
            
            Keep the response conversational and helpful.
            """
            
            # Use existing chat session for continuity
            if context.user_id in self.chat_sessions:
                chat_session = self.chat_sessions[context.user_id]
                response = await chat_session.send_message_async(prompt)
            else:
                response = await self.model.generate_content_async(prompt)
                self.chat_sessions[context.user_id] = self.model.start_chat()
            
            # Update context
            context.previous_messages.append({
                "user": question,
                "assistant": response.text,
                "timestamp": datetime.now().isoformat()
            })
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error handling follow-up question: {str(e)}")
            return "I'm having trouble processing your follow-up question. Could you please rephrase it?"
    
    def _build_analysis_prompt(
        self, 
        analysis_data: AnalysisResult, 
        user_query: str, 
        context: Optional[ConversationContext]
    ) -> str:
        """Build comprehensive prompt for stock analysis response"""
        
        # Base analysis information
        base_prompt = f"""
        You are a knowledgeable and friendly stock analyst assistant. Based on the following 
        analysis data, provide a conversational response to the user's query.
        
        Stock Analysis for {analysis_data.symbol}:
        - Recommendation: {analysis_data.recommendation}
        - Confidence Level: {analysis_data.confidence}%
        - Analysis Type: {analysis_data.analysis_type}
        - Key Reasoning: {', '.join(analysis_data.reasoning)}
        - Risk Factors: {', '.join(analysis_data.risks)}
        """
        
        # Add price targets if available
        if analysis_data.targets:
            targets_text = ", ".join([f"{period}: ${target:.2f}" for period, target in analysis_data.targets.items()])
            base_prompt += f"\n- Price Targets: {targets_text}"
        
        # Add user context if available
        context_prompt = ""
        if context:
            if context.current_stocks:
                context_prompt += f"\nPreviously discussed stocks: {', '.join(context.current_stocks)}"
            
            if context.user_preferences:
                risk_tolerance = context.user_preferences.get('risk_tolerance', 'moderate')
                context_prompt += f"\nUser's risk tolerance: {risk_tolerance}"
        
        # Final instructions
        instructions = f"""
        {context_prompt}
        
        User's Question: {user_query}
        
        Provide a helpful, conversational response that:
        - Explains the analysis in plain English
        - Includes specific numbers and reasoning
        - Addresses the user's specific question
        - Mentions both opportunities and risks
        - Keeps the tone friendly and accessible
        - Limits response to 3-4 sentences for clarity
        
        Remember: This is for informational purposes only, not financial advice.
        """
        
        return base_prompt + instructions
    
    def _get_fallback_response(self, analysis_data: AnalysisResult, user_query: str) -> str:
        """Provide fallback response when AI generation fails"""
        return f"""
        Based on my analysis of {analysis_data.symbol}, I have a {analysis_data.recommendation} 
        recommendation with {analysis_data.confidence}% confidence. The key factors supporting 
        this view include: {', '.join(analysis_data.reasoning[:2])}. However, please be aware 
        of these risks: {', '.join(analysis_data.risks[:2])}. This analysis is for informational 
        purposes only and should not be considered financial advice.
        """
    
    def clear_chat_session(self, user_id: str) -> None:
        """Clear chat session for a user to start fresh"""
        if user_id in self.chat_sessions:
            del self.chat_sessions[user_id]
            logger.info(f"Cleared chat session for user {user_id}")
    
    def get_active_sessions_count(self) -> int:
        """Get count of active chat sessions"""
        return len(self.chat_sessions)