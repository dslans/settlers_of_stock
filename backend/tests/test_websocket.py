"""
Integration tests for WebSocket functionality.
Tests WebSocket connection, message handling, and error scenarios.
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect
import jwt
from datetime import datetime, timedelta

from app.api.websocket import manager, ConnectionManager
from app.core.config import get_settings
from main import app

settings = get_settings()

class TestWebSocketConnection:
    """Test WebSocket connection management"""
    
    def setup_method(self):
        """Setup test environment"""
        # Clear any existing connections
        manager.active_connections.clear()
        manager.connection_info.clear()
        
    def test_connection_manager_initialization(self):
        """Test ConnectionManager initialization"""
        cm = ConnectionManager()
        assert cm.active_connections == {}
        assert cm.connection_info == {}
        assert cm.rooms == {}
        
    def test_get_connection_count(self):
        """Test connection count tracking"""
        cm = ConnectionManager()
        assert cm.get_connection_count() == 0
        
        # Simulate connections
        cm.active_connections["user1"] = Mock()
        cm.active_connections["user2"] = Mock()
        
        assert cm.get_connection_count() == 2
        
    def test_get_user_info(self):
        """Test user connection info retrieval"""
        cm = ConnectionManager()
        user_id = "test_user"
        
        # No info initially
        assert cm.get_user_info(user_id) == {}
        
        # Add connection info
        test_info = {
            "connected_at": datetime.now(),
            "last_activity": datetime.now(),
            "message_count": 5
        }
        cm.connection_info[user_id] = test_info
        
        assert cm.get_user_info(user_id) == test_info

class TestWebSocketAuthentication:
    """Test WebSocket authentication"""
    
    def create_test_token(self, user_id: str = "test_user", expired: bool = False) -> str:
        """Create a test JWT token"""
        payload = {
            "sub": user_id,
            "exp": datetime.utcnow() + (timedelta(hours=-1) if expired else timedelta(hours=1))
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    @pytest.mark.asyncio
    async def test_websocket_authentication_success(self):
        """Test successful WebSocket authentication"""
        from app.api.websocket import get_current_user_from_websocket
        
        # Mock WebSocket with valid token
        mock_websocket = Mock()
        mock_websocket.query_params = {"token": self.create_test_token("test_user")}
        mock_websocket.headers = {}
        
        user_id = await get_current_user_from_websocket(mock_websocket)
        assert user_id == "test_user"
    
    @pytest.mark.asyncio
    async def test_websocket_authentication_no_token(self):
        """Test WebSocket authentication without token"""
        from app.api.websocket import get_current_user_from_websocket
        from fastapi import HTTPException
        
        # Mock WebSocket without token
        mock_websocket = Mock()
        mock_websocket.query_params = {}
        mock_websocket.headers = {}
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_from_websocket(mock_websocket)
        
        assert exc_info.value.status_code == 401
        assert "No authentication token provided" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_websocket_authentication_invalid_token(self):
        """Test WebSocket authentication with invalid token"""
        from app.api.websocket import get_current_user_from_websocket
        from fastapi import HTTPException
        
        # Mock WebSocket with invalid token
        mock_websocket = Mock()
        mock_websocket.query_params = {"token": "invalid_token"}
        mock_websocket.headers = {}
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_from_websocket(mock_websocket)
        
        assert exc_info.value.status_code == 401
        assert "Invalid authentication token" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_websocket_authentication_expired_token(self):
        """Test WebSocket authentication with expired token"""
        from app.api.websocket import get_current_user_from_websocket
        from fastapi import HTTPException
        
        # Mock WebSocket with expired token
        mock_websocket = Mock()
        mock_websocket.query_params = {"token": self.create_test_token("test_user", expired=True)}
        mock_websocket.headers = {}
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_from_websocket(mock_websocket)
        
        assert exc_info.value.status_code == 401

class TestWebSocketMessages:
    """Test WebSocket message handling"""
    
    def setup_method(self):
        """Setup test environment"""
        manager.active_connections.clear()
        manager.connection_info.clear()
    
    @pytest.mark.asyncio
    async def test_send_personal_message(self):
        """Test sending message to specific user"""
        # Mock WebSocket connection
        mock_websocket = AsyncMock()
        user_id = "test_user"
        
        # Add connection to manager
        manager.active_connections[user_id] = mock_websocket
        manager.connection_info[user_id] = {
            "connected_at": datetime.now(),
            "last_activity": datetime.now(),
            "message_count": 0
        }
        
        # Send message
        test_message = {"type": "test", "content": "Hello"}
        await manager.send_personal_message(test_message, user_id)
        
        # Verify message was sent
        mock_websocket.send_text.assert_called_once()
        sent_data = mock_websocket.send_text.call_args[0][0]
        sent_message = json.loads(sent_data)
        assert sent_message["type"] == "test"
        assert sent_message["content"] == "Hello"
        
        # Verify activity timestamp was updated
        assert manager.connection_info[user_id]["last_activity"] > manager.connection_info[user_id]["connected_at"]
    
    @pytest.mark.asyncio
    async def test_send_personal_message_connection_error(self):
        """Test handling connection error when sending personal message"""
        # Mock WebSocket connection that raises exception
        mock_websocket = AsyncMock()
        mock_websocket.send_text.side_effect = Exception("Connection lost")
        user_id = "test_user"
        
        # Add connection to manager
        manager.active_connections[user_id] = mock_websocket
        manager.connection_info[user_id] = {
            "connected_at": datetime.now(),
            "last_activity": datetime.now(),
            "message_count": 0
        }
        
        # Send message (should handle error gracefully)
        test_message = {"type": "test", "content": "Hello"}
        await manager.send_personal_message(test_message, user_id)
        
        # Verify connection was removed after error
        assert user_id not in manager.active_connections
        assert user_id not in manager.connection_info
    
    @pytest.mark.asyncio
    async def test_broadcast_message(self):
        """Test broadcasting message to all users"""
        # Mock multiple WebSocket connections
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        mock_ws3 = AsyncMock()
        
        manager.active_connections["user1"] = mock_ws1
        manager.active_connections["user2"] = mock_ws2
        manager.active_connections["user3"] = mock_ws3
        
        # Broadcast message
        test_message = {"type": "broadcast", "content": "Hello everyone"}
        await manager.broadcast_message(test_message)
        
        # Verify all connections received the message
        mock_ws1.send_text.assert_called_once()
        mock_ws2.send_text.assert_called_once()
        mock_ws3.send_text.assert_called_once()
        
        # Verify message content
        for mock_ws in [mock_ws1, mock_ws2, mock_ws3]:
            sent_data = mock_ws.send_text.call_args[0][0]
            sent_message = json.loads(sent_data)
            assert sent_message["type"] == "broadcast"
            assert sent_message["content"] == "Hello everyone"
    
    @pytest.mark.asyncio
    async def test_broadcast_message_with_exclusion(self):
        """Test broadcasting message excluding specific user"""
        # Mock multiple WebSocket connections
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        mock_ws3 = AsyncMock()
        
        manager.active_connections["user1"] = mock_ws1
        manager.active_connections["user2"] = mock_ws2
        manager.active_connections["user3"] = mock_ws3
        
        # Broadcast message excluding user2
        test_message = {"type": "broadcast", "content": "Hello"}
        await manager.broadcast_message(test_message, exclude_user="user2")
        
        # Verify only user1 and user3 received the message
        mock_ws1.send_text.assert_called_once()
        mock_ws2.send_text.assert_not_called()
        mock_ws3.send_text.assert_called_once()

class TestWebSocketIntegration:
    """Integration tests for WebSocket endpoints"""
    
    def create_test_token(self, user_id: str = "test_user") -> str:
        """Create a test JWT token"""
        payload = {
            "sub": user_id,
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    @patch('app.services.chat_service.ChatService')
    def test_websocket_status_endpoint(self, mock_chat_service):
        """Test WebSocket status REST endpoint"""
        with TestClient(app) as client:
            response = client.get("/api/v1/ws/status")
            assert response.status_code == 200
            
            data = response.json()
            assert "active_connections" in data
            assert "connection_info" in data
            assert "timestamp" in data
            assert data["active_connections"] == 0
    
    @patch('app.services.chat_service.ChatService')
    def test_ping_connections_endpoint(self, mock_chat_service):
        """Test ping connections REST endpoint"""
        with TestClient(app) as client:
            response = client.post("/api/v1/ws/ping")
            assert response.status_code == 200
            
            data = response.json()
            assert "message" in data
            assert "connection_count" in data
            assert "timestamp" in data
            assert "Ping sent to all connections" in data["message"]

class TestWebSocketErrorHandling:
    """Test WebSocket error handling and recovery"""
    
    def setup_method(self):
        """Setup test environment"""
        manager.active_connections.clear()
        manager.connection_info.clear()
    
    @pytest.mark.asyncio
    async def test_connection_cleanup_on_disconnect(self):
        """Test connection cleanup when user disconnects"""
        user_id = "test_user"
        mock_websocket = Mock()
        
        # Simulate connection
        manager.active_connections[user_id] = mock_websocket
        manager.connection_info[user_id] = {
            "connected_at": datetime.now(),
            "last_activity": datetime.now(),
            "message_count": 5
        }
        
        # Verify connection exists
        assert user_id in manager.active_connections
        assert user_id in manager.connection_info
        
        # Simulate disconnect
        manager.disconnect(user_id)
        
        # Verify cleanup
        assert user_id not in manager.active_connections
        assert user_id not in manager.connection_info
    
    @pytest.mark.asyncio
    async def test_reconnection_handling(self):
        """Test handling of user reconnection"""
        user_id = "test_user"
        old_websocket = AsyncMock()
        new_websocket = AsyncMock()
        
        # Simulate existing connection
        manager.active_connections[user_id] = old_websocket
        manager.connection_info[user_id] = {
            "connected_at": datetime.now(),
            "last_activity": datetime.now(),
            "message_count": 5
        }
        
        # Simulate reconnection
        await manager.connect(new_websocket, user_id)
        
        # Verify old connection was closed
        old_websocket.close.assert_called_once()
        
        # Verify new connection is active
        assert manager.active_connections[user_id] == new_websocket
        new_websocket.accept.assert_called_once()

class TestWebSocketMessageValidation:
    """Test WebSocket message validation"""
    
    def test_chat_websocket_message_validation(self):
        """Test ChatWebSocketMessage validation"""
        from app.api.websocket import ChatWebSocketMessage
        
        # Valid message
        valid_data = {
            "type": "chat_message",
            "message": "Hello",
            "timestamp": datetime.now().isoformat()
        }
        message = ChatWebSocketMessage(**valid_data)
        assert message.type == "chat_message"
        assert message.message == "Hello"
        
        # Invalid message (missing required field)
        with pytest.raises(Exception):
            ChatWebSocketMessage(type="chat_message")
    
    def test_system_websocket_message_validation(self):
        """Test SystemWebSocketMessage validation"""
        from app.api.websocket import SystemWebSocketMessage
        
        # Valid message
        valid_data = {
            "type": "system_message",
            "message": "System notification",
            "level": "info",
            "timestamp": datetime.now().isoformat()
        }
        message = SystemWebSocketMessage(**valid_data)
        assert message.type == "system_message"
        assert message.message == "System notification"
        assert message.level == "info"
    
    def test_error_websocket_message_validation(self):
        """Test ErrorWebSocketMessage validation"""
        from app.api.websocket import ErrorWebSocketMessage
        
        # Valid error message
        valid_data = {
            "type": "error",
            "message": "Something went wrong",
            "error_code": "PROCESSING_ERROR",
            "timestamp": datetime.now().isoformat()
        }
        message = ErrorWebSocketMessage(**valid_data)
        assert message.type == "error"
        assert message.message == "Something went wrong"
        assert message.error_code == "PROCESSING_ERROR"

if __name__ == "__main__":
    pytest.main([__file__])