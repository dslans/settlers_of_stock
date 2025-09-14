"""
Pytest configuration and custom fixtures for comprehensive testing.
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path


def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers", "unit: Unit tests that don't require external dependencies"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests that require database/external services"
    )
    config.addinivalue_line(
        "markers", "api: API endpoint tests"
    )
    config.addinivalue_line(
        "markers", "database: Database operation tests"
    )
    config.addinivalue_line(
        "markers", "external: Tests requiring external APIs"
    )
    config.addinivalue_line(
        "markers", "slow: Slow running tests (>5 seconds)"
    )
    config.addinivalue_line(
        "markers", "performance: Performance and benchmark tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location and name."""
    for item in items:
        # Add markers based on test file location
        if "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        if "test_performance" in item.nodeid or "test_load" in item.nodeid:
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)
        
        if "test_database" in item.nodeid:
            item.add_marker(pytest.mark.database)
        
        if "_api" in item.nodeid or "test_main" in item.nodeid:
            item.add_marker(pytest.mark.api)
        
        # Add markers based on test name patterns
        if "external" in item.name.lower():
            item.add_marker(pytest.mark.external)
        
        if any(keyword in item.name.lower() for keyword in ["slow", "load", "stress", "endurance"]):
            item.add_marker(pytest.mark.slow)


@pytest.fixture(scope="session")
def test_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp(prefix="settlers_test_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="session")
def test_config():
    """Test configuration settings."""
    return {
        "database_url": "sqlite:///./test_settlers_of_stock.db",
        "redis_url": "redis://localhost:6379/1",  # Use different DB for tests
        "secret_key": "test-secret-key-for-testing-only",
        "environment": "test",
        "debug": True,
        "testing": True,
    }


@pytest.fixture(autouse=True)
def setup_test_environment(test_config):
    """Set up test environment variables."""
    original_env = {}
    
    # Store original environment variables
    for key, value in test_config.items():
        env_key = key.upper()
        original_env[env_key] = os.environ.get(env_key)
        os.environ[env_key] = str(value)
    
    yield
    
    # Restore original environment variables
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


@pytest.fixture
def mock_external_apis():
    """Mock all external API calls for isolated testing."""
    with patch('yfinance.Ticker') as mock_yf, \
         patch('requests.get') as mock_requests, \
         patch('app.services.vertex_ai_service.VertexAIService') as mock_vertex:
        
        # Configure yfinance mock
        mock_ticker = MagicMock()
        mock_ticker.info = {
            'symbol': 'AAPL',
            'currentPrice': 150.00,
            'regularMarketChange': 2.50,
            'regularMarketChangePercent': 1.69,
            'volume': 50000000
        }
        mock_yf.return_value = mock_ticker
        
        # Configure requests mock
        mock_response = MagicMock()
        mock_response.json.return_value = {'status': 'ok', 'articles': []}
        mock_response.status_code = 200
        mock_requests.return_value = mock_response
        
        # Configure Vertex AI mock
        mock_vertex_instance = MagicMock()
        mock_vertex_instance.generate_stock_analysis_response.return_value = "Mock AI response"
        mock_vertex.return_value = mock_vertex_instance
        
        yield {
            'yfinance': mock_yf,
            'requests': mock_requests,
            'vertex_ai': mock_vertex
        }


@pytest.fixture
def performance_thresholds():
    """Performance testing thresholds."""
    return {
        'health_endpoint': {
            'max_response_time': 0.1,  # 100ms
            'max_error_rate': 1.0,     # 1%
            'min_throughput': 100      # requests/second
        },
        'stock_lookup': {
            'max_response_time': 0.5,  # 500ms
            'max_error_rate': 5.0,     # 5%
            'min_throughput': 20       # requests/second
        },
        'analysis_endpoint': {
            'max_response_time': 2.0,  # 2 seconds
            'max_error_rate': 10.0,    # 10%
            'min_throughput': 5        # requests/second
        },
        'chat_endpoint': {
            'max_response_time': 3.0,  # 3 seconds
            'max_error_rate': 15.0,    # 15%
            'min_throughput': 2        # requests/second
        }
    }


class TestReporter:
    """Custom test reporter for generating detailed test reports."""
    
    def __init__(self):
        self.test_results = []
        self.performance_results = []
    
    def add_test_result(self, test_name, status, duration, error_message=None):
        """Add a test result."""
        self.test_results.append({
            'test_name': test_name,
            'status': status,
            'duration': duration,
            'error_message': error_message
        })
    
    def add_performance_result(self, endpoint, metrics):
        """Add performance test result."""
        self.performance_results.append({
            'endpoint': endpoint,
            'metrics': metrics
        })
    
    def generate_report(self, output_file='test_report.html'):
        """Generate HTML test report."""
        html_content = self._generate_html_report()
        with open(output_file, 'w') as f:
            f.write(html_content)
    
    def _generate_html_report(self):
        """Generate HTML content for test report."""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'passed'])
        failed_tests = total_tests - passed_tests
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Settlers of Stock - Test Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
                .passed {{ color: green; }}
                .failed {{ color: red; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>Settlers of Stock - Test Report</h1>
            
            <div class="summary">
                <h2>Test Summary</h2>
                <p>Total Tests: {total_tests}</p>
                <p class="passed">Passed: {passed_tests}</p>
                <p class="failed">Failed: {failed_tests}</p>
                <p>Success Rate: {(passed_tests/total_tests*100):.1f}%</p>
            </div>
            
            <h2>Test Results</h2>
            <table>
                <tr>
                    <th>Test Name</th>
                    <th>Status</th>
                    <th>Duration (s)</th>
                    <th>Error Message</th>
                </tr>
        """
        
        for result in self.test_results:
            status_class = 'passed' if result['status'] == 'passed' else 'failed'
            html += f"""
                <tr>
                    <td>{result['test_name']}</td>
                    <td class="{status_class}">{result['status']}</td>
                    <td>{result['duration']:.3f}</td>
                    <td>{result.get('error_message', '')}</td>
                </tr>
            """
        
        html += """
            </table>
            
            <h2>Performance Results</h2>
            <table>
                <tr>
                    <th>Endpoint</th>
                    <th>Avg Response Time (ms)</th>
                    <th>Requests/sec</th>
                    <th>Error Rate (%)</th>
                </tr>
        """
        
        for result in self.performance_results:
            metrics = result['metrics']
            html += f"""
                <tr>
                    <td>{result['endpoint']}</td>
                    <td>{metrics.get('avg_response_time', 0)*1000:.2f}</td>
                    <td>{metrics.get('requests_per_second', 0):.2f}</td>
                    <td>{metrics.get('error_rate', 0):.2f}</td>
                </tr>
            """
        
        html += """
            </table>
        </body>
        </html>
        """
        
        return html


@pytest.fixture(scope="session")
def test_reporter():
    """Test reporter fixture."""
    return TestReporter()


# Import required modules for mocking
from unittest.mock import patch, MagicMock