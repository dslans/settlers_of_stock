"""
Educational service for managing financial concept explanations and learning paths.
"""

import re
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.education import (
    EducationalConcept, LearningPath, UserLearningProgress,
    ConceptType, DifficultyLevel,
    EducationalConceptResponse, ConceptExplanationResponse,
    LearningPathResponse, UserLearningProgressResponse
)
from app.services.vertex_ai_service import VertexAIService


class EducationService:
    """Service for educational content and explanations"""

    def __init__(self, db: Session, vertex_ai_service: VertexAIService):
        self.db = db
        self.vertex_ai_service = vertex_ai_service
        self._initialize_default_concepts()

    def _initialize_default_concepts(self):
        """Initialize default educational concepts if they don't exist"""
        # Check if concepts already exist
        existing_count = self.db.query(EducationalConcept).count()
        if existing_count > 0:
            return

        # Define default concepts
        default_concepts = [
            # Technical Indicators
            {
                "name": "RSI (Relative Strength Index)",
                "concept_type": ConceptType.TECHNICAL_INDICATOR,
                "difficulty_level": DifficultyLevel.BEGINNER,
                "short_description": "Momentum oscillator that measures the speed and change of price movements",
                "detailed_explanation": "RSI is a momentum oscillator that ranges from 0 to 100. It measures how quickly prices are changing and helps identify overbought (>70) and oversold (<30) conditions. RSI is calculated using average gains and losses over a specified period, typically 14 days.",
                "practical_example": "If Apple's RSI is 75, it suggests the stock may be overbought and due for a pullback. Conversely, an RSI of 25 might indicate oversold conditions and a potential buying opportunity.",
                "formula": "RSI = 100 - (100 / (1 + RS)), where RS = Average Gain / Average Loss",
                "interpretation_guide": "RSI > 70: Potentially overbought, consider selling. RSI < 30: Potentially oversold, consider buying. RSI around 50: Neutral momentum.",
                "common_mistakes": "Don't rely solely on RSI for trading decisions. In strong trends, RSI can remain overbought or oversold for extended periods.",
                "keywords": "momentum, overbought, oversold, oscillator, technical analysis"
            },
            {
                "name": "Moving Average",
                "concept_type": ConceptType.TECHNICAL_INDICATOR,
                "difficulty_level": DifficultyLevel.BEGINNER,
                "short_description": "Average price over a specific number of periods to smooth out price fluctuations",
                "detailed_explanation": "Moving averages smooth out price data to identify trends. Simple Moving Average (SMA) calculates the arithmetic mean, while Exponential Moving Average (EMA) gives more weight to recent prices. Common periods are 20, 50, and 200 days.",
                "practical_example": "If Tesla's 50-day moving average is $250 and the current price is $270, the stock is trading above its average, suggesting an uptrend.",
                "formula": "SMA = (Sum of prices over n periods) / n. EMA = (Current Price × Multiplier) + (Previous EMA × (1 - Multiplier))",
                "interpretation_guide": "Price above MA: Uptrend. Price below MA: Downtrend. MA slope indicates trend strength.",
                "common_mistakes": "Moving averages lag price action. Don't use them alone for entry/exit signals in choppy markets.",
                "keywords": "trend, SMA, EMA, smoothing, support, resistance"
            },
            {
                "name": "MACD (Moving Average Convergence Divergence)",
                "concept_type": ConceptType.TECHNICAL_INDICATOR,
                "difficulty_level": DifficultyLevel.INTERMEDIATE,
                "short_description": "Trend-following momentum indicator showing relationship between two moving averages",
                "detailed_explanation": "MACD consists of three components: MACD line (12-day EMA minus 26-day EMA), Signal line (9-day EMA of MACD line), and Histogram (difference between MACD and Signal lines). It helps identify trend changes and momentum shifts.",
                "practical_example": "When Microsoft's MACD line crosses above the signal line, it generates a bullish signal. When the histogram turns positive, it confirms strengthening upward momentum.",
                "formula": "MACD Line = 12-day EMA - 26-day EMA. Signal Line = 9-day EMA of MACD Line. Histogram = MACD Line - Signal Line",
                "interpretation_guide": "MACD above signal: Bullish momentum. MACD below signal: Bearish momentum. Histogram shows momentum strength.",
                "common_mistakes": "MACD can generate false signals in sideways markets. Always confirm with other indicators.",
                "keywords": "momentum, convergence, divergence, crossover, histogram"
            },
            # Fundamental Ratios
            {
                "name": "P/E Ratio (Price-to-Earnings)",
                "concept_type": ConceptType.FUNDAMENTAL_RATIO,
                "difficulty_level": DifficultyLevel.BEGINNER,
                "short_description": "Valuation ratio comparing stock price to earnings per share",
                "detailed_explanation": "P/E ratio measures how much investors are willing to pay for each dollar of earnings. It's calculated by dividing the stock price by earnings per share (EPS). A higher P/E suggests investors expect higher earnings growth, while a lower P/E might indicate undervaluation or poor growth prospects.",
                "practical_example": "If Amazon trades at $3,000 with EPS of $100, its P/E ratio is 30. This means investors pay $30 for every $1 of earnings, expecting significant growth.",
                "formula": "P/E Ratio = Stock Price / Earnings Per Share (EPS)",
                "interpretation_guide": "High P/E: Growth expectations or overvaluation. Low P/E: Value opportunity or declining business. Compare to industry averages.",
                "common_mistakes": "Don't compare P/E ratios across different industries. Consider growth rates and debt levels.",
                "keywords": "valuation, earnings, growth, overvalued, undervalued"
            },
            {
                "name": "ROE (Return on Equity)",
                "concept_type": ConceptType.FUNDAMENTAL_RATIO,
                "difficulty_level": DifficultyLevel.INTERMEDIATE,
                "short_description": "Profitability ratio measuring how efficiently a company uses shareholders' equity",
                "detailed_explanation": "ROE measures how much profit a company generates with shareholders' equity. It's calculated by dividing net income by shareholders' equity. Higher ROE indicates more efficient use of equity capital. ROE above 15% is generally considered good.",
                "practical_example": "If Coca-Cola has net income of $9 billion and shareholders' equity of $20 billion, its ROE is 45%, indicating excellent profitability.",
                "formula": "ROE = Net Income / Shareholders' Equity × 100%",
                "interpretation_guide": "ROE > 15%: Excellent. ROE 10-15%: Good. ROE < 10%: Poor. Compare within industry.",
                "common_mistakes": "High ROE from excessive debt can be risky. Consider debt levels and sustainability.",
                "keywords": "profitability, efficiency, equity, management effectiveness"
            },
            # Market Concepts
            {
                "name": "Market Capitalization",
                "concept_type": ConceptType.MARKET_CONCEPT,
                "difficulty_level": DifficultyLevel.BEGINNER,
                "short_description": "Total value of a company's shares in the stock market",
                "detailed_explanation": "Market cap represents the total dollar value of a company's outstanding shares. It's calculated by multiplying the stock price by the number of outstanding shares. Companies are categorized as large-cap (>$10B), mid-cap ($2-10B), or small-cap (<$2B).",
                "practical_example": "If Google has 13 billion shares outstanding at $2,800 per share, its market cap is $36.4 trillion, making it a large-cap stock.",
                "formula": "Market Cap = Stock Price × Outstanding Shares",
                "interpretation_guide": "Large-cap: Stable, established companies. Mid-cap: Growth potential with moderate risk. Small-cap: High growth potential, higher risk.",
                "common_mistakes": "Don't confuse market cap with company value. Consider debt and cash positions.",
                "keywords": "valuation, size, large-cap, mid-cap, small-cap, outstanding shares"
            }
        ]

        # Create concepts in database
        for concept_data in default_concepts:
            concept = EducationalConcept(**concept_data)
            self.db.add(concept)

        self.db.commit()

    async def get_concept_by_name(self, name: str) -> Optional[EducationalConceptResponse]:
        """Get educational concept by name"""
        concept = self.db.query(EducationalConcept).filter(
            EducationalConcept.name.ilike(f"%{name}%"),
            EducationalConcept.is_active == True
        ).first()

        if concept:
            return EducationalConceptResponse.from_orm(concept)
        return None

    async def search_concepts(
        self, 
        query: str, 
        concept_type: Optional[ConceptType] = None,
        difficulty_level: Optional[DifficultyLevel] = None,
        limit: int = 10
    ) -> List[EducationalConceptResponse]:
        """Search educational concepts by query"""
        db_query = self.db.query(EducationalConcept).filter(
            EducationalConcept.is_active == True
        )

        # Add text search
        if query:
            search_filter = or_(
                EducationalConcept.name.ilike(f"%{query}%"),
                EducationalConcept.short_description.ilike(f"%{query}%"),
                EducationalConcept.keywords.ilike(f"%{query}%")
            )
            db_query = db_query.filter(search_filter)

        # Add filters
        if concept_type:
            db_query = db_query.filter(EducationalConcept.concept_type == concept_type)
        
        if difficulty_level:
            db_query = db_query.filter(EducationalConcept.difficulty_level == difficulty_level)

        concepts = db_query.limit(limit).all()
        return [EducationalConceptResponse.from_orm(concept) for concept in concepts]

    async def get_contextual_explanation(
        self, 
        concept_name: str, 
        context: Optional[str] = None,
        user_level: DifficultyLevel = DifficultyLevel.BEGINNER
    ) -> Optional[ConceptExplanationResponse]:
        """Get contextual explanation for a concept"""
        concept = await self.get_concept_by_name(concept_name)
        if not concept:
            return None

        # Generate contextual explanation using AI
        contextual_explanation = await self._generate_contextual_explanation(
            concept, context, user_level
        )

        # Get related concepts
        related_concepts = await self._get_related_concepts(concept.id)

        # Generate next learning steps
        next_steps = await self._generate_learning_steps(concept, user_level)

        return ConceptExplanationResponse(
            concept=concept,
            contextual_explanation=contextual_explanation,
            related_suggestions=related_concepts,
            next_learning_steps=next_steps
        )

    async def _generate_contextual_explanation(
        self, 
        concept: EducationalConceptResponse, 
        context: Optional[str],
        user_level: DifficultyLevel
    ) -> str:
        """Generate contextual explanation using AI"""
        prompt = f"""
        Explain the financial concept "{concept.name}" in a conversational way.
        
        Base Information:
        - Type: {concept.concept_type}
        - Description: {concept.short_description}
        - Detailed Explanation: {concept.detailed_explanation}
        - Formula: {concept.formula or 'N/A'}
        
        Context: {context or 'General explanation'}
        User Level: {user_level}
        
        Requirements:
        - Use simple, clear language appropriate for {user_level} level
        - Include practical examples relevant to the context
        - Explain why this concept matters for investing/trading
        - Keep explanation concise but informative (2-3 paragraphs)
        - Avoid jargon unless you explain it
        
        Provide a helpful, educational explanation that helps the user understand both what this concept is and how to use it.
        """

        try:
            explanation = await self.vertex_ai_service.generate_content(prompt)
            return explanation
        except Exception as e:
            # Fallback to basic explanation
            return f"{concept.detailed_explanation}\n\n{concept.practical_example or ''}"

    async def _get_related_concepts(self, concept_id: int, limit: int = 5) -> List[EducationalConceptResponse]:
        """Get related concepts"""
        # For now, get concepts of the same type or related keywords
        concept = self.db.query(EducationalConcept).filter(
            EducationalConcept.id == concept_id
        ).first()

        if not concept:
            return []

        related = self.db.query(EducationalConcept).filter(
            and_(
                EducationalConcept.id != concept_id,
                EducationalConcept.is_active == True,
                or_(
                    EducationalConcept.concept_type == concept.concept_type,
                    EducationalConcept.difficulty_level == concept.difficulty_level
                )
            )
        ).limit(limit).all()

        return [EducationalConceptResponse.from_orm(c) for c in related]

    async def _generate_learning_steps(
        self, 
        concept: EducationalConceptResponse, 
        user_level: DifficultyLevel
    ) -> List[str]:
        """Generate next learning steps"""
        if user_level == DifficultyLevel.BEGINNER:
            return [
                f"Practice identifying {concept.name} in real stock charts",
                "Learn how to interpret the values in different market conditions",
                "Study related concepts to build comprehensive understanding"
            ]
        elif user_level == DifficultyLevel.INTERMEDIATE:
            return [
                f"Combine {concept.name} with other indicators for better signals",
                "Backtest strategies using this concept",
                "Learn advanced applications and edge cases"
            ]
        else:  # Advanced
            return [
                f"Develop custom strategies incorporating {concept.name}",
                "Study academic research on this concept's effectiveness",
                "Teach others or write about your insights"
            ]

    async def extract_concepts_from_text(self, text: str) -> List[str]:
        """Extract financial concepts mentioned in text"""
        # Get all concept names and keywords
        concepts = self.db.query(EducationalConcept).filter(
            EducationalConcept.is_active == True
        ).all()

        found_concepts = []
        text_lower = text.lower()

        for concept in concepts:
            # Check if concept name is mentioned
            if concept.name.lower() in text_lower:
                found_concepts.append(concept.name)
                continue

            # Check keywords
            if concept.keywords:
                keywords = [k.strip().lower() for k in concept.keywords.split(',')]
                for keyword in keywords:
                    if keyword in text_lower:
                        found_concepts.append(concept.name)
                        break

        return list(set(found_concepts))  # Remove duplicates

    async def get_learning_path_suggestions(
        self, 
        user_level: DifficultyLevel,
        interests: List[ConceptType] = None
    ) -> List[str]:
        """Get learning path suggestions based on user level and interests"""
        suggestions = []

        if user_level == DifficultyLevel.BEGINNER:
            suggestions = [
                "Start with basic market concepts like Market Capitalization",
                "Learn fundamental ratios: P/E Ratio, ROE, and Debt-to-Equity",
                "Understand simple technical indicators: Moving Averages and RSI",
                "Practice reading stock charts and identifying trends"
            ]
        elif user_level == DifficultyLevel.INTERMEDIATE:
            suggestions = [
                "Master advanced technical indicators: MACD, Bollinger Bands",
                "Learn sector analysis and industry comparisons",
                "Study risk management and position sizing",
                "Understand earnings analysis and financial statements"
            ]
        else:  # Advanced
            suggestions = [
                "Develop custom trading strategies and backtesting",
                "Study options strategies and derivatives",
                "Learn quantitative analysis and statistical methods",
                "Master portfolio theory and asset allocation"
            ]

        return suggestions

    async def track_user_progress(
        self, 
        user_id: int, 
        concept_id: int, 
        completed: bool = True,
        difficulty_rating: Optional[int] = None
    ) -> UserLearningProgressResponse:
        """Track user learning progress"""
        # Check if progress already exists
        progress = self.db.query(UserLearningProgress).filter(
            and_(
                UserLearningProgress.user_id == user_id,
                UserLearningProgress.concept_id == concept_id
            )
        ).first()

        if progress:
            progress.is_completed = completed
            if difficulty_rating:
                progress.difficulty_rating = difficulty_rating
            if completed:
                progress.completion_date = datetime.utcnow()
        else:
            progress = UserLearningProgress(
                user_id=user_id,
                concept_id=concept_id,
                is_completed=completed,
                difficulty_rating=difficulty_rating,
                completion_date=datetime.utcnow() if completed else None
            )
            self.db.add(progress)

        self.db.commit()
        self.db.refresh(progress)

        return UserLearningProgressResponse.from_orm(progress)

    async def get_user_progress(self, user_id: int) -> List[UserLearningProgressResponse]:
        """Get user's learning progress"""
        progress_records = self.db.query(UserLearningProgress).filter(
            UserLearningProgress.user_id == user_id
        ).all()

        return [UserLearningProgressResponse.from_orm(record) for record in progress_records]