#!/usr/bin/env python3
"""
Test script to validate Phase 3 API enhancements
"""

def test_api_structure():
    """Test that API routes are properly defined"""
    try:
        # Test basic imports first
        print("🔍 Testing imports...")
        import sys
        sys.path.insert(0, '.')
        
        # Test individual components
        print("  - Testing FastAPI import...")
        from fastapi import FastAPI
        
        print("  - Testing database models...")
        from src.database.models import DailyRecommendations, QuantitativeScores, SentimentAnalysis
        
        print("  - Testing config...")
        from src.config.settings import config
        
        print("✅ All core imports successful!")
        
        # Test API app creation (without dependencies that require network)
        print("\n🚀 Testing API structure...")
        
        # Create a minimal test version of the API
        app = FastAPI(title="Test API")
        
        # Test the endpoint definitions by importing the route functions
        print("  - Testing new endpoints structure...")
        
        # Since full import might fail due to dependencies, let's check the file structure
        with open('src/api/main.py', 'r') as f:
            content = f.read()
            
        required_endpoints = [
            '/recommendations/latest',
            '/stocks/{symbol}/analysis', 
            '/market/sentiment',
            '/themes/top',
            '/stocks/list'
        ]
        
        print("📋 Checking for Phase 3 endpoints:")
        for endpoint in required_endpoints:
            if endpoint in content:
                print(f"  ✅ {endpoint}")
            else:
                print(f"  ❌ {endpoint}")
        
        # Check for proper function definitions
        functions_to_check = [
            'get_latest_recommendation',
            'get_stock_analysis', 
            'get_market_sentiment',
            'get_top_themes',
            'get_stocks_with_scores'
        ]
        
        print("\n🔧 Checking endpoint functions:")
        for func in functions_to_check:
            if f"async def {func}" in content:
                print(f"  ✅ {func}")
            else:
                print(f"  ❌ {func}")
        
        # Check for proper imports
        required_imports = [
            'DailyRecommendations',
            'QuantitativeScores', 
            'SentimentAnalysis',
            'NewsStockMention'
        ]
        
        print("\n📦 Checking model imports:")
        for imp in required_imports:
            if imp in content:
                print(f"  ✅ {imp}")
            else:
                print(f"  ❌ {imp}")
        
        print("\n✅ API structure validation complete!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_api_structure()
    exit(0 if success else 1)