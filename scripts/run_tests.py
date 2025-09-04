#!/usr/bin/env python3
"""
Test runner script for Karma MCP server
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, cwd=None, env=None):
    """Run a command and return the result"""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)

    return result.returncode == 0


def run_unit_tests(verbose=False, coverage=False):
    """Run unit tests"""
    print("\n🧪 Running Unit Tests")
    print("=" * 50)

    cmd = ["python", "-m", "pytest", "tests/unit/"]

    if verbose:
        cmd.append("-v")

    if coverage:
        cmd.extend(["--cov=src/karma_mcp", "--cov-report=term-missing"])

    return run_command(cmd)


def run_integration_tests(karma_url=None, verbose=False):
    """Run integration tests"""
    print("\n🔗 Running Integration Tests")
    print("=" * 50)

    if not karma_url:
        print("⚠️  No KARMA_URL provided - integration tests will be skipped")
        karma_url = "http://localhost:8080"  # This will cause tests to be skipped
    else:
        print(f"Testing against Karma instance: {karma_url}")

    env = os.environ.copy()
    env["KARMA_URL"] = karma_url

    cmd = ["python", "-m", "pytest", "tests/integration/"]

    if verbose:
        cmd.append("-v")

    return run_command(cmd, env=env)


def run_all_tests(karma_url=None, verbose=False, coverage=False):
    """Run all tests"""
    print("\n🚀 Running All Tests")
    print("=" * 50)

    # Set up environment
    env = os.environ.copy()
    if karma_url:
        env["KARMA_URL"] = karma_url
        print(f"Using Karma URL: {karma_url}")

    cmd = ["python", "-m", "pytest"]

    if verbose:
        cmd.append("-v")

    if coverage:
        cmd.extend(
            ["--cov=src/karma_mcp", "--cov-report=term-missing", "--cov-report=html"]
        )

    return run_command(cmd, env=env)


def run_linting():
    """Run linting checks"""
    print("\n✨ Running Linting Checks")
    print("=" * 50)

    success = True

    # Check if ruff is available
    try:
        subprocess.run(["ruff", "--version"], capture_output=True, check=True)
        print("Running ruff...")
        if not run_command(["ruff", "check", "src/", "tests/"]):
            success = False
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  ruff not found - skipping linting")

    return success


def run_type_checking():
    """Run type checking"""
    print("\n🔍 Running Type Checking")
    print("=" * 50)

    try:
        subprocess.run(["mypy", "--version"], capture_output=True, check=True)
        print("Running mypy...")
        return run_command(["mypy", "src/"])
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  mypy not found - skipping type checking")
        return True


def generate_coverage_report():
    """Generate coverage report"""
    print("\n📊 Generating Coverage Report")
    print("=" * 50)

    if not run_command(
        ["python", "-m", "pytest", "--cov=src/karma_mcp", "--cov-report=html"]
    ):
        return False

    print("\n✅ Coverage report generated in htmlcov/")
    return True


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="Run Karma MCP server tests")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument(
        "--integration", action="store_true", help="Run only integration tests"
    )
    parser.add_argument("--karma-url", help="Karma URL for integration tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--coverage", action="store_true", help="Generate coverage report"
    )
    parser.add_argument("--lint", action="store_true", help="Run linting only")
    parser.add_argument(
        "--type-check", action="store_true", help="Run type checking only"
    )
    parser.add_argument("--all", action="store_true", help="Run all tests and checks")

    args = parser.parse_args()

    # Change to project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    print(f"🏠 Working directory: {project_root}")

    success = True

    if args.lint:
        success &= run_linting()
    elif args.type_check:
        success &= run_type_checking()
    elif args.unit:
        success &= run_unit_tests(verbose=args.verbose, coverage=args.coverage)
    elif args.integration:
        success &= run_integration_tests(karma_url=args.karma_url, verbose=args.verbose)
    elif args.all:
        success &= run_linting()
        success &= run_type_checking()
        success &= run_all_tests(
            karma_url=args.karma_url, verbose=args.verbose, coverage=args.coverage
        )
    else:
        # Default: run all tests
        success &= run_all_tests(
            karma_url=args.karma_url, verbose=args.verbose, coverage=args.coverage
        )

    if args.coverage and not (args.lint or args.type_check):
        generate_coverage_report()

    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
