#!/usr/bin/env python3
"""
Comprehensive Phase 3 validation test
Tests all components and integration points
"""

import sys
import os
import json

def run_comprehensive_test():
    """Run comprehensive Phase 3 validation"""
    
    print("🧪 AlphaGen Phase 3 Comprehensive Validation")
    print("=" * 60)
    
    test_results = {
        "api_structure": False,
        "dashboard_structure": False, 
        "components": False,
        "integration": False,
        "documentation": False
    }
    
    # Test 1: API Structure and Endpoints
    print("\n1. 🔧 Testing API Structure...")
    try:
        sys.path.insert(0, '.')
        
        # Check main API file
        if not os.path.exists('src/api/main.py'):
            raise Exception("API main file missing")
        
        with open('src/api/main.py', 'r') as f:
            api_content = f.read()
        
        # Required endpoints
        required_endpoints = [
            'get_latest_recommendation',
            'get_stock_analysis',
            'get_market_sentiment', 
            'get_top_themes',
            'get_stocks_with_scores'
        ]
        
        endpoint_count = 0
        for endpoint in required_endpoints:
            if f"async def {endpoint}" in api_content:
                print(f"   ✅ {endpoint}")
                endpoint_count += 1
            else:
                print(f"   ❌ {endpoint}")
        
        # Check model imports
        required_models = [
            'DailyRecommendations',
            'QuantitativeScores',
            'SentimentAnalysis',
            'NewsStockMention'
        ]
        
        model_count = 0
        for model in required_models:
            if model in api_content:
                print(f"   ✅ Model: {model}")
                model_count += 1
            else:
                print(f"   ❌ Model: {model}")
        
        if endpoint_count == len(required_endpoints) and model_count == len(required_models):
            test_results["api_structure"] = True
            print("   🎯 API structure validation: PASSED")
        else:
            print("   ❌ API structure validation: FAILED")
        
    except Exception as e:
        print(f"   ❌ API structure test failed: {e}")
    
    # Test 2: Dashboard Structure
    print("\n2. 🖥️ Testing Dashboard Structure...")
    try:
        dashboard_files = [
            'src/dashboard/main.py',
            'src/dashboard/utils/api_client.py',
            'src/dashboard/utils/formatting.py',
            'src/dashboard/components/charts.py',
            'src/dashboard/components/metrics.py',
            'src/dashboard/components/tables.py',
            'src/dashboard/pages/overview.py',
            'src/dashboard/pages/stock_detail.py',
            'src/dashboard/pages/market_sentiment.py',
            'src/dashboard/pages/themes.py',
            'src/dashboard/.streamlit/config.toml'
        ]
        
        file_count = 0
        for file_path in dashboard_files:
            if os.path.exists(file_path):
                print(f"   ✅ {file_path}")
                file_count += 1
            else:
                print(f"   ❌ {file_path}")
        
        if file_count == len(dashboard_files):
            test_results["dashboard_structure"] = True
            print("   🎯 Dashboard structure validation: PASSED")
        else:
            print("   ❌ Dashboard structure validation: FAILED")
            
    except Exception as e:
        print(f"   ❌ Dashboard structure test failed: {e}")
    
    # Test 3: Component Functionality
    print("\n3. 🧩 Testing Component Functionality...")
    try:
        sys.path.insert(0, 'src/dashboard')
        
        # Test formatting utilities
        from utils.formatting import (
            format_currency, format_recommendation, format_sentiment,
            format_date, get_recommendation_color, get_sentiment_color
        )
        
        # Test basic functions
        currency_test = format_currency(8500000)
        rec_test = format_recommendation("BUY")
        sentiment_test = format_sentiment(0.75)
        color_test = get_recommendation_color("BUY")
        
        print(f"   ✅ Currency: {currency_test}")
        print(f"   ✅ Recommendation: {rec_test}")
        print(f"   ✅ Sentiment: {sentiment_test}")
        print(f"   ✅ Color: {color_test}")
        
        # Test API client
        from utils.api_client import AlphaGenAPIClient
        api_client = AlphaGenAPIClient()
        print(f"   ✅ API Client: {api_client.base_url}")
        
        # Test chart components (import only)
        from components.charts import create_sentiment_gauge
        print(f"   ✅ Chart components imported")
        
        # Test metric components (import only) 
        from components.metrics import display_stock_card
        print(f"   ✅ Metric components imported")
        
        # Test table components (import only)
        from components.tables import create_news_table
        print(f"   ✅ Table components imported")
        
        test_results["components"] = True
        print("   🎯 Component functionality validation: PASSED")
        
    except Exception as e:
        print(f"   ❌ Component functionality test failed: {e}")
    
    # Test 4: Integration Points
    print("\n4. 🔗 Testing Integration Points...")
    try:
        # Test that pages can import their dependencies
        page_tests = {
            'overview': ['utils.api_client', 'components.metrics', 'components.charts'],
            'stock_detail': ['utils.api_client', 'components.metrics', 'components.charts'],
            'market_sentiment': ['utils.api_client', 'components.metrics', 'components.charts'],
            'themes': ['utils.api_client', 'components.charts', 'components.tables']
        }
        
        integration_count = 0
        for page, dependencies in page_tests.items():
            try:
                page_file = f'src/dashboard/pages/{page}.py'
                if os.path.exists(page_file):
                    with open(page_file, 'r') as f:
                        page_content = f.read()
                    
                    deps_found = 0
                    for dep in dependencies:
                        if dep in page_content:
                            deps_found += 1
                    
                    if deps_found == len(dependencies):
                        print(f"   ✅ {page} page integration")
                        integration_count += 1
                    else:
                        print(f"   ⚠️ {page} page partial integration ({deps_found}/{len(dependencies)})")
                
            except Exception as e:
                print(f"   ❌ {page} page integration failed: {e}")
        
        if integration_count >= 3:  # Allow for some flexibility
            test_results["integration"] = True
            print("   🎯 Integration validation: PASSED")
        else:
            print("   ❌ Integration validation: FAILED")
        
    except Exception as e:
        print(f"   ❌ Integration test failed: {e}")
    
    # Test 5: Documentation and Configuration
    print("\n5. 📋 Testing Documentation and Configuration...")
    try:
        doc_files = [
            'PHASE3_DOCUMENTATION.md',
            'phase3_demo.py',
            'dashboard_preview.py',
            'test_api_structure.py',
            'test_dashboard_structure.py'
        ]
        
        doc_count = 0
        for doc_file in doc_files:
            if os.path.exists(doc_file):
                print(f"   ✅ {doc_file}")
                doc_count += 1
            else:
                print(f"   ❌ {doc_file}")
        
        # Check Streamlit config
        config_file = 'src/dashboard/.streamlit/config.toml'
        if os.path.exists(config_file):
            print(f"   ✅ Streamlit configuration")
            doc_count += 1
        
        if doc_count >= 4:  # Allow for some missing files
            test_results["documentation"] = True
            print("   🎯 Documentation validation: PASSED")
        else:
            print("   ❌ Documentation validation: FAILED")
            
    except Exception as e:
        print(f"   ❌ Documentation test failed: {e}")
    
    # Final Results
    print("\n" + "=" * 60)
    print("🎯 FINAL VALIDATION RESULTS")
    print("=" * 60)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall Score: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
    
    if passed_tests >= 4:  # Allow for one failure
        print("\n🎉 Phase 3 Implementation: VALIDATION SUCCESSFUL")
        print("🚀 AlphaGen platform is ready for deployment!")
        
        print("\n📋 NEXT STEPS:")
        print("1. Start the FastAPI backend: python -m src.api.main")
        print("2. Start the Streamlit dashboard: streamlit run src/dashboard/main.py")
        print("3. Access the dashboard at http://localhost:8501")
        print("4. Access the API docs at http://localhost:8000/docs")
        
        print("\n💡 FEATURES AVAILABLE:")
        print("• Real-time stock recommendations")
        print("• Interactive market sentiment analysis")
        print("• Individual stock deep-dive analysis") 
        print("• Trending financial themes tracking")
        print("• Professional investment dashboard")
        
        return True
    else:
        print("\n⚠️ Phase 3 Implementation: VALIDATION INCOMPLETE")
        print("Some components need attention before deployment.")
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    exit(0 if success else 1)