"""
Performance tests for critical endpoints and services.
"""

import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main import app
from app.services.data_aggregation import DataAggregationService
from app.services.analysis_engine import AnalysisEngine
from tests.test_factories import MarketDataFactory, FundamentalDataFactory


@pytest.mark.performance
class TestAPIPerformance:
    """Performance tests for API endpoints."""
    
    def test_health_endpoint_performance(self, benchmark):
        """Test health endpoint response time."""
        client = TestClient(app)
        
        def call_health():
            response = client.get("/health")
            assert response.status_code == 200
            return response
        
        result = benchmark(call_health)
        assert result.status_code == 200
        # Health endpoint should respond in under 100ms
        assert benchmark.stats.stats.mean < 0.1

    def test_stock_lookup_performance(self, benchmark, client, auth_headers):
        """Test stock lookup endpoint performance."""
        
        with patch('app.services.data_aggregation.DataAggregationService.get_market_data') as mock_data:
            mock_data.return_value = MarketDataFactory()
            
            def call_stock_lookup():
                response = client.get("/api/stocks/AAPL", headers=auth_headers)
                assert response.status_code == 200
                return response
            
            result = benchmark(call_stock_lookup)
            assert result.status_code == 200
            # Stock lookup should respond in under 500ms
            assert benchmark.stats.stats.mean < 0.5

    def test_analysis_endpoint_performance(self, benchmark, client, auth_headers):
        """Test stock analysis endpoint performance."""
        
        with patch('app.services.analysis_engine.AnalysisEngine.perform_combined_analysis') as mock_analysis:
            mock_analysis.return_value = {
                "symbol": "AAPL",
                "recommendation": "BUY",
                "confidence": 85,
                "reasoning": ["Strong fundamentals"],
                "risks": ["Market volatility"]
            }
            
            def call_analysis():
                response = client.post(
                    "/api/analysis/AAPL",
                    json={"analysis_types": ["fundamental", "technical"]},
                    headers=auth_headers
                )
                assert response.status_code == 200
                return response
            
            result = benchmark(call_analysis)
            assert result.status_code == 200
            # Analysis should complete in under 2 seconds
            assert benchmark.stats.stats.mean < 2.0

    @pytest.mark.slow
    def test_concurrent_requests_performance(self, client, auth_headers):
        """Test API performance under concurrent load."""
        
        def make_request():
            response = client.get("/health")
            return response.status_code
        
        # Test with 10 concurrent requests
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in futures]
        
        end_time = time.time()
        duration = end_time - start_time
        
        # All requests should succeed
        assert all(status == 200 for status in results)
        # 10 concurrent requests should complete in under 2 seconds
        assert duration < 2.0


@pytest.mark.performance
class TestServicePerformance:
    """Performance tests for core services."""
    
    @pytest.mark.asyncio
    async def test_data_aggregation_performance(self, benchmark):
        """Test data aggregation service performance."""
        service = DataAggregationService()
        
        with patch.object(service, '_fetch_yfinance_data') as mock_fetch:
            mock_fetch.return_value = MarketDataFactory()
            
            async def get_market_data():
                return await service.get_market_data("AAPL")
            
            result = await benchmark(get_market_data)
            assert result is not None
            # Data aggregation should complete in under 200ms
            assert benchmark.stats.stats.mean < 0.2

    @pytest.mark.asyncio
    async def test_analysis_engine_performance(self, benchmark):
        """Test analysis engine performance."""
        engine = AnalysisEngine()
        
        with patch.object(engine, 'fundamental_analyzer') as mock_fundamental, \
             patch.object(engine, 'technical_analyzer') as mock_technical:
            
            mock_fundamental.analyze.return_value = {"score": 85, "recommendation": "BUY"}
            mock_technical.analyze.return_value = {"score": 75, "recommendation": "BUY"}
            
            async def perform_analysis():
                return await engine.perform_combined_analysis("AAPL")
            
            result = await benchmark(perform_analysis)
            assert result is not None
            # Combined analysis should complete in under 1 second
            assert benchmark.stats.stats.mean < 1.0

    def test_cache_performance(self, benchmark):
        """Test Redis cache performance."""
        from app.core.cache import get_cache_client
        
        cache = get_cache_client()
        test_key = "performance_test_key"
        test_value = {"data": "test_performance_data"}
        
        def cache_operations():
            # Set operation
            cache.setex(test_key, 60, str(test_value))
            # Get operation
            result = cache.get(test_key)
            # Delete operation
            cache.delete(test_key)
            return result
        
        result = benchmark(cache_operations)
        assert result is not None
        # Cache operations should complete in under 10ms
        assert benchmark.stats.stats.mean < 0.01


@pytest.mark.performance
class TestDatabasePerformance:
    """Performance tests for database operations."""
    
    def test_user_query_performance(self, benchmark, db_session):
        """Test user query performance."""
        from app.models.user import User
        
        # Create test users
        users = []
        for i in range(100):
            user = User(
                email=f"perftest{i}@example.com",
                full_name=f"Performance Test User {i}",
                hashed_password="test_hash"
            )
            users.append(user)
        
        db_session.add_all(users)
        db_session.commit()
        
        def query_users():
            return db_session.query(User).filter(User.is_active == True).limit(10).all()
        
        result = benchmark(query_users)
        assert len(result) == 10
        # User queries should complete in under 50ms
        assert benchmark.stats.stats.mean < 0.05

    def test_watchlist_query_performance(self, benchmark, db_session, test_user):
        """Test watchlist query performance."""
        from app.models.watchlist import Watchlist, WatchlistItem
        
        # Create test watchlists with items
        for i in range(10):
            watchlist = Watchlist(
                user_id=test_user.id,
                name=f"Performance Test Watchlist {i}",
                description="Performance test"
            )
            db_session.add(watchlist)
            db_session.flush()
            
            # Add items to each watchlist
            for j in range(20):
                item = WatchlistItem(
                    watchlist_id=watchlist.id,
                    symbol=f"PERF{i}{j}",
                    company_name=f"Performance Test Company {i}-{j}"
                )
                db_session.add(item)
        
        db_session.commit()
        
        def query_watchlists():
            return db_session.query(Watchlist).filter(
                Watchlist.user_id == test_user.id
            ).all()
        
        result = benchmark(query_watchlists)
        assert len(result) == 10
        # Watchlist queries should complete in under 100ms
        assert benchmark.stats.stats.mean < 0.1


@pytest.mark.performance
class TestMemoryUsage:
    """Memory usage tests for critical operations."""
    
    def test_large_dataset_memory_usage(self):
        """Test memory usage with large datasets."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate processing large dataset
        large_data = []
        for i in range(10000):
            large_data.append({
                "symbol": f"TEST{i}",
                "price": 100.0 + i,
                "volume": 1000000 + i * 1000,
                "data": [j for j in range(100)]  # Simulate complex data
            })
        
        # Process the data
        processed_data = []
        for item in large_data:
            processed_item = {
                "symbol": item["symbol"],
                "avg_price": sum(item["data"]) / len(item["data"]),
                "total_volume": item["volume"]
            }
            processed_data.append(processed_item)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for this test)
        assert memory_increase < 100, f"Memory usage increased by {memory_increase}MB"
        
        # Clean up
        del large_data
        del processed_data


@pytest.mark.performance
class TestLoadTesting:
    """Load testing for critical endpoints."""
    
    @pytest.mark.slow
    def test_health_endpoint_load(self):
        """Load test the health endpoint."""
        client = TestClient(app)
        
        def make_requests(num_requests):
            success_count = 0
            error_count = 0
            response_times = []
            
            for _ in range(num_requests):
                start_time = time.time()
                try:
                    response = client.get("/health")
                    end_time = time.time()
                    response_times.append(end_time - start_time)
                    
                    if response.status_code == 200:
                        success_count += 1
                    else:
                        error_count += 1
                except Exception:
                    error_count += 1
                    end_time = time.time()
                    response_times.append(end_time - start_time)
            
            return success_count, error_count, response_times
        
        # Test with 100 requests
        success, errors, times = make_requests(100)
        
        # At least 95% success rate
        success_rate = success / (success + errors)
        assert success_rate >= 0.95, f"Success rate: {success_rate:.2%}"
        
        # Average response time should be reasonable
        avg_response_time = sum(times) / len(times)
        assert avg_response_time < 0.5, f"Average response time: {avg_response_time:.3f}s"
        
        # 95th percentile should be reasonable
        times.sort()
        p95_response_time = times[int(len(times) * 0.95)]
        assert p95_response_time < 1.0, f"95th percentile response time: {p95_response_time:.3f}s"

    @pytest.mark.slow
    def test_concurrent_user_simulation(self, client, multiple_users):
        """Simulate concurrent users accessing the system."""
        
        def simulate_user_session(user_email):
            """Simulate a user session with multiple requests."""
            # Login
            login_response = client.post("/api/auth/login", json={
                "email": user_email,
                "password": "TestPassword123!"
            })
            
            if login_response.status_code != 200:
                return False
            
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Make several requests
            requests_made = 0
            successful_requests = 0
            
            # Get user profile
            response = client.get("/api/auth/me", headers=headers)
            requests_made += 1
            if response.status_code == 200:
                successful_requests += 1
            
            # Get watchlists
            response = client.get("/api/watchlists", headers=headers)
            requests_made += 1
            if response.status_code == 200:
                successful_requests += 1
            
            # Get stock data (mocked)
            with patch('app.services.data_aggregation.DataAggregationService.get_market_data'):
                response = client.get("/api/stocks/AAPL", headers=headers)
                requests_made += 1
                if response.status_code == 200:
                    successful_requests += 1
            
            return successful_requests / requests_made >= 0.9  # 90% success rate
        
        # Simulate 5 concurrent users
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=5) as executor:
            user_emails = [user.email for user in multiple_users[:5]]
            futures = [executor.submit(simulate_user_session, email) for email in user_emails]
            results = [future.result() for future in futures]
        
        end_time = time.time()
        duration = end_time - start_time
        
        # All user sessions should be successful
        success_rate = sum(results) / len(results)
        assert success_rate >= 0.8, f"User session success rate: {success_rate:.2%}"
        
        # Concurrent sessions should complete in reasonable time
        assert duration < 10.0, f"Concurrent sessions took {duration:.2f}s"