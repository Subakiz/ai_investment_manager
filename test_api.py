#!/usr/bin/env python3
"""
Test script for AlphaGen Phase 3 API endpoints
"""
import asyncio
import aiohttp
import json
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000"

async def test_endpoint(session, method, endpoint, data=None):
    """Test a single API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method.upper() == "GET":
            async with session.get(url) as response:
                return response.status, await response.json()
        elif method.upper() == "POST":
            async with session.post(url, json=data) as response:
                return response.status, await response.json()
    except Exception as e:
        return None, str(e)

async def main():
    """Run all API endpoint tests"""
    print("🧪 Testing AlphaGen Phase 3 API Endpoints")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # Test basic endpoints
        tests = [
            ("GET", "/", "Root endpoint"),
            ("GET", "/health", "Health check"),
            ("GET", "/config", "Configuration"),
            ("GET", "/stocks", "Stock list"),
        ]
        
        # Phase 3 specific endpoints (these will likely fail without data)
        phase3_tests = [
            ("GET", "/api/v1/recommendations/", "Latest recommendations"),
            ("GET", "/api/v1/recommendations/BBCA", "BBCA recommendation"),
            ("GET", "/api/v1/scores/quantitative/BBCA", "BBCA quantitative scores"),
            ("GET", "/api/v1/scores/qualitative/BBCA", "BBCA qualitative scores"),
            ("GET", "/api/v1/history/scores/BBCA?days=30", "BBCA historical scores"),
            ("GET", "/api/v1/risk/BBCA", "BBCA risk analysis"),
            ("GET", "/api/v1/portfolio/test_portfolio", "Portfolio view"),
        ]
        
        print("🔍 Testing Basic Endpoints:")
        for method, endpoint, description in tests:
            status, response = await test_endpoint(session, method, endpoint)
            status_color = "🟢" if status and 200 <= status < 300 else "🔴"
            print(f"  {status_color} {method} {endpoint} - {description}")
            if status:
                print(f"     Status: {status}")
            else:
                print(f"     Error: {response}")
        
        print("\n🚀 Testing Phase 3 Endpoints:")
        for method, endpoint, description in phase3_tests:
            status, response = await test_endpoint(session, method, endpoint)
            status_color = "🟢" if status and 200 <= status < 300 else "🔴"
            print(f"  {status_color} {method} {endpoint} - {description}")
            if status:
                print(f"     Status: {status}")
                if status == 404:
                    print(f"     Note: 404 expected if no data exists yet")
            else:
                print(f"     Error: {response}")
        
        # Test portfolio creation
        print("\n📊 Testing Portfolio Management:")
        trade_data = {
            "action": "BUY",
            "symbol": "BBCA",
            "quantity": 100,
            "price": 8500.0,
            "notes": "Test trade"
        }
        
        status, response = await test_endpoint(
            session, "POST", "/api/v1/portfolio/test_portfolio/trade", trade_data
        )
        status_color = "🟢" if status and 200 <= status < 300 else "🔴"
        print(f"  {status_color} POST /api/v1/portfolio/test_portfolio/trade - Create trade")
        if status:
            print(f"     Status: {status}")
            if 200 <= status < 300:
                print("     ✅ Trade created successfully!")
        else:
            print(f"     Error: {response}")

    print("\n" + "=" * 50)
    print("🎯 Test Summary:")
    print("- Basic endpoints should return 200 if API is running")
    print("- Phase 3 endpoints may return 404 if database is empty")
    print("- Portfolio endpoints may return 404 if stock symbols don't exist")
    print("- All endpoints should return valid JSON responses")
    print("\n💡 Tip: Populate database with sample data for full testing")

if __name__ == "__main__":
    asyncio.run(main())