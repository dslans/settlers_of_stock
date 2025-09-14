"""
Export and sharing API endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Response
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any
import logging
from io import BytesIO

from ..services.export_service import export_service
from ..services.analysis_engine import analysis_engine
from ..services.sentiment_analyzer import sentiment_analyzer
from ..models.analysis import AnalysisResult
from ..models.sentiment import SentimentAnalysisResult
from ..core.dependencies import get_current_user
from ..models.user import User
from pydantic import BaseModel

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/export", tags=["export"])


class ShareLinkRequest(BaseModel):
    """Request model for creating shareable links."""
    symbol: str
    include_sentiment: bool = True
    expires_in_hours: int = 24


class ShareLinkResponse(BaseModel):
    """Response model for shareable links."""
    link_id: str
    share_url: str
    expires_at: str
    created_at: str


class ExportRequest(BaseModel):
    """Request model for exports."""
    symbol: str
    format: str = "pdf"  # pdf, csv, json
    include_sentiment: bool = True
    include_charts: bool = True


@router.post("/pdf/{symbol}")
async def export_pdf_report(
    symbol: str,
    include_sentiment: bool = Query(True, description="Include sentiment analysis in report"),
    include_charts: bool = Query(True, description="Include charts in report"),
    current_user: User = Depends(get_current_user)
):
    """
    Export stock analysis as PDF report.
    
    Args:
        symbol: Stock ticker symbol
        include_sentiment: Whether to include sentiment analysis
        include_charts: Whether to include charts
        current_user: Current authenticated user
        
    Returns:
        PDF file as streaming response
    """
    try:
        logger.info(f"User {current_user.email} requested PDF export for {symbol}")
        
        # Validate symbol
        symbol = symbol.upper().strip()
        if not symbol or len(symbol) > 10:
            raise HTTPException(
                status_code=400,
                detail="Invalid stock symbol format"
            )
        
        # Get analysis data
        analysis_result = await analysis_engine.analyze_stock(symbol)
        
        # Get sentiment data if requested
        sentiment_result = None
        if include_sentiment:
            try:
                sentiment_result = await sentiment_analyzer.analyze_stock_sentiment(symbol)
            except Exception as e:
                logger.warning(f"Could not get sentiment data for {symbol}: {e}")
        
        # Generate PDF
        pdf_bytes = await export_service.generate_pdf_report(
            analysis_result=analysis_result,
            sentiment_result=sentiment_result,
            include_charts=include_charts,
            user_id=current_user.id
        )
        
        # Create filename
        filename = f"{symbol}_analysis_report_{analysis_result.analysis_timestamp.strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Return as streaming response
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting PDF for {symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate PDF report"
        )


@router.post("/csv/{symbol}")
async def export_csv_data(
    symbol: str,
    include_sentiment: bool = Query(True, description="Include sentiment analysis in export"),
    current_user: User = Depends(get_current_user)
):
    """
    Export stock analysis data as CSV.
    
    Args:
        symbol: Stock ticker symbol
        include_sentiment: Whether to include sentiment analysis
        current_user: Current authenticated user
        
    Returns:
        CSV file as streaming response
    """
    try:
        logger.info(f"User {current_user.email} requested CSV export for {symbol}")
        
        # Validate symbol
        symbol = symbol.upper().strip()
        if not symbol or len(symbol) > 10:
            raise HTTPException(
                status_code=400,
                detail="Invalid stock symbol format"
            )
        
        # Get analysis data
        analysis_result = await analysis_engine.analyze_stock(symbol)
        
        # Get sentiment data if requested
        sentiment_result = None
        if include_sentiment:
            try:
                sentiment_result = await sentiment_analyzer.analyze_stock_sentiment(symbol)
            except Exception as e:
                logger.warning(f"Could not get sentiment data for {symbol}: {e}")
        
        # Generate CSV
        csv_content = await export_service.export_data_csv(
            analysis_result=analysis_result,
            sentiment_result=sentiment_result
        )
        
        # Create filename
        filename = f"{symbol}_analysis_data_{analysis_result.analysis_timestamp.strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Return as streaming response
        return StreamingResponse(
            BytesIO(csv_content.encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting CSV for {symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate CSV export"
        )


@router.post("/json/{symbol}")
async def export_json_data(
    symbol: str,
    include_sentiment: bool = Query(True, description="Include sentiment analysis in export"),
    include_metadata: bool = Query(True, description="Include export metadata"),
    current_user: User = Depends(get_current_user)
):
    """
    Export stock analysis data as JSON.
    
    Args:
        symbol: Stock ticker symbol
        include_sentiment: Whether to include sentiment analysis
        include_metadata: Whether to include export metadata
        current_user: Current authenticated user
        
    Returns:
        JSON file as streaming response
    """
    try:
        logger.info(f"User {current_user.email} requested JSON export for {symbol}")
        
        # Validate symbol
        symbol = symbol.upper().strip()
        if not symbol or len(symbol) > 10:
            raise HTTPException(
                status_code=400,
                detail="Invalid stock symbol format"
            )
        
        # Get analysis data
        analysis_result = await analysis_engine.analyze_stock(symbol)
        
        # Get sentiment data if requested
        sentiment_result = None
        if include_sentiment:
            try:
                sentiment_result = await sentiment_analyzer.analyze_stock_sentiment(symbol)
            except Exception as e:
                logger.warning(f"Could not get sentiment data for {symbol}: {e}")
        
        # Generate JSON
        json_content = await export_service.export_data_json(
            analysis_result=analysis_result,
            sentiment_result=sentiment_result,
            include_metadata=include_metadata
        )
        
        # Create filename
        filename = f"{symbol}_analysis_data_{analysis_result.analysis_timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        
        # Return as streaming response
        return StreamingResponse(
            BytesIO(json_content.encode('utf-8')),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting JSON for {symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate JSON export"
        )


@router.post("/share", response_model=ShareLinkResponse)
async def create_share_link(
    request: ShareLinkRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create a shareable link for analysis results.
    
    Args:
        request: Share link request parameters
        current_user: Current authenticated user
        
    Returns:
        ShareLinkResponse with link details
    """
    try:
        logger.info(f"User {current_user.email} creating share link for {request.symbol}")
        
        # Validate symbol
        symbol = request.symbol.upper().strip()
        if not symbol or len(symbol) > 10:
            raise HTTPException(
                status_code=400,
                detail="Invalid stock symbol format"
            )
        
        # Validate expiration time
        if request.expires_in_hours < 1 or request.expires_in_hours > 168:  # Max 1 week
            raise HTTPException(
                status_code=400,
                detail="Expiration time must be between 1 and 168 hours"
            )
        
        # Get analysis data
        analysis_result = await analysis_engine.analyze_stock(symbol)
        
        # Get sentiment data if requested
        sentiment_result = None
        if request.include_sentiment:
            try:
                sentiment_result = await sentiment_analyzer.analyze_stock_sentiment(symbol)
            except Exception as e:
                logger.warning(f"Could not get sentiment data for {symbol}: {e}")
        
        # Create shareable link
        link_id = await export_service.create_shareable_link(
            analysis_result=analysis_result,
            sentiment_result=sentiment_result,
            user_id=current_user.id,
            expires_in_hours=request.expires_in_hours
        )
        
        # Create response
        from datetime import datetime, timedelta
        
        response = ShareLinkResponse(
            link_id=link_id,
            share_url=f"/share/{link_id}",  # Frontend will handle full URL
            expires_at=(datetime.now() + timedelta(hours=request.expires_in_hours)).isoformat(),
            created_at=datetime.now().isoformat()
        )
        
        logger.info(f"Created share link {link_id} for {symbol}")
        return response
        
    except Exception as e:
        logger.error(f"Error creating share link for {request.symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create shareable link"
        )


@router.get("/share/{link_id}")
async def get_shared_analysis(link_id: str):
    """
    Get shared analysis by link ID.
    
    Args:
        link_id: Shareable link ID
        
    Returns:
        Shared analysis data
    """
    try:
        logger.info(f"Retrieving shared analysis {link_id}")
        
        # Get shared data
        share_data = await export_service.get_shared_analysis(link_id)
        
        if not share_data:
            raise HTTPException(
                status_code=404,
                detail="Shared link not found or expired"
            )
        
        # Return the data (view count is automatically incremented)
        return {
            "analysis": share_data["analysis"],
            "sentiment": share_data["sentiment"],
            "created_at": share_data["created_at"],
            "view_count": share_data["view_count"],
            "expires_at": share_data["expires_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving shared analysis {link_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve shared analysis"
        )


@router.delete("/share/{link_id}")
async def delete_share_link(
    link_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a shareable link.
    
    Args:
        link_id: Shareable link ID
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    try:
        logger.info(f"User {current_user.email} deleting share link {link_id}")
        
        # Delete the link
        deleted = await export_service.delete_shared_link(link_id, current_user.id)
        
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail="Shared link not found or you don't have permission to delete it"
            )
        
        return {"message": "Shared link deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting share link {link_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete shared link"
        )


@router.get("/user/exports")
async def get_user_exports(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of exports to return"),
    current_user: User = Depends(get_current_user)
):
    """
    Get user's recent exports.
    
    Args:
        limit: Maximum number of exports to return
        current_user: Current authenticated user
        
    Returns:
        List of user's exports
    """
    try:
        logger.info(f"Getting exports for user {current_user.email}")
        
        # Get user exports
        exports = await export_service.get_user_exports(current_user.id, limit)
        
        return {
            "exports": exports,
            "total": len(exports)
        }
        
    except Exception as e:
        logger.error(f"Error getting user exports: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user exports"
        )


@router.get("/formats")
async def get_export_formats():
    """
    Get available export formats.
    
    Returns:
        List of available export formats
    """
    return {
        "formats": [
            {
                "format": "pdf",
                "name": "PDF Report",
                "description": "Comprehensive analysis report with charts and formatting",
                "mime_type": "application/pdf",
                "supports_charts": True
            },
            {
                "format": "csv",
                "name": "CSV Data",
                "description": "Raw analysis data in comma-separated values format",
                "mime_type": "text/csv",
                "supports_charts": False
            },
            {
                "format": "json",
                "name": "JSON Data",
                "description": "Structured analysis data in JSON format",
                "mime_type": "application/json",
                "supports_charts": False
            }
        ]
    }


@router.get("/health")
async def health_check():
    """
    Health check endpoint for the export service.
    
    Returns:
        dict: Service health status
    """
    try:
        return {
            "status": "healthy",
            "service": "export_service",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Export service health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Export service unavailable"
        )