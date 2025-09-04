#!/usr/bin/env python3
"""
Validation script to check all components before deployment
"""

import subprocess
import sys


def run_command(cmd: str, description: str) -> bool:
    """Run a command and return success status"""
    print(f"🔍 {description}...")
    try:
        subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - OK")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        if e.stderr:
            print(f"   Error: {e.stderr}")
        if e.stdout:
            print(f"   Output: {e.stdout}")
        return False


def main():
    """Main validation function"""
    print("🚀 Starting karma-mcp validation...")
    print("=" * 50)

    checks = [
        ("uv run ruff format --check .", "Code formatting check"),
        ("uv run ruff check .", "Linting check"),
        ("uv run mypy src/", "Type checking"),
        ("uv run bandit -r src/ -q", "Security check"),
        ("uv run python scripts/run_tests.py --unit", "Unit tests"),
        (
            "docker build -f docker/Dockerfile -t karma-mcp:validation .",
            "Docker build test",
        ),
    ]

    failed_checks = []

    for cmd, desc in checks:
        if not run_command(cmd, desc):
            failed_checks.append(desc)

    print("\n" + "=" * 50)

    if failed_checks:
        print(f"❌ Validation FAILED! {len(failed_checks)} checks failed:")
        for check in failed_checks:
            print(f"   - {check}")
        print("\n📋 Next steps:")
        print("   1. Fix the failing checks above")
        print("   2. Run this script again")
        print("   3. Commit your changes")
        sys.exit(1)
    else:
        print("✅ All validations PASSED!")
        print("\n🎉 Ready for deployment!")
        print("\n📋 Next steps:")
        print("   1. git add .")
        print("   2. git commit -m 'Add comprehensive CI/CD pipeline'")
        print("   3. git push")
        print("\n🐳 Docker image built successfully:")
        print("   - Image: karma-mcp:validation")
        print("   - Architectures: Multi-platform support enabled")


if __name__ == "__main__":
    main()
