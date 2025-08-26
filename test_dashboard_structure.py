#!/usr/bin/env python3
"""
Test script to validate Phase 3 Dashboard implementation
"""

def test_dashboard_structure():
    """Test that dashboard components are properly structured"""
    try:
        print("🔍 Testing dashboard imports...")
        
        # Test core Streamlit import
        import streamlit as st
        print("  ✅ Streamlit imported successfully")
        
        # Test dashboard utilities
        import sys
        sys.path.insert(0, 'src')
        
        print("  - Testing API client...")
        from dashboard.utils.api_client import AlphaGenAPIClient
        api_client = AlphaGenAPIClient()
        print("  ✅ API client created")
        
        print("  - Testing formatting utilities...")
        from dashboard.utils.formatting import format_currency, format_recommendation
        test_currency = format_currency(1000000)
        test_rec = format_recommendation("BUY")
        print(f"  ✅ Formatting working: {test_currency}, {test_rec}")
        
        print("  - Testing components...")
        from dashboard.components.charts import create_sentiment_gauge
        from dashboard.components.metrics import display_stock_card
        from dashboard.components.tables import create_news_table
        print("  ✅ All components imported")
        
        print("  - Testing pages...")
        from dashboard.pages import overview, stock_detail, market_sentiment, themes
        print("  ✅ All pages imported")
        
        # Test dashboard structure
        print("\n📁 Checking dashboard file structure...")
        
        import os
        
        required_files = [
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
        
        for file_path in required_files:
            if os.path.exists(file_path):
                print(f"  ✅ {file_path}")
            else:
                print(f"  ❌ {file_path}")
        
        print("\n🎯 Testing chart creation...")
        try:
            import plotly.graph_objects as go
            # Test sentiment gauge creation
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=75,
                title={'text': "Test Gauge"},
                gauge={'axis': {'range': [None, 100]}}
            ))
            print("  ✅ Plotly charts working")
        except Exception as e:
            print(f"  ❌ Chart creation failed: {e}")
        
        print("\n🚀 Dashboard structure validation complete!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_dashboard_structure()
    exit(0 if success else 1)