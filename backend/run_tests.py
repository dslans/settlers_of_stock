#!/usr/bin/env python3
"""
Comprehensive test runner for Settlers of Stock backend.
"""

import argparse
import subprocess
import sys
import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any


class TestRunner:
    """Test runner with different test suites and reporting."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.results = {}
    
    def run_unit_tests(self, verbose: bool = False) -> bool:
        """Run unit tests."""
        print("🧪 Running unit tests...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/",
            "-v" if verbose else "-q",
            "--cov=app",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov/unit",
            "--cov-report=xml:coverage-unit.xml",
            "--junit-xml=test-results-unit.xml",
            "-m", "unit and not slow",
            "--tb=short"
        ]
        
        result = subprocess.run(cmd, cwd=self.project_root)
        success = result.returncode == 0
        
        self.results['unit_tests'] = {
            'success': success,
            'command': ' '.join(cmd),
            'return_code': result.returncode
        }
        
        print(f"✅ Unit tests {'passed' if success else 'failed'}")
        return success
    
    def run_integration_tests(self, verbose: bool = False) -> bool:
        """Run integration tests."""
        print("🔗 Running integration tests...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/",
            "-v" if verbose else "-q",
            "--cov=app",
            "--cov-append",
            "--cov-report=html:htmlcov/integration",
            "--cov-report=xml:coverage-integration.xml",
            "--junit-xml=test-results-integration.xml",
            "-m", "integration",
            "--tb=short"
        ]
        
        result = subprocess.run(cmd, cwd=self.project_root)
        success = result.returncode == 0
        
        self.results['integration_tests'] = {
            'success': success,
            'command': ' '.join(cmd),
            'return_code': result.returncode
        }
        
        print(f"✅ Integration tests {'passed' if success else 'failed'}")
        return success
    
    def run_performance_tests(self, verbose: bool = False) -> bool:
        """Run performance tests."""
        print("⚡ Running performance tests...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/test_performance.py",
            "-v" if verbose else "-q",
            "--benchmark-only",
            "--benchmark-json=benchmark-results.json",
            "--benchmark-sort=mean",
            "--tb=short"
        ]
        
        result = subprocess.run(cmd, cwd=self.project_root)
        success = result.returncode == 0
        
        self.results['performance_tests'] = {
            'success': success,
            'command': ' '.join(cmd),
            'return_code': result.returncode
        }
        
        print(f"✅ Performance tests {'passed' if success else 'failed'}")
        return success
    
    def run_load_tests(self, verbose: bool = False) -> bool:
        """Run load tests."""
        print("🚀 Running load tests...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/test_load_testing.py",
            "-v" if verbose else "-q",
            "-m", "performance",
            "--tb=short"
        ]
        
        result = subprocess.run(cmd, cwd=self.project_root)
        success = result.returncode == 0
        
        self.results['load_tests'] = {
            'success': success,
            'command': ' '.join(cmd),
            'return_code': result.returncode
        }
        
        print(f"✅ Load tests {'passed' if success else 'failed'}")
        return success
    
    def run_security_tests(self, verbose: bool = False) -> bool:
        """Run security tests."""
        print("🔒 Running security tests...")
        
        # Run bandit security linter
        bandit_cmd = [
            "bandit", "-r", "app",
            "-f", "json",
            "-o", "bandit-report.json"
        ]
        
        bandit_result = subprocess.run(bandit_cmd, cwd=self.project_root)
        
        # Run safety check for dependencies
        safety_cmd = [
            "safety", "check",
            "-r", "requirements.txt",
            "--json",
            "--output", "safety-report.json"
        ]
        
        safety_result = subprocess.run(safety_cmd, cwd=self.project_root)
        
        success = bandit_result.returncode == 0 and safety_result.returncode == 0
        
        self.results['security_tests'] = {
            'success': success,
            'bandit_return_code': bandit_result.returncode,
            'safety_return_code': safety_result.returncode
        }
        
        print(f"✅ Security tests {'passed' if success else 'failed'}")
        return success
    
    def run_code_quality_checks(self, verbose: bool = False) -> bool:
        """Run code quality checks."""
        print("📊 Running code quality checks...")
        
        checks = []
        
        # Flake8 linting
        flake8_cmd = ["flake8", "app", "tests", "--max-line-length=100", "--ignore=E203,W503"]
        flake8_result = subprocess.run(flake8_cmd, cwd=self.project_root)
        checks.append(('flake8', flake8_result.returncode == 0))
        
        # MyPy type checking
        mypy_cmd = ["mypy", "app", "--ignore-missing-imports"]
        mypy_result = subprocess.run(mypy_cmd, cwd=self.project_root)
        checks.append(('mypy', mypy_result.returncode == 0))
        
        # Black code formatting check
        black_cmd = ["black", "--check", "app", "tests"]
        black_result = subprocess.run(black_cmd, cwd=self.project_root)
        checks.append(('black', black_result.returncode == 0))
        
        # isort import sorting check
        isort_cmd = ["isort", "--check-only", "app", "tests"]
        isort_result = subprocess.run(isort_cmd, cwd=self.project_root)
        checks.append(('isort', isort_result.returncode == 0))
        
        success = all(check[1] for check in checks)
        
        self.results['code_quality'] = {
            'success': success,
            'checks': dict(checks)
        }
        
        for check_name, check_success in checks:
            status = "✅" if check_success else "❌"
            print(f"  {status} {check_name}")
        
        print(f"✅ Code quality checks {'passed' if success else 'failed'}")
        return success
    
    def generate_coverage_report(self):
        """Generate combined coverage report."""
        print("📈 Generating coverage report...")
        
        # Combine coverage data
        subprocess.run(["coverage", "combine"], cwd=self.project_root)
        
        # Generate reports
        subprocess.run([
            "coverage", "html",
            "--directory=htmlcov/combined"
        ], cwd=self.project_root)
        
        subprocess.run([
            "coverage", "xml",
            "-o", "coverage-combined.xml"
        ], cwd=self.project_root)
        
        # Get coverage percentage
        result = subprocess.run([
            "coverage", "report",
            "--format=total"
        ], cwd=self.project_root, capture_output=True, text=True)
        
        if result.returncode == 0:
            coverage_pct = float(result.stdout.strip())
            self.results['coverage'] = {
                'percentage': coverage_pct,
                'meets_threshold': coverage_pct >= 85
            }
            print(f"📊 Overall coverage: {coverage_pct:.1f}%")
        
    def run_all_tests(self, verbose: bool = False, skip_slow: bool = False) -> bool:
        """Run all test suites."""
        print("🚀 Running comprehensive test suite...")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run test suites
        results = []
        
        results.append(self.run_unit_tests(verbose))
        results.append(self.run_integration_tests(verbose))
        results.append(self.run_code_quality_checks(verbose))
        results.append(self.run_security_tests(verbose))
        
        if not skip_slow:
            results.append(self.run_performance_tests(verbose))
            results.append(self.run_load_tests(verbose))
        
        # Generate coverage report
        self.generate_coverage_report()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Summary
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        
        total_success = all(results)
        
        for suite_name, suite_result in self.results.items():
            if isinstance(suite_result, dict) and 'success' in suite_result:
                status = "✅ PASS" if suite_result['success'] else "❌ FAIL"
                print(f"{status} {suite_name.replace('_', ' ').title()}")
        
        print(f"\n⏱️  Total duration: {duration:.2f} seconds")
        print(f"🎯 Overall result: {'✅ ALL TESTS PASSED' if total_success else '❌ SOME TESTS FAILED'}")
        
        # Save results to JSON
        self.results['summary'] = {
            'total_success': total_success,
            'duration': duration,
            'timestamp': time.time()
        }
        
        with open('test-results-summary.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        return total_success
    
    def run_ci_tests(self, verbose: bool = False) -> bool:
        """Run tests suitable for CI environment."""
        print("🤖 Running CI test suite...")
        
        # Set environment variables for CI
        os.environ['CI'] = 'true'
        os.environ['ENVIRONMENT'] = 'test'
        
        results = []
        
        # Fast tests for CI
        results.append(self.run_unit_tests(verbose))
        results.append(self.run_integration_tests(verbose))
        results.append(self.run_code_quality_checks(verbose))
        
        # Generate coverage
        self.generate_coverage_report()
        
        return all(results)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Settlers of Stock Test Runner")
    parser.add_argument(
        "--suite",
        choices=["unit", "integration", "performance", "load", "security", "quality", "all", "ci"],
        default="all",
        help="Test suite to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--skip-slow",
        action="store_true",
        help="Skip slow tests (performance and load tests)"
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.suite == "unit":
        success = runner.run_unit_tests(args.verbose)
    elif args.suite == "integration":
        success = runner.run_integration_tests(args.verbose)
    elif args.suite == "performance":
        success = runner.run_performance_tests(args.verbose)
    elif args.suite == "load":
        success = runner.run_load_tests(args.verbose)
    elif args.suite == "security":
        success = runner.run_security_tests(args.verbose)
    elif args.suite == "quality":
        success = runner.run_code_quality_checks(args.verbose)
    elif args.suite == "ci":
        success = runner.run_ci_tests(args.verbose)
    else:  # all
        success = runner.run_all_tests(args.verbose, args.skip_slow)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()