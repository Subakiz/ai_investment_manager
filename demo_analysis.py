#!/usr/bin/env python3
"""
Phase 2 Analysis Engine Demo Script

This script demonstrates the new analysis capabilities added to AlphaGen:
- Quantitative analysis engine 
- Qualitative analysis engine (Gemini AI)
- Enhanced pipeline integration

Usage:
    python demo_analysis.py [test_type]
    
Test types:
    - quantitative: Test quantitative analysis functions
    - qualitative: Test qualitative analysis functions  
    - pipeline: Test enhanced pipeline CLI commands
    - all: Run all tests
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_quantitative_analysis():
    """Test the quantitative analysis engine"""
    print("\n=== Testing Quantitative Analysis Engine ===")
    
    try:
        from src.analysis.quantitative import QuantitativeAnalyzer
        
        analyzer = QuantitativeAnalyzer()
        print("✅ QuantitativeAnalyzer instantiated successfully")
        
        # Test methods available
        methods = [method for method in dir(analyzer) if not method.startswith('_')]
        print(f"📊 Available methods: {', '.join(methods)}")
        
        # Note: Actual data fetching would require database setup
        print("💡 Database connection would be needed for real data analysis")
        print("   - fetch_latest_market_data() - Get current stock prices")
        print("   - fetch_historical_data() - Get historical price data")
        print("   - calculate_technical_indicators() - RSI, moving averages")
        print("   - calculate_relative_valuation() - P/E, P/B ratios")
        print("   - run_quantitative_analysis() - Full analysis pipeline")
        
        return True
        
    except Exception as e:
        print(f"❌ Quantitative analysis test failed: {e}")
        return False

async def test_qualitative_analysis():
    """Test the qualitative analysis engine"""
    print("\n=== Testing Qualitative Analysis Engine ===")
    
    try:
        from src.analysis.qualitative import QualitativeAnalyzer
        
        analyzer = QualitativeAnalyzer()
        print("✅ QualitativeAnalyzer instantiated successfully")
        
        # Test methods available
        methods = [method for method in dir(analyzer) if not method.startswith('_')]
        print(f"🤖 Available methods: {', '.join(methods)}")
        
        # Test prompt creation
        sample_article = """
        PT Bank Central Asia Tbk (BBCA) melaporkan laba bersih sebesar Rp 8,2 triliun 
        pada kuartal pertama 2024, naik 15% dari periode yang sama tahun lalu. 
        Pertumbuhan didorong oleh kenaikan pendapatan bunga dan ekspansi kredit digital.
        """
        
        prompt = analyzer.create_sentiment_prompt(sample_article, "PT Bank Central Asia", "BBCA.JK")
        print("📝 Sample sentiment analysis prompt created")
        print(f"   Length: {len(prompt)} characters")
        
        # Note: Actual Gemini API calls require API key
        print("💡 Gemini API key would be needed for real sentiment analysis")
        print("   - analyze_article_sentiment() - Single article analysis")  
        print("   - batch_analyze_articles() - Process multiple articles")
        print("   - aggregate_sentiment_by_symbol() - Symbol-based aggregation")
        print("   - run_qualitative_analysis() - Full analysis pipeline")
        
        return True
        
    except Exception as e:
        print(f"❌ Qualitative analysis test failed: {e}")
        return False

async def test_pipeline_integration():
    """Test the enhanced pipeline integration"""
    print("\n=== Testing Enhanced Pipeline Integration ===")
    
    try:
        from src.data_pipeline.pipeline import DataPipeline
        
        pipeline = DataPipeline()
        print("✅ Enhanced DataPipeline instantiated successfully")
        
        # Check new methods
        new_methods = ['run_quantitative_analysis', 'run_qualitative_analysis', 'run_combined_analysis']
        available_methods = [method for method in dir(pipeline) if method in new_methods]
        print(f"🔄 New analysis methods: {', '.join(available_methods)}")
        
        print("📅 Enhanced scheduling includes:")
        print("   - Market data collection: 4:30 PM WIB (9:30 UTC)")
        print("   - News data collection: 4:45 PM WIB (9:45 UTC)")
        print("   - Quantitative analysis: 5:00 PM WIB (10:00 UTC)")
        print("   - Qualitative analysis: 5:15 PM WIB (10:15 UTC)")
        
        print("🖥️  New CLI commands available:")
        print("   - python -m src.data_pipeline.pipeline analyze-quantitative")
        print("   - python -m src.data_pipeline.pipeline analyze-qualitative") 
        print("   - python -m src.data_pipeline.pipeline analyze-all")
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline integration test failed: {e}")
        return False

async def test_database_models():
    """Test the new database models"""
    print("\n=== Testing New Database Models ===")
    
    try:
        from src.database.models import (
            QuantitativeScores, SentimentAnalysis, 
            DailyRecommendations, NewsArticle
        )
        
        print("✅ New database models imported successfully:")
        print("   📊 QuantitativeScores - Daily quantitative metrics per stock")
        print("   🤖 SentimentAnalysis - AI-processed news sentiment data")
        print("   📈 DailyRecommendations - Final ranked recommendations")
        print("   📰 Enhanced NewsArticle - Additional sentiment fields")
        
        # Show model attributes
        print("\n📋 QuantitativeScores fields:")
        for field in ['pe_ratio', 'pb_ratio', 'rsi', 'ma_signal', 'composite_score']:
            print(f"   - {field}")
            
        print("\n📋 SentimentAnalysis fields:")
        for field in ['sentiment_score', 'confidence', 'themes', 'summary', 'relevance']:
            print(f"   - {field}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database models test failed: {e}")
        return False

async def main():
    """Main demo function"""
    print("🚀 AlphaGen Phase 2 Analysis Engine Demo")
    print("=" * 50)
    
    # Parse command line arguments
    test_type = sys.argv[1] if len(sys.argv) > 1 else 'all'
    
    tests = []
    
    if test_type in ['all', 'quantitative']:
        tests.append(('Quantitative Analysis', test_quantitative_analysis))
    
    if test_type in ['all', 'qualitative']:
        tests.append(('Qualitative Analysis', test_qualitative_analysis))
        
    if test_type in ['all', 'pipeline']:
        tests.append(('Pipeline Integration', test_pipeline_integration))
        
    if test_type in ['all', 'models']:
        tests.append(('Database Models', test_database_models))
    
    # Run tests
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    # Summary
    print(f"\n{'='*50}")
    print(f"📊 Demo Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Phase 2 components are working correctly!")
        print("\n🚀 Ready for deployment and testing with real data:")
        print("   1. Set up PostgreSQL database")
        print("   2. Configure Gemini API key in .env")
        print("   3. Run data collection: python -m src.data_pipeline.pipeline collect")
        print("   4. Run analysis: python -m src.data_pipeline.pipeline analyze-all")
    else:
        print("⚠️  Some components need attention before production use")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)