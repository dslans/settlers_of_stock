"""
Load testing for critical endpoints using locust-like approach.
"""

import pytest
import asyncio
import aiohttp
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from dataclasses import dataclass
from unittest.mock import patch

from fastapi.testclient import TestClient
from main import app


@dataclass
class LoadTestResult:
    """Result of a load test."""
    endpoint: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    error_rate: float


class LoadTester:
    """Load testing utility class."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[LoadTestResult] = []
    
    def run_load_test(
        self,
        endpoint: str,
        num_requests: int,
        concurrent_users: int,
        headers: Dict[str, str] = None,
        method: str = "GET",
        payload: Dict[str, Any] = None
    ) -> LoadTestResult:
        """Run a load test against an endpoint."""
        
        response_times = []
        successful_requests = 0
        failed_requests = 0
        
        start_time = time.time()
        
        def make_request():
            """Make a single request and return response time and success status."""
            request_start = time.time()
            try:
                client = TestClient(app)
                if method == "GET":
                    response = client.get(endpoint, headers=headers)
                elif method == "POST":
                    response = client.post(endpoint, json=payload, headers=headers)
                elif method == "PUT":
                    response = client.put(endpoint, json=payload, headers=headers)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                request_end = time.time()
                response_time = request_end - request_start
                
                if 200 <= response.status_code < 300:
                    return response_time, True
                else:
                    return response_time, False
                    
            except Exception:
                request_end = time.time()
                response_time = request_end - request_start
                return response_time, False
        
        # Execute requests with thread pool
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            
            for future in as_completed(futures):
                response_time, success = future.result()
                response_times.append(response_time)
                
                if success:
                    successful_requests += 1
                else:
                    failed_requests += 1
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Calculate statistics
        avg_response_time = statistics.mean(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)
        
        sorted_times = sorted(response_times)
        p95_index = int(len(sorted_times) * 0.95)
        p99_index = int(len(sorted_times) * 0.99)
        p95_response_time = sorted_times[p95_index]
        p99_response_time = sorted_times[p99_index]
        
        requests_per_second = num_requests / total_duration
        error_rate = (failed_requests / num_requests) * 100
        
        result = LoadTestResult(
            endpoint=endpoint,
            total_requests=num_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate
        )
        
        self.results.append(result)
        return result
    
    def print_results(self):
        """Print load test results in a formatted table."""
        print("\n" + "="*100)
        print("LOAD TEST RESULTS")
        print("="*100)
        
        for result in self.results:
            print(f"\nEndpoint: {result.endpoint}")
            print(f"Total Requests: {result.total_requests}")
            print(f"Successful: {result.successful_requests} ({100-result.error_rate:.1f}%)")
            print(f"Failed: {result.failed_requests} ({result.error_rate:.1f}%)")
            print(f"Requests/sec: {result.requests_per_second:.2f}")
            print(f"Avg Response Time: {result.avg_response_time*1000:.2f}ms")
            print(f"Min Response Time: {result.min_response_time*1000:.2f}ms")
            print(f"Max Response Time: {result.max_response_time*1000:.2f}ms")
            print(f"95th Percentile: {result.p95_response_time*1000:.2f}ms")
            print(f"99th Percentile: {result.p99_response_time*1000:.2f}ms")
            print("-" * 50)


@pytest.mark.slow
@pytest.mark.performance
class TestLoadTesting:
    """Load testing for critical endpoints."""
    
    def setup_method(self):
        """Set up load tester."""
        self.load_tester = LoadTester()
    
    def test_health_endpoint_load(self):
        """Load test the health endpoint."""
        result = self.load_tester.run_load_test(
            endpoint="/health",
            num_requests=100,
            concurrent_users=10
        )
        
        # Assertions
        assert result.error_rate < 1.0, f"Error rate too high: {result.error_rate}%"
        assert result.avg_response_time < 0.1, f"Average response time too slow: {result.avg_response_time}s"
        assert result.p95_response_time < 0.2, f"95th percentile too slow: {result.p95_response_time}s"
        assert result.requests_per_second > 50, f"Throughput too low: {result.requests_per_second} req/s"
    
    def test_stock_lookup_load(self, auth_headers):
        """Load test stock lookup endpoint."""
        with patch('app.services.data_aggregation.DataAggregationService.get_market_data') as mock_data:
            mock_data.return_value = {
                "symbol": "AAPL",
                "price": 150.00,
                "change": 2.50,
                "change_percent": 1.69
            }
            
            result = self.load_tester.run_load_test(
                endpoint="/api/stocks/AAPL",
                num_requests=50,
                concurrent_users=5,
                headers=auth_headers
            )
            
            # Assertions
            assert result.error_rate < 5.0, f"Error rate too high: {result.error_rate}%"
            assert result.avg_response_time < 0.5, f"Average response time too slow: {result.avg_response_time}s"
            assert result.p95_response_time < 1.0, f"95th percentile too slow: {result.p95_response_time}s"
    
    def test_analysis_endpoint_load(self, auth_headers):
        """Load test analysis endpoint."""
        with patch('app.services.analysis_engine.AnalysisEngine.perform_combined_analysis') as mock_analysis:
            mock_analysis.return_value = {
                "symbol": "AAPL",
                "recommendation": "BUY",
                "confidence": 85,
                "reasoning": ["Strong fundamentals"]
            }
            
            payload = {"analysis_types": ["fundamental", "technical"]}
            
            result = self.load_tester.run_load_test(
                endpoint="/api/analysis/AAPL",
                num_requests=30,
                concurrent_users=3,
                headers=auth_headers,
                method="POST",
                payload=payload
            )
            
            # Assertions
            assert result.error_rate < 10.0, f"Error rate too high: {result.error_rate}%"
            assert result.avg_response_time < 2.0, f"Average response time too slow: {result.avg_response_time}s"
    
    def test_chat_endpoint_load(self, auth_headers):
        """Load test chat endpoint."""
        with patch('app.services.vertex_ai_service.VertexAIService.generate_stock_analysis_response') as mock_ai:
            mock_ai.return_value = "Test response from AI"
            
            payload = {
                "message": "Tell me about AAPL",
                "context": {}
            }
            
            result = self.load_tester.run_load_test(
                endpoint="/api/chat",
                num_requests=20,
                concurrent_users=2,
                headers=auth_headers,
                method="POST",
                payload=payload
            )
            
            # Assertions
            assert result.error_rate < 15.0, f"Error rate too high: {result.error_rate}%"
            assert result.avg_response_time < 3.0, f"Average response time too slow: {result.avg_response_time}s"
    
    def test_watchlist_operations_load(self, auth_headers):
        """Load test watchlist operations."""
        # Test GET watchlists
        get_result = self.load_tester.run_load_test(
            endpoint="/api/watchlists",
            num_requests=50,
            concurrent_users=5,
            headers=auth_headers
        )
        
        assert get_result.error_rate < 5.0
        assert get_result.avg_response_time < 0.3
        
        # Test POST watchlist creation
        payload = {
            "name": "Load Test Watchlist",
            "description": "Created during load testing"
        }
        
        post_result = self.load_tester.run_load_test(
            endpoint="/api/watchlists",
            num_requests=20,
            concurrent_users=2,
            headers=auth_headers,
            method="POST",
            payload=payload
        )
        
        assert post_result.error_rate < 10.0
        assert post_result.avg_response_time < 1.0
    
    def test_mixed_workload_simulation(self, auth_headers):
        """Simulate a mixed workload with different endpoints."""
        
        # Simulate realistic user behavior
        endpoints_and_weights = [
            ("/health", 0.1, "GET", None),
            ("/api/stocks/AAPL", 0.3, "GET", None),
            ("/api/stocks/GOOGL", 0.2, "GET", None),
            ("/api/watchlists", 0.2, "GET", None),
            ("/api/alerts", 0.1, "GET", None),
            ("/api/chat", 0.1, "POST", {"message": "What's the market doing?", "context": {}})
        ]
        
        total_requests = 100
        results = []
        
        for endpoint, weight, method, payload in endpoints_and_weights:
            num_requests = int(total_requests * weight)
            if num_requests == 0:
                continue
                
            with patch('app.services.data_aggregation.DataAggregationService.get_market_data') as mock_data, \
                 patch('app.services.vertex_ai_service.VertexAIService.generate_stock_analysis_response') as mock_ai:
                
                mock_data.return_value = {"symbol": "TEST", "price": 100.00}
                mock_ai.return_value = "Test AI response"
                
                result = self.load_tester.run_load_test(
                    endpoint=endpoint,
                    num_requests=num_requests,
                    concurrent_users=3,
                    headers=auth_headers,
                    method=method,
                    payload=payload
                )
                results.append(result)
        
        # Overall system should handle mixed workload well
        avg_error_rate = sum(r.error_rate for r in results) / len(results)
        assert avg_error_rate < 10.0, f"Average error rate across endpoints too high: {avg_error_rate}%"
    
    def test_stress_testing(self, auth_headers):
        """Stress test with high load to find breaking point."""
        
        with patch('app.services.data_aggregation.DataAggregationService.get_market_data') as mock_data:
            mock_data.return_value = {"symbol": "STRESS", "price": 100.00}
            
            # Gradually increase load
            loads = [
                (50, 5),   # 50 requests, 5 concurrent
                (100, 10), # 100 requests, 10 concurrent
                (200, 20), # 200 requests, 20 concurrent
            ]
            
            breaking_point_found = False
            
            for num_requests, concurrent_users in loads:
                result = self.load_tester.run_load_test(
                    endpoint="/api/stocks/STRESS",
                    num_requests=num_requests,
                    concurrent_users=concurrent_users,
                    headers=auth_headers
                )
                
                print(f"\nLoad: {num_requests} requests, {concurrent_users} concurrent users")
                print(f"Error rate: {result.error_rate:.1f}%")
                print(f"Avg response time: {result.avg_response_time*1000:.2f}ms")
                print(f"Requests/sec: {result.requests_per_second:.2f}")
                
                # Consider system stressed if error rate > 20% or avg response time > 2s
                if result.error_rate > 20.0 or result.avg_response_time > 2.0:
                    breaking_point_found = True
                    print(f"⚠️ Breaking point reached at {num_requests} requests with {concurrent_users} concurrent users")
                    break
            
            if not breaking_point_found:
                print("✅ System handled all stress test loads successfully")
    
    def teardown_method(self):
        """Print results after each test."""
        if hasattr(self, 'load_tester') and self.load_tester.results:
            self.load_tester.print_results()


@pytest.mark.slow
@pytest.mark.performance
class TestEnduranceTest:
    """Long-running endurance tests."""
    
    def test_sustained_load_endurance(self, auth_headers):
        """Test system under sustained load over time."""
        
        with patch('app.services.data_aggregation.DataAggregationService.get_market_data') as mock_data:
            mock_data.return_value = {"symbol": "ENDURE", "price": 100.00}
            
            load_tester = LoadTester()
            
            # Run sustained load for multiple intervals
            intervals = 5  # Number of test intervals
            requests_per_interval = 20
            concurrent_users = 3
            
            results = []
            
            for i in range(intervals):
                print(f"\nRunning endurance test interval {i+1}/{intervals}")
                
                result = load_tester.run_load_test(
                    endpoint="/api/stocks/ENDURE",
                    num_requests=requests_per_interval,
                    concurrent_users=concurrent_users,
                    headers=auth_headers
                )
                
                results.append(result)
                
                # Brief pause between intervals
                time.sleep(1)
            
            # Analyze results for degradation
            error_rates = [r.error_rate for r in results]
            response_times = [r.avg_response_time for r in results]
            
            # Check for performance degradation over time
            first_half_avg_time = statistics.mean(response_times[:len(response_times)//2])
            second_half_avg_time = statistics.mean(response_times[len(response_times)//2:])
            
            degradation_pct = ((second_half_avg_time - first_half_avg_time) / first_half_avg_time) * 100
            
            print(f"\nEndurance Test Results:")
            print(f"Average error rate: {statistics.mean(error_rates):.2f}%")
            print(f"Performance degradation: {degradation_pct:+.1f}%")
            
            # Assertions
            assert statistics.mean(error_rates) < 10.0, "Average error rate too high during endurance test"
            assert degradation_pct < 50.0, f"Performance degraded too much: {degradation_pct:.1f}%"
    
    def test_memory_leak_detection(self, auth_headers):
        """Test for memory leaks during sustained operation."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        with patch('app.services.data_aggregation.DataAggregationService.get_market_data') as mock_data:
            mock_data.return_value = {"symbol": "MEMORY", "price": 100.00}
            
            load_tester = LoadTester()
            
            # Run multiple rounds of requests
            for round_num in range(10):
                load_tester.run_load_test(
                    endpoint="/api/stocks/MEMORY",
                    num_requests=20,
                    concurrent_users=2,
                    headers=auth_headers
                )
                
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = current_memory - initial_memory
                
                print(f"Round {round_num + 1}: Memory usage: {current_memory:.1f}MB (+{memory_increase:.1f}MB)")
                
                # Check for excessive memory growth
                if memory_increase > 100:  # 100MB threshold
                    pytest.fail(f"Potential memory leak detected: {memory_increase:.1f}MB increase")
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        total_increase = final_memory - initial_memory
        
        print(f"\nTotal memory increase: {total_increase:.1f}MB")
        assert total_increase < 50, f"Memory usage increased too much: {total_increase:.1f}MB"