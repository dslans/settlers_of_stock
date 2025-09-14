"""
Tests for Disclaimer Service
"""

import pytest
from app.services.disclaimer_service import disclaimer_service, DisclaimerContext, DisclaimerSeverity


class TestDisclaimerService:
    """Test cases for DisclaimerService"""

    def test_get_disclaimers_for_context_chat_response(self):
        """Test getting disclaimers for chat response context"""
        disclaimers = disclaimer_service.get_disclaimers_for_context(DisclaimerContext.CHAT_RESPONSE)
        
        assert len(disclaimers) > 0
        assert any(d.id == "investment_advice" for d in disclaimers)
        assert any(d.id == "ai_limitations" for d in disclaimers)

    def test_get_disclaimers_for_context_recommendation(self):
        """Test getting disclaimers for recommendation context"""
        disclaimers = disclaimer_service.get_disclaimers_for_context(DisclaimerContext.RECOMMENDATION)
        
        assert len(disclaimers) > 0
        assert any(d.id == "investment_advice" for d in disclaimers)
        assert any(d.id == "risk_warning" for d in disclaimers)
        assert any(d.id == "market_volatility" for d in disclaimers)

    def test_get_disclaimers_for_context_backtest(self):
        """Test getting disclaimers for backtest context"""
        disclaimers = disclaimer_service.get_disclaimers_for_context(DisclaimerContext.BACKTEST)
        
        assert len(disclaimers) > 0
        assert any(d.id == "backtesting_limitations" for d in disclaimers)
        assert any(d.id == "risk_warning" for d in disclaimers)

    def test_get_required_disclaimers_for_context(self):
        """Test getting only required disclaimers"""
        all_disclaimers = disclaimer_service.get_disclaimers_for_context(DisclaimerContext.RECOMMENDATION)
        required_disclaimers = disclaimer_service.get_required_disclaimers_for_context(DisclaimerContext.RECOMMENDATION)
        
        assert len(required_disclaimers) <= len(all_disclaimers)
        assert all(d.required for d in required_disclaimers)

    def test_generate_disclaimer_text_compact(self):
        """Test generating compact disclaimer text"""
        text = disclaimer_service.generate_disclaimer_text(DisclaimerContext.CHAT_RESPONSE, compact=True)
        
        assert "⚠️ Important" in text
        assert "informational purposes only" in text
        assert "not investment advice" in text

    def test_generate_disclaimer_text_full(self):
        """Test generating full disclaimer text"""
        text = disclaimer_service.generate_disclaimer_text(DisclaimerContext.RECOMMENDATION, compact=False)
        
        assert "IMPORTANT DISCLAIMERS" in text
        assert "Investment Disclaimer" in text
        assert "Risk Warning" in text

    def test_generate_disclaimer_text_empty_context(self):
        """Test generating disclaimer text for context with no disclaimers"""
        # Create a context that doesn't exist in any disclaimer
        text = disclaimer_service.generate_disclaimer_text(DisclaimerContext.WATCHLIST, compact=False)
        
        assert text == ""

    def test_should_show_high_risk_disclaimer_high_level(self):
        """Test high risk disclaimer for HIGH risk level"""
        should_show = disclaimer_service.should_show_high_risk_disclaimer(risk_level="HIGH")
        assert should_show is True

    def test_should_show_high_risk_disclaimer_very_high_level(self):
        """Test high risk disclaimer for VERY_HIGH risk level"""
        should_show = disclaimer_service.should_show_high_risk_disclaimer(risk_level="VERY_HIGH")
        assert should_show is True

    def test_should_show_high_risk_disclaimer_low_level(self):
        """Test high risk disclaimer for LOW risk level"""
        should_show = disclaimer_service.should_show_high_risk_disclaimer(risk_level="LOW")
        assert should_show is False

    def test_should_show_high_risk_disclaimer_high_volatility(self):
        """Test high risk disclaimer for high volatility"""
        should_show = disclaimer_service.should_show_high_risk_disclaimer(volatility=0.4)
        assert should_show is True

    def test_should_show_high_risk_disclaimer_low_volatility(self):
        """Test high risk disclaimer for low volatility"""
        should_show = disclaimer_service.should_show_high_risk_disclaimer(volatility=0.1)
        assert should_show is False

    def test_should_show_high_risk_disclaimer_no_indicators(self):
        """Test high risk disclaimer with no risk indicators"""
        should_show = disclaimer_service.should_show_high_risk_disclaimer()
        assert should_show is False

    def test_get_high_risk_disclaimer_text_with_symbol(self):
        """Test high risk disclaimer text with symbol"""
        text = disclaimer_service.get_high_risk_disclaimer_text(symbol="TSLA")
        
        assert "HIGH RISK WARNING (TSLA)" in text
        assert "high risk" in text.lower()
        assert "lose some or all" in text.lower()

    def test_get_high_risk_disclaimer_text_without_symbol(self):
        """Test high risk disclaimer text without symbol"""
        text = disclaimer_service.get_high_risk_disclaimer_text()
        
        assert "HIGH RISK WARNING:" in text
        assert "high risk" in text.lower()
        assert "lose some or all" in text.lower()

    def test_add_disclaimers_to_response_normal(self):
        """Test adding disclaimers to normal response"""
        original_response = "AAPL looks like a good investment based on fundamentals."
        
        response_with_disclaimers = disclaimer_service.add_disclaimers_to_response(
            original_response,
            DisclaimerContext.RECOMMENDATION,
            compact=True
        )
        
        assert original_response in response_with_disclaimers
        assert "⚠️ Important" in response_with_disclaimers
        assert "not investment advice" in response_with_disclaimers

    def test_add_disclaimers_to_response_high_risk(self):
        """Test adding disclaimers to high risk response"""
        original_response = "This volatile stock might be worth considering."
        
        response_with_disclaimers = disclaimer_service.add_disclaimers_to_response(
            original_response,
            DisclaimerContext.RECOMMENDATION,
            risk_level="HIGH",
            symbol="VOLATILE",
            compact=True
        )
        
        assert original_response in response_with_disclaimers
        assert "HIGH RISK WARNING (VOLATILE)" in response_with_disclaimers

    def test_add_disclaimers_to_response_no_disclaimers(self):
        """Test adding disclaimers when none are applicable"""
        original_response = "Here's some general market information."
        
        response_with_disclaimers = disclaimer_service.add_disclaimers_to_response(
            original_response,
            DisclaimerContext.WATCHLIST,  # Context with no disclaimers
            compact=True
        )
        
        assert response_with_disclaimers == original_response

    def test_get_disclaimer_metadata(self):
        """Test getting disclaimer metadata"""
        metadata = disclaimer_service.get_disclaimer_metadata(DisclaimerContext.RECOMMENDATION)
        
        assert "disclaimers" in metadata
        assert "required_count" in metadata
        assert "total_count" in metadata
        assert isinstance(metadata["disclaimers"], list)
        assert metadata["required_count"] <= metadata["total_count"]
        
        # Check disclaimer structure
        if metadata["disclaimers"]:
            disclaimer = metadata["disclaimers"][0]
            assert "id" in disclaimer
            assert "title" in disclaimer
            assert "severity" in disclaimer
            assert "required" in disclaimer

    def test_disclaimer_severities(self):
        """Test that disclaimers have appropriate severities"""
        disclaimers = disclaimer_service.get_disclaimers_for_context(DisclaimerContext.RECOMMENDATION)
        
        # Check that we have different severity levels
        severities = {d.severity for d in disclaimers}
        assert len(severities) > 1  # Should have multiple severity levels
        
        # Check that risk warning has error severity
        risk_warning = next((d for d in disclaimers if d.id == "risk_warning"), None)
        assert risk_warning is not None
        assert risk_warning.severity == DisclaimerSeverity.ERROR

    def test_disclaimer_contexts(self):
        """Test that disclaimers are properly assigned to contexts"""
        # Investment advice should be in multiple contexts
        investment_disclaimer = next(
            (d for d in disclaimer_service.disclaimers if d.id == "investment_advice"), 
            None
        )
        assert investment_disclaimer is not None
        assert DisclaimerContext.CHAT_RESPONSE in investment_disclaimer.contexts
        assert DisclaimerContext.RECOMMENDATION in investment_disclaimer.contexts
        
        # Backtesting disclaimer should only be in backtest context
        backtest_disclaimer = next(
            (d for d in disclaimer_service.disclaimers if d.id == "backtesting_limitations"), 
            None
        )
        assert backtest_disclaimer is not None
        assert DisclaimerContext.BACKTEST in backtest_disclaimer.contexts

    def test_disclaimer_content_quality(self):
        """Test that disclaimer content meets quality standards"""
        for disclaimer in disclaimer_service.disclaimers:
            # Content should not be empty
            assert disclaimer.content.strip() != ""
            
            # Content should be reasonably long (more than just a sentence)
            assert len(disclaimer.content) > 50
            
            # Title should not be empty
            assert disclaimer.title.strip() != ""
            
            # Should have at least one context
            assert len(disclaimer.contexts) > 0

    @pytest.mark.parametrize("context", [
        DisclaimerContext.CHAT_RESPONSE,
        DisclaimerContext.ANALYSIS_RESULT,
        DisclaimerContext.RECOMMENDATION,
        DisclaimerContext.BACKTEST,
    ])
    def test_all_contexts_have_disclaimers(self, context):
        """Test that all major contexts have at least one disclaimer"""
        disclaimers = disclaimer_service.get_disclaimers_for_context(context)
        assert len(disclaimers) > 0, f"Context {context} should have at least one disclaimer"

    def test_compact_vs_full_disclaimer_text(self):
        """Test difference between compact and full disclaimer text"""
        compact_text = disclaimer_service.generate_disclaimer_text(
            DisclaimerContext.RECOMMENDATION, compact=True
        )
        full_text = disclaimer_service.generate_disclaimer_text(
            DisclaimerContext.RECOMMENDATION, compact=False
        )
        
        # Compact should be shorter
        assert len(compact_text) < len(full_text)
        
        # Full text should contain more detailed information
        assert "IMPORTANT DISCLAIMERS" in full_text
        assert "IMPORTANT DISCLAIMERS" not in compact_text