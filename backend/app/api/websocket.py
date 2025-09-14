"""
WebSocket API endpoints for real-time chat communication.
Handles WebSocket connections, message broadcasting, and connection management.
"""

import json
import logging
from typing import Dict, List, Set
from datetime import datetime
import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, ValidationError
import jwt

from app.services.chat_service import ChatService, ChatMessage, ChatResponse
from app.services.vertex_ai_service import AnalysisResult
from app.core.config import get_settings
from app.core.dependencies import get_current_user
from app.core.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()
settings = get_settings()

# Chat service will be initialized per connection

# Security
security = HTTPBearer()

# WebSocket message models
class WebSocketMessage(BaseModel):
    """Base WebSocket message structure"""
    type: str
    timestamp: datetime = datetime.now()

class ChatWebSocketMessage(WebSocketMessage):
    """Chat message over WebSocket"""
    type: str = "chat_message"
    message: str
    analysis_data: Dict = None

class SystemWebSocketMessage(WebSocketMessage):
    """System message over WebSocket"""
    type: str = "system_message"
    message: str
    level: str = "info"  # info, warning, error

class ConnectionWebSocketMessage(WebSocketMessage):
    """Connection status message"""
    type: str = "connection_status"
    status: str  # connected, disconnected, reconnected
    user_count: int = 0

class ErrorWebSocketMessage(WebSocketMessage):
    """Error message over WebSocket"""
    type: str = "error"
    message: str
    error_code: str = "UNKNOWN_ERROR"

# Connection manager for handling multiple WebSocket connections
class ConnectionManager:
    """Manages WebSocket connections and message broadcasting"""
    
    def __init__(self):
        # Active connections: user_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        # Connection metadata: user_id -> connection info
        self.connection_info: Dict[str, Dict] = {}
        # Room-based connections for future group chat features
        self.rooms: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept WebSocket connection and register user"""
        await websocket.accept()
        
        # Close existing connection if user reconnects
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].close()
            except Exception as e:
                logger.warning(f"Error closing existing connection for user {user_id}: {e}")
        
        self.active_connections[user_id] = websocket
        self.connection_info[user_id] = {
            "connected_at": datetime.now(),
            "last_activity": datetime.now(),
            "message_count": 0
        }
        
        logger.info(f"WebSocket connected for user {user_id}. Total connections: {len(self.active_connections)}")
        
        # Send connection confirmation
        await self.send_personal_message(
            ConnectionWebSocketMessage(
                status="connected",
                user_count=len(self.active_connections)
            ).model_dump(),
            user_id
        )
    
    def disconnect(self, user_id: str):
        """Remove user connection"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.connection_info:
            del self.connection_info[user_id]
        
        logger.info(f"WebSocket disconnected for user {user_id}. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: Dict, user_id: str):
        """Send message to specific user"""
        if user_id in self.active_connections:
            try:
                websocket = self.active_connections[user_id]
                await websocket.send_text(json.dumps(message, default=str))
                
                # Update activity timestamp
                if user_id in self.connection_info:
                    self.connection_info[user_id]["last_activity"] = datetime.now()
                    
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                # Remove broken connection
                self.disconnect(user_id)
    
    async def broadcast_message(self, message: Dict, exclude_user: str = None):
        """Broadcast message to all connected users"""
        disconnected_users = []
        
        for user_id, websocket in self.active_connections.items():
            if exclude_user and user_id == exclude_user:
                continue
                
            try:
                await websocket.send_text(json.dumps(message, default=str))
            except Exception as e:
                logger.error(f"Error broadcasting to user {user_id}: {e}")
                disconnected_users.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected_users:
            self.disconnect(user_id)
    
    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return len(self.active_connections)
    
    def get_user_info(self, user_id: str) -> Dict:
        """Get connection info for specific user"""
        return self.connection_info.get(user_id, {})
    
    async def ping_all_connections(self):
        """Send ping to all connections to check health"""
        ping_message = SystemWebSocketMessage(
            message="ping",
            level="info"
        ).model_dump()
        
        await self.broadcast_message(ping_message)

# Global connection manager instance
manager = ConnectionManager()

async def get_current_user_from_websocket(websocket: WebSocket) -> str:
    """Extract user ID from WebSocket connection (from query params or headers)"""
    try:
        # Try to get token from query parameters
        token = websocket.query_params.get("token")
        
        if not token:
            # Try to get from headers (if supported by client)
            headers = dict(websocket.headers)
            auth_header = headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No authentication token provided"
            )
        
        # Decode JWT token
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = payload.get("sub")
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: no user ID"
            )
        
        return user_id
        
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    except Exception as e:
        logger.error(f"Error extracting user from WebSocket: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

@router.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat communication
    
    Handles:
    - User authentication via token
    - Real-time message exchange
    - Connection management
    - Error handling and recovery
    """
    user_id = None
    
    try:
        # Authenticate user before accepting connection
        user_id = await get_current_user_from_websocket(websocket)
        
        # Connect user
        await manager.connect(websocket, user_id)
        
        # Send welcome message
        welcome_message = SystemWebSocketMessage(
            message=f"Connected to Settlers of Stock chat. You can now send messages in real-time!",
            level="info"
        ).model_dump()
        await manager.send_personal_message(welcome_message, user_id)
        
        # Main message loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Validate message structure
                try:
                    ws_message = ChatWebSocketMessage(**message_data)
                except ValidationError as e:
                    error_msg = ErrorWebSocketMessage(
                        message=f"Invalid message format: {str(e)}",
                        error_code="INVALID_MESSAGE_FORMAT"
                    ).model_dump()
                    await manager.send_personal_message(error_msg, user_id)
                    continue
                
                # Update message count
                if user_id in manager.connection_info:
                    manager.connection_info[user_id]["message_count"] += 1
                
                # Process chat message through chat service
                analysis_result = None
                if ws_message.analysis_data:
                    try:
                        analysis_result = AnalysisResult(**ws_message.analysis_data)
                    except Exception as e:
                        logger.warning(f"Invalid analysis data in WebSocket message: {e}")
                
                # Create chat service instance (we can't use dependency injection in websockets easily)
                import os
                testing_mode = os.getenv("TESTING_MODE", "false").lower() == "true"
                
                try:
                    # For websockets, we'll create a chat service without DB session for now
                    # In a production environment, you'd want to properly manage DB sessions
                    chat_service_instance = ChatService(testing_mode=testing_mode, db_session=None)
                    
                    chat_response = await chat_service_instance.process_message(
                        user_id=user_id,
                        message=ws_message.message,
                        analysis_result=analysis_result
                    )
                except Exception as e:
                    logger.error(f"Error creating chat service: {e}")
                    # Mock response for testing or when service fails
                    from app.services.chat_service import ChatResponse
                    chat_response = ChatResponse(
                        message=f"Mock response to: {ws_message.message}",
                        message_type="assistant"
                    )
                
                # Send response back to user
                response_message = {
                    "type": "chat_response",
                    "message": chat_response.message,
                    "message_type": chat_response.message_type,
                    "analysis_data": chat_response.analysis_data,
                    "suggestions": chat_response.suggestions,
                    "requires_follow_up": chat_response.requires_follow_up,
                    "timestamp": datetime.now().isoformat()
                }
                
                await manager.send_personal_message(response_message, user_id)
                
                logger.info(f"Processed WebSocket message for user {user_id}")
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for user {user_id}")
                break
            except json.JSONDecodeError:
                error_msg = ErrorWebSocketMessage(
                    message="Invalid JSON format",
                    error_code="INVALID_JSON"
                ).model_dump()
                await manager.send_personal_message(error_msg, user_id)
            except Exception as e:
                logger.error(f"Error processing WebSocket message for user {user_id}: {e}")
                error_msg = ErrorWebSocketMessage(
                    message="Error processing your message. Please try again.",
                    error_code="PROCESSING_ERROR"
                ).model_dump()
                await manager.send_personal_message(error_msg, user_id)
                
    except HTTPException as e:
        # Authentication failed
        logger.warning(f"WebSocket authentication failed: {e.detail}")
        await websocket.close(code=1008, reason=e.detail)
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket connection: {e}")
        await websocket.close(code=1011, reason="Internal server error")
    finally:
        # Clean up connection
        if user_id:
            manager.disconnect(user_id)

@router.websocket("/ws/market-updates")
async def websocket_market_updates(websocket: WebSocket):
    """
    WebSocket endpoint for real-time market data updates
    
    Sends periodic market updates to connected clients
    """
    user_id = None
    
    try:
        # Authenticate user
        user_id = await get_current_user_from_websocket(websocket)
        await websocket.accept()
        
        logger.info(f"Market updates WebSocket connected for user {user_id}")
        
        # Send initial connection message
        welcome_message = {
            "type": "market_connection",
            "message": "Connected to real-time market updates",
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(welcome_message, default=str))
        
        # Market update loop (placeholder - would integrate with real market data)
        while True:
            try:
                # Wait for 30 seconds between updates
                await asyncio.sleep(30)
                
                # Send market update (placeholder data)
                market_update = {
                    "type": "market_update",
                    "data": {
                        "SPY": {"price": 450.25, "change": 0.5},
                        "QQQ": {"price": 375.80, "change": -0.2},
                        "IWM": {"price": 195.45, "change": 1.2}
                    },
                    "timestamp": datetime.now().isoformat()
                }
                
                await websocket.send_text(json.dumps(market_update, default=str))
                
            except WebSocketDisconnect:
                logger.info(f"Market updates WebSocket disconnected for user {user_id}")
                break
            except Exception as e:
                logger.error(f"Error sending market update to user {user_id}: {e}")
                break
                
    except HTTPException as e:
        logger.warning(f"Market updates WebSocket authentication failed: {e.detail}")
        await websocket.close(code=1008, reason=e.detail)
    except Exception as e:
        logger.error(f"Unexpected error in market updates WebSocket: {e}")
        await websocket.close(code=1011, reason="Internal server error")

# REST endpoints for WebSocket management
@router.get("/ws/status")
async def websocket_status():
    """Get WebSocket connection status and statistics"""
    return {
        "active_connections": manager.get_connection_count(),
        "connection_info": {
            user_id: {
                "connected_at": info["connected_at"].isoformat(),
                "last_activity": info["last_activity"].isoformat(),
                "message_count": info["message_count"]
            }
            for user_id, info in manager.connection_info.items()
        },
        "timestamp": datetime.now().isoformat()
    }

@router.post("/ws/broadcast")
async def broadcast_message(
    message: str,
    message_type: str = "system",
    current_user: dict = Depends(get_current_user)
):
    """
    Broadcast message to all connected WebSocket clients
    (Admin functionality - would need proper authorization)
    """
    broadcast_msg = SystemWebSocketMessage(
        message=message,
        level=message_type
    ).model_dump()
    
    await manager.broadcast_message(broadcast_msg)
    
    return {
        "message": "Message broadcasted successfully",
        "recipients": manager.get_connection_count(),
        "timestamp": datetime.now().isoformat()
    }

@router.post("/ws/ping")
async def ping_connections():
    """Ping all WebSocket connections to check health"""
    await manager.ping_all_connections()
    
    return {
        "message": "Ping sent to all connections",
        "connection_count": manager.get_connection_count(),
        "timestamp": datetime.now().isoformat()
    }