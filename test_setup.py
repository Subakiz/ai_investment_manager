#!/usr/bin/env python3
"""
Simple validation test for AlphaGen setup
"""
import sys
import importlib.util
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all required modules can be imported"""
    modules_to_test = [
        'src.config.settings',
        'src.data_pipeline.lq45_stocks',
        'src.database.models',
        'src.utils.logger',
    ]
    
    print("Testing module imports...")
    
    for module_name in modules_to_test:
        try:
            module = importlib.import_module(module_name)
            print(f"✅ {module_name}")
        except ImportError as e:
            print(f"❌ {module_name}: {e}")
            return False
    
    return True

def test_lq45_stocks():
    """Test LQ45 stocks configuration"""
    try:
        from src.data_pipeline.lq45_stocks import get_lq45_symbols, LQ45_STOCKS
        
        symbols = get_lq45_symbols()
        print(f"\n✅ LQ45 stocks loaded: {len(symbols)} symbols")
        print(f"Sample stocks: {symbols[:5]}")
        
        # Verify all symbols end with .JK
        invalid_symbols = [s for s in symbols if not s.endswith('.JK')]
        if invalid_symbols:
            print(f"❌ Invalid symbols found: {invalid_symbols}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ LQ45 stocks test failed: {e}")
        return False

def test_config():
    """Test configuration"""
    try:
        from src.config.settings import config
        
        print(f"\n✅ Configuration loaded")
        print(f"Database URL: {config.database_url}")
        print(f"Environment: {config.ENVIRONMENT}")
        print(f"Log level: {config.LOG_LEVEL}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 AlphaGen Setup Validation Test\n")
    
    tests = [
        ("Module Imports", test_imports),
        ("LQ45 Stocks", test_lq45_stocks),
        ("Configuration", test_config),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print(f"\n{'='*50}")
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Setup looks good.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the setup.")
        return 1

if __name__ == "__main__":
    sys.exit(main())