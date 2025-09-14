"""
Export and sharing service for analysis results.
"""

import os
import uuid
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path
from io import BytesIO
import base64

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus.flowables import Image as ReportLabImage
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from jinja2 import Template
import redis
from google.cloud import storage

from ..models.analysis import AnalysisResult, PriceTarget
from ..models.sentiment import SentimentAnalysisResult
from ..core.config import get_settings

# Configure logging
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()


class ExportService:
    """Service for exporting and sharing analysis results."""
    
    def __init__(self):
        """Initialize export service."""
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )
        
        # Initialize Google Cloud Storage if configured
        self.storage_client = None
        if settings.GCP_PROJECT_ID:
            try:
                self.storage_client = storage.Client(project=settings.GCP_PROJECT_ID)
                self.bucket_name = f"{settings.GCP_PROJECT_ID}-exports"
            except Exception as e:
                logger.warning(f"Could not initialize GCS client: {e}")
        
        # Create local export directory
        self.local_export_dir = Path("exports")
        self.local_export_dir.mkdir(exist_ok=True)
    
    async def generate_pdf_report(
        self,
        analysis_result: AnalysisResult,
        sentiment_result: Optional[SentimentAnalysisResult] = None,
        include_charts: bool = True,
        user_id: Optional[str] = None
    ) -> bytes:
        """
        Generate PDF report from analysis results.
        
        Args:
            analysis_result: Stock analysis results
            sentiment_result: Optional sentiment analysis results
            include_charts: Whether to include charts in the report
            user_id: User ID for tracking
            
        Returns:
            bytes: PDF content as bytes
        """
        try:
            logger.info(f"Generating PDF report for {analysis_result.symbol}")
            
            # Create PDF buffer
            buffer = BytesIO()
            
            # Create PDF document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Get styles
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                textColor=HexColor('#1976d2'),
                alignment=TA_CENTER
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=12,
                textColor=HexColor('#1976d2'),
                borderWidth=1,
                borderColor=HexColor('#1976d2'),
                borderPadding=5
            )
            
            # Build story (content)
            story = []
            
            # Title
            story.append(Paragraph(f"Stock Analysis Report: {analysis_result.symbol}", title_style))
            story.append(Spacer(1, 12))
            
            # Report metadata
            metadata_data = [
                ['Report Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')],
                ['Analysis Date:', analysis_result.analysis_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')],
                ['Analysis Type:', analysis_result.analysis_type.value.title()],
                ['Data Sources:', 'yfinance, NewsAPI, Reddit API, SEC EDGAR']
            ]
            
            metadata_table = Table(metadata_data, colWidths=[2*inch, 4*inch])
            metadata_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f5f5f5')),
                ('TEXTCOLOR', (0, 0), (-1, -1), black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, black)
            ]))
            
            story.append(metadata_table)
            story.append(Spacer(1, 20))
            
            # Executive Summary
            story.append(Paragraph("Executive Summary", heading_style))
            
            summary_data = [
                ['Recommendation:', analysis_result.recommendation.value],
                ['Confidence:', f"{analysis_result.confidence}%"],
                ['Overall Score:', f"{analysis_result.overall_score}/100"],
                ['Risk Level:', analysis_result.risk_level.value],
                ['Summary:', analysis_result.get_recommendation_summary()]
            ]
            
            summary_table = Table(summary_data, colWidths=[1.5*inch, 4.5*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), HexColor('#e3f2fd')),
                ('BACKGROUND', (1, 0), (1, -1), white),
                ('TEXTCOLOR', (0, 0), (-1, -1), black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, black)
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 20))
            
            # Price Targets
            if analysis_result.price_targets:
                story.append(Paragraph("Price Targets", heading_style))
                
                target_data = [['Timeframe', 'Target Price', 'Confidence', 'Rationale']]
                for target in analysis_result.price_targets:
                    target_data.append([
                        target.timeframe,
                        f"${target.target:.2f}",
                        f"{target.confidence}%",
                        target.rationale[:50] + "..." if len(target.rationale) > 50 else target.rationale
                    ])
                
                target_table = Table(target_data, colWidths=[1*inch, 1*inch, 1*inch, 3*inch])
                target_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1976d2')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('GRID', (0, 0), (-1, -1), 1, black)
                ]))
                
                story.append(target_table)
                story.append(Spacer(1, 20))
            
            # Strengths and Weaknesses
            story.append(Paragraph("Analysis Details", heading_style))
            
            if analysis_result.strengths:
                story.append(Paragraph("<b>Key Strengths:</b>", styles['Normal']))
                for strength in analysis_result.strengths:
                    story.append(Paragraph(f"• {strength}", styles['Normal']))
                story.append(Spacer(1, 10))
            
            if analysis_result.weaknesses:
                story.append(Paragraph("<b>Key Weaknesses:</b>", styles['Normal']))
                for weakness in analysis_result.weaknesses:
                    story.append(Paragraph(f"• {weakness}", styles['Normal']))
                story.append(Spacer(1, 10))
            
            if analysis_result.risks:
                story.append(Paragraph("<b>Risk Factors:</b>", styles['Normal']))
                for risk in analysis_result.risks:
                    story.append(Paragraph(f"• {risk}", styles['Normal']))
                story.append(Spacer(1, 10))
            
            if analysis_result.opportunities:
                story.append(Paragraph("<b>Opportunities:</b>", styles['Normal']))
                for opportunity in analysis_result.opportunities:
                    story.append(Paragraph(f"• {opportunity}", styles['Normal']))
                story.append(Spacer(1, 20))
            
            # Sentiment Analysis (if provided)
            if sentiment_result:
                story.append(Paragraph("Sentiment Analysis", heading_style))
                
                sentiment_data = [
                    ['Overall Sentiment:', f"{sentiment_result.sentiment_data.overall_sentiment:.2f}"],
                    ['News Sentiment:', f"{sentiment_result.sentiment_data.news_sentiment:.2f}"],
                    ['Social Sentiment:', f"{sentiment_result.sentiment_data.social_sentiment:.2f}"],
                    ['Trend Direction:', sentiment_result.sentiment_data.trend_direction.value],
                    ['Confidence:', f"{sentiment_result.sentiment_data.confidence_score:.2f}"]
                ]
                
                sentiment_table = Table(sentiment_data, colWidths=[2*inch, 4*inch])
                sentiment_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), HexColor('#e8f5e8')),
                    ('BACKGROUND', (1, 0), (1, -1), white),
                    ('TEXTCOLOR', (0, 0), (-1, -1), black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('GRID', (0, 0), (-1, -1), 1, black)
                ]))
                
                story.append(sentiment_table)
                story.append(Spacer(1, 20))
            
            # Disclaimer
            story.append(PageBreak())
            story.append(Paragraph("Important Disclaimers", heading_style))
            
            disclaimer_text = """
            <b>Investment Disclaimer:</b> This report is for informational purposes only and does not constitute investment advice. 
            Past performance does not guarantee future results. All investments carry risk of loss. 
            Please consult with a qualified financial advisor before making investment decisions.
            
            <b>Data Sources:</b> This analysis is based on publicly available data from various sources including 
            yfinance, NewsAPI, Reddit, and SEC filings. Data accuracy cannot be guaranteed.
            
            <b>Limitations:</b> This analysis is automated and may not capture all relevant factors. 
            Market conditions can change rapidly, making this analysis outdated quickly.
            
            <b>Risk Warning:</b> Stock prices can be volatile and unpredictable. You may lose some or all of your investment. 
            Never invest more than you can afford to lose.
            """
            
            story.append(Paragraph(disclaimer_text, styles['Normal']))
            
            # Build PDF
            doc.build(story)
            
            # Get PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            logger.info(f"PDF report generated successfully for {analysis_result.symbol}")
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            raise
    
    async def create_shareable_link(
        self,
        analysis_result: AnalysisResult,
        sentiment_result: Optional[SentimentAnalysisResult] = None,
        user_id: Optional[str] = None,
        expires_in_hours: int = 24
    ) -> str:
        """
        Create a shareable link for analysis results.
        
        Args:
            analysis_result: Stock analysis results
            sentiment_result: Optional sentiment analysis results
            user_id: User ID for tracking
            expires_in_hours: Link expiration time in hours
            
        Returns:
            str: Shareable link ID
        """
        try:
            # Generate unique link ID
            link_id = str(uuid.uuid4())
            
            # Prepare data for sharing
            share_data = {
                "analysis": analysis_result.dict(),
                "sentiment": sentiment_result.dict() if sentiment_result else None,
                "created_at": datetime.now().isoformat(),
                "created_by": user_id,
                "expires_at": (datetime.now() + timedelta(hours=expires_in_hours)).isoformat(),
                "view_count": 0
            }
            
            # Store in Redis with expiration
            redis_key = f"share:{link_id}"
            self.redis_client.setex(
                redis_key,
                timedelta(hours=expires_in_hours),
                json.dumps(share_data, default=str)
            )
            
            logger.info(f"Created shareable link {link_id} for {analysis_result.symbol}")
            return link_id
            
        except Exception as e:
            logger.error(f"Error creating shareable link: {e}")
            raise
    
    async def get_shared_analysis(self, link_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve shared analysis by link ID.
        
        Args:
            link_id: Shareable link ID
            
        Returns:
            Dict containing analysis data or None if not found/expired
        """
        try:
            redis_key = f"share:{link_id}"
            data = self.redis_client.get(redis_key)
            
            if not data:
                return None
            
            share_data = json.loads(data)
            
            # Increment view count
            share_data["view_count"] += 1
            self.redis_client.setex(
                redis_key,
                self.redis_client.ttl(redis_key),
                json.dumps(share_data, default=str)
            )
            
            logger.info(f"Retrieved shared analysis {link_id}, view count: {share_data['view_count']}")
            return share_data
            
        except Exception as e:
            logger.error(f"Error retrieving shared analysis: {e}")
            return None
    
    async def export_data_csv(
        self,
        analysis_result: AnalysisResult,
        sentiment_result: Optional[SentimentAnalysisResult] = None
    ) -> str:
        """
        Export analysis data to CSV format.
        
        Args:
            analysis_result: Stock analysis results
            sentiment_result: Optional sentiment analysis results
            
        Returns:
            str: CSV content
        """
        try:
            import csv
            from io import StringIO
            
            output = StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'Timestamp', 'Symbol', 'Analysis_Type', 'Recommendation', 'Confidence',
                'Overall_Score', 'Fundamental_Score', 'Technical_Score', 'Risk_Level',
                'Strengths', 'Weaknesses', 'Risks', 'Opportunities'
            ])
            
            # Write analysis data
            writer.writerow([
                analysis_result.analysis_timestamp.isoformat(),
                analysis_result.symbol,
                analysis_result.analysis_type.value,
                analysis_result.recommendation.value,
                analysis_result.confidence,
                analysis_result.overall_score,
                analysis_result.fundamental_score,
                analysis_result.technical_score,
                analysis_result.risk_level.value,
                '; '.join(analysis_result.strengths),
                '; '.join(analysis_result.weaknesses),
                '; '.join(analysis_result.risks),
                '; '.join(analysis_result.opportunities)
            ])
            
            # Add price targets if available
            if analysis_result.price_targets:
                writer.writerow([])  # Empty row
                writer.writerow(['Price Targets'])
                writer.writerow(['Timeframe', 'Target_Price', 'Confidence', 'Rationale'])
                
                for target in analysis_result.price_targets:
                    writer.writerow([
                        target.timeframe,
                        float(target.target),
                        target.confidence,
                        target.rationale
                    ])
            
            # Add sentiment data if available
            if sentiment_result:
                writer.writerow([])  # Empty row
                writer.writerow(['Sentiment Analysis'])
                writer.writerow([
                    'Overall_Sentiment', 'News_Sentiment', 'Social_Sentiment',
                    'Trend_Direction', 'Confidence_Score'
                ])
                writer.writerow([
                    float(sentiment_result.sentiment_data.overall_sentiment),
                    float(sentiment_result.sentiment_data.news_sentiment),
                    float(sentiment_result.sentiment_data.social_sentiment),
                    sentiment_result.sentiment_data.trend_direction.value,
                    float(sentiment_result.sentiment_data.confidence_score)
                ])
            
            csv_content = output.getvalue()
            output.close()
            
            logger.info(f"CSV export generated for {analysis_result.symbol}")
            return csv_content
            
        except Exception as e:
            logger.error(f"Error generating CSV export: {e}")
            raise
    
    async def export_data_json(
        self,
        analysis_result: AnalysisResult,
        sentiment_result: Optional[SentimentAnalysisResult] = None,
        include_metadata: bool = True
    ) -> str:
        """
        Export analysis data to JSON format.
        
        Args:
            analysis_result: Stock analysis results
            sentiment_result: Optional sentiment analysis results
            include_metadata: Whether to include export metadata
            
        Returns:
            str: JSON content
        """
        try:
            export_data = {
                "analysis": analysis_result.dict(),
                "sentiment": sentiment_result.dict() if sentiment_result else None
            }
            
            if include_metadata:
                export_data["export_metadata"] = {
                    "exported_at": datetime.now().isoformat(),
                    "format": "json",
                    "version": "1.0",
                    "disclaimer": "This data is for informational purposes only and does not constitute investment advice."
                }
            
            json_content = json.dumps(export_data, indent=2, default=str)
            
            logger.info(f"JSON export generated for {analysis_result.symbol}")
            return json_content
            
        except Exception as e:
            logger.error(f"Error generating JSON export: {e}")
            raise
    
    async def save_export_file(
        self,
        content: bytes,
        filename: str,
        content_type: str = "application/pdf"
    ) -> str:
        """
        Save export file to storage (local or cloud).
        
        Args:
            content: File content as bytes
            filename: Filename for the export
            content_type: MIME type of the content
            
        Returns:
            str: File path or URL
        """
        try:
            # Try cloud storage first
            if self.storage_client:
                try:
                    bucket = self.storage_client.bucket(self.bucket_name)
                    blob = bucket.blob(f"exports/{filename}")
                    blob.upload_from_string(content, content_type=content_type)
                    
                    # Make blob publicly readable for sharing
                    blob.make_public()
                    
                    logger.info(f"Export file saved to GCS: {filename}")
                    return blob.public_url
                    
                except Exception as e:
                    logger.warning(f"Failed to save to GCS, falling back to local: {e}")
            
            # Fallback to local storage
            local_path = self.local_export_dir / filename
            with open(local_path, 'wb') as f:
                f.write(content)
            
            logger.info(f"Export file saved locally: {filename}")
            return str(local_path)
            
        except Exception as e:
            logger.error(f"Error saving export file: {e}")
            raise
    
    async def get_user_exports(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get user's recent exports.
        
        Args:
            user_id: User ID
            limit: Maximum number of exports to return
            
        Returns:
            List of export metadata
        """
        try:
            # This would typically query a database
            # For now, return empty list as placeholder
            return []
            
        except Exception as e:
            logger.error(f"Error getting user exports: {e}")
            return []
    
    async def delete_shared_link(self, link_id: str, user_id: Optional[str] = None) -> bool:
        """
        Delete a shared link.
        
        Args:
            link_id: Shareable link ID
            user_id: User ID for authorization
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            redis_key = f"share:{link_id}"
            
            # Check if link exists and user has permission
            if user_id:
                data = self.redis_client.get(redis_key)
                if data:
                    share_data = json.loads(data)
                    if share_data.get("created_by") != user_id:
                        return False
            
            # Delete the link
            deleted = self.redis_client.delete(redis_key)
            
            if deleted:
                logger.info(f"Deleted shared link {link_id}")
                return True
            else:
                logger.warning(f"Shared link {link_id} not found")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting shared link: {e}")
            return False


# Global export service instance
export_service = ExportService()