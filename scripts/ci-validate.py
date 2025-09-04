#!/usr/bin/env python3
"""
Simple CI validation script - less strict than local validation
"""

import subprocess
import sys


def run_command(cmd: str, description: str) -> bool:
    """Run a command and return success status"""
    print(f"🔍 {description}...")
    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"✅ {description} - OK")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ {description} - FAILED")
        return False


def main():
    """Main validation function for CI"""
    print("🚀 Starting CI validation...")
    print("=" * 50)

    # Critical checks for CI/CD
    checks = [
        ("uv run python scripts/run_tests.py --unit", "Unit tests"),
        ("docker build -f docker/Dockerfile -t karma-mcp:ci .", "Docker build"),
    ]

    failed_checks = []

    for cmd, desc in checks:
        if not run_command(cmd, desc):
            failed_checks.append(desc)

    print("\n" + "=" * 50)

    if failed_checks:
        print(f"❌ CI Validation FAILED! {len(failed_checks)} checks failed:")
        for check in failed_checks:
            print(f"   - {check}")
        sys.exit(1)
    else:
        print("✅ CI Validation PASSED!")
        print("🚀 Ready for deployment!")


if __name__ == "__main__":
    main()