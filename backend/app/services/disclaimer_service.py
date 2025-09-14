"""
Disclaimer Service

Backend service for managing disclaimers and risk warnings in API responses.
"""

from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel


class DisclaimerContext(str, Enum):
    CHAT_RESPONSE = "chat_response"
    ANALYSIS_RESULT = "analysis_result"
    RECOMMENDATION = "recommendation"
    BACKTEST = "backtest"
    EXPORT = "export"
    SHARED_ANALYSIS = "shared_analysis"
    WATCHLIST = "watchlist"
    ALERT = "alert"


class DisclaimerSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class DisclaimerConfig(BaseModel):
    id: str
    title: str
    content: str
    severity: DisclaimerSeverity
    required: bool
    contexts: List[DisclaimerContext]


class DisclaimerService:
    """Service for managing disclaimers and risk warnings."""
    
    def __init__(self):
        self.disclaimers = [
            DisclaimerConfig(
                id="investment_advice",
                title="Investment Disclaimer",
                content=(
                    "This application provides information and analysis for educational purposes only "
                    "and does not constitute investment advice, financial advice, trading advice, or "
                    "any other sort of advice. The information provided should not be relied upon as "
                    "a substitute for extensive independent market research before making your investment "
                    "decisions. All investments carry risk of loss, and you may lose some or all of your "
                    "investment. Past performance does not guarantee future results."
                ),
                severity=DisclaimerSeverity.WARNING,
                required=True,
                contexts=[
                    DisclaimerContext.CHAT_RESPONSE,
                    DisclaimerContext.ANALYSIS_RESULT,
                    DisclaimerContext.RECOMMENDATION,
                    DisclaimerContext.EXPORT,
                    DisclaimerContext.SHARED_ANALYSIS
                ]
            ),
            DisclaimerConfig(
                id="data_accuracy",
                title="Data Accuracy Disclaimer",
                content=(
                    "The data and information provided in this application is obtained from sources "
                    "believed to be reliable, but we cannot guarantee its accuracy, completeness, or "
                    "timeliness. Market data may be delayed, and real-time quotes may not be available. "
                    "Users should verify all information independently before making investment decisions."
                ),
                severity=DisclaimerSeverity.INFO,
                required=False,
                contexts=[
                    DisclaimerContext.ANALYSIS_RESULT,
                    DisclaimerContext.EXPORT,
                    DisclaimerContext.SHARED_ANALYSIS,
                    DisclaimerContext.CHAT_RESPONSE
                ]
            ),
            DisclaimerConfig(
                id="risk_warning",
                title="Risk Warning",
                content=(
                    "Trading and investing in stocks, securities, and financial instruments involves "
                    "substantial risk of loss and is not suitable for all investors. Stock prices can "
                    "be extremely volatile and unpredictable. You should carefully consider your "
                    "investment objectives, level of experience, and risk appetite before making any "
                    "investment decisions. Never invest money you cannot afford to lose."
                ),
                severity=DisclaimerSeverity.ERROR,
                required=True,
                contexts=[
                    DisclaimerContext.RECOMMENDATION,
                    DisclaimerContext.ANALYSIS_RESULT,
                    DisclaimerContext.BACKTEST
                ]
            ),
            DisclaimerConfig(
                id="ai_limitations",
                title="AI Analysis Limitations",
                content=(
                    "This application uses artificial intelligence and automated analysis tools. "
                    "AI-generated content may contain errors, biases, or inaccuracies. The analysis "
                    "is based on historical data and patterns, which may not predict future market "
                    "behavior. Always conduct your own research and consult with qualified financial "
                    "professionals before making investment decisions."
                ),
                severity=DisclaimerSeverity.WARNING,
                required=True,
                contexts=[
                    DisclaimerContext.CHAT_RESPONSE,
                    DisclaimerContext.ANALYSIS_RESULT,
                    DisclaimerContext.RECOMMENDATION
                ]
            ),
            DisclaimerConfig(
                id="backtesting_limitations",
                title="Backtesting Disclaimer",
                content=(
                    "Backtesting results are hypothetical and do not represent actual trading. "
                    "Past performance shown in backtests does not guarantee future results. "
                    "Backtesting may not account for market impact, liquidity constraints, "
                    "transaction costs, slippage, or other real-world trading conditions. "
                    "Actual trading results may differ significantly from backtested results."
                ),
                severity=DisclaimerSeverity.WARNING,
                required=True,
                contexts=[DisclaimerContext.BACKTEST]
            ),
            DisclaimerConfig(
                id="market_volatility",
                title="Market Volatility Warning",
                content=(
                    "Financial markets are subject to extreme volatility and unpredictable events. "
                    "Market conditions can change rapidly, and investments can lose value quickly. "
                    "Economic events, geopolitical situations, and market sentiment can significantly "
                    "impact investment performance in ways that cannot be predicted or modeled."
                ),
                severity=DisclaimerSeverity.ERROR,
                required=True,
                contexts=[
                    DisclaimerContext.RECOMMENDATION,
                    DisclaimerContext.ANALYSIS_RESULT
                ]
            )
        ]
    
    def get_disclaimers_for_context(self, context: DisclaimerContext) -> List[DisclaimerConfig]:
        """Get all disclaimers applicable to a specific context."""
        return [d for d in self.disclaimers if context in d.contexts]
    
    def get_required_disclaimers_for_context(self, context: DisclaimerContext) -> List[DisclaimerConfig]:
        """Get required disclaimers for a specific context."""
        return [d for d in self.disclaimers if context in d.contexts and d.required]
    
    def generate_disclaimer_text(self, context: DisclaimerContext, compact: bool = False) -> str:
        """Generate disclaimer text for embedding in responses."""
        disclaimers = self.get_required_disclaimers_for_context(context)
        
        if not disclaimers:
            return ""
        
        if compact:
            return "⚠️ Important: This is for informational purposes only and not investment advice. All investments carry risk of loss."
        
        disclaimer_texts = [f"**{d.title}:** {d.content}" for d in disclaimers]
        return f"\n\n---\n**IMPORTANT DISCLAIMERS:**\n\n{chr(10).join(disclaimer_texts)}"
    
    def should_show_high_risk_disclaimer(self, risk_level: Optional[str] = None, volatility: Optional[float] = None) -> bool:
        """Determine if high-risk disclaimer should be shown."""
        if risk_level and risk_level.upper() in ['HIGH', 'VERY_HIGH']:
            return True
        
        if volatility and volatility > 0.3:  # 30% volatility threshold
            return True
        
        return False
    
    def get_high_risk_disclaimer_text(self, symbol: Optional[str] = None) -> str:
        """Get high-risk specific disclaimer text."""
        symbol_text = f" ({symbol})" if symbol else ""
        return (
            f"⚠️ **HIGH RISK WARNING{symbol_text}:** This investment has been identified as high risk "
            "due to high volatility or other risk factors. You may lose some or all of your investment. "
            "Only invest what you can afford to lose. Please exercise extreme caution and consider "
            "consulting with a qualified financial advisor."
        )
    
    def add_disclaimers_to_response(
        self, 
        response_text: str, 
        context: DisclaimerContext,
        risk_level: Optional[str] = None,
        volatility: Optional[float] = None,
        symbol: Optional[str] = None,
        compact: bool = True
    ) -> str:
        """Add appropriate disclaimers to a response text."""
        disclaimer_text = self.generate_disclaimer_text(context, compact)
        
        # Add high-risk disclaimer if applicable
        if self.should_show_high_risk_disclaimer(risk_level, volatility):
            high_risk_text = self.get_high_risk_disclaimer_text(symbol)
            if compact:
                disclaimer_text = high_risk_text
            else:
                disclaimer_text = f"{disclaimer_text}\n\n{high_risk_text}"
        
        if disclaimer_text:
            return f"{response_text}\n\n{disclaimer_text}"
        
        return response_text
    
    def get_disclaimer_metadata(self, context: DisclaimerContext) -> Dict[str, Any]:
        """Get disclaimer metadata for API responses."""
        disclaimers = self.get_disclaimers_for_context(context)
        required_disclaimers = self.get_required_disclaimers_for_context(context)
        
        return {
            "disclaimers": [
                {
                    "id": d.id,
                    "title": d.title,
                    "severity": d.severity.value,
                    "required": d.required
                }
                for d in disclaimers
            ],
            "required_count": len(required_disclaimers),
            "total_count": len(disclaimers)
        }


# Global instance
disclaimer_service = DisclaimerService()