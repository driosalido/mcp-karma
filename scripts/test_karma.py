#!/usr/bin/env python3
"""
Quick test script for Karma MCP server
"""

import asyncio
import sys

from karma_mcp.server import check_karma, get_alerts_summary


async def test_karma():
    """Test basic Karma connectivity and functionality"""
    print("🔍 Checking Karma connectivity...")
    try:
        health = await check_karma()
        print(health)

        print("\n📋 Getting alerts summary...")
        summary = await get_alerts_summary()
        print(summary[:500] + "..." if len(summary) > 500 else summary)

        print("\n✅ Karma test completed successfully!")

    except Exception as e:
        print(f"\n❌ Error testing Karma: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(test_karma())
