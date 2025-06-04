#!/usr/bin/env python3
"""
Test script for AI File Organizer OpenRouter integration
"""

import sys
import os

def test_imports():
    """Test that all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        import requests
        print("✅ requests imported")
    except ImportError as e:
        print(f"❌ requests import failed: {e}")
        return False
    
    try:
        from secure_storage import SecureStorage
        print("✅ SecureStorage imported")
    except ImportError as e:
        print(f"❌ SecureStorage import failed: {e}")
        return False
    
    try:
        import cryptography
        print(f"✅ cryptography version: {cryptography.__version__}")
    except ImportError as e:
        print(f"⚠️ cryptography not available: {e}")
        print("   Install with: pip install cryptography")
    
    return True

def test_openrouter_class():
    """Test OpenRouter LLM class instantiation"""
    print("\n🧪 Testing OpenRouter class...")
    
    try:
        # Import the class from our main file
        sys.path.insert(0, os.path.dirname(__file__))
        from FIelOrganizer import OpenRouterLLM, OPENROUTER_MODELS
        
        # Test class instantiation
        api_key = "test-key-123"
        model = OPENROUTER_MODELS[0]  # Claude 3.5 Sonnet
        
        llm = OpenRouterLLM(model=model, api_key=api_key)
        print(f"✅ OpenRouterLLM instantiated with model: {llm.model}")
        print(f"✅ API endpoint: {llm.base_url}")
        print(f"✅ Available models: {len(OPENROUTER_MODELS)} models")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenRouter class test failed: {e}")
        return False

def test_secure_storage():
    """Test secure storage functionality"""
    print("\n🧪 Testing secure storage...")
    
    try:
        from secure_storage import SecureStorage
        
        # Create test storage
        test_file = "test_secure_storage.dat"
        storage = SecureStorage(test_file)
        
        # Test data
        test_password = "test_password_123"
        test_api_key = "sk-test123456789abcdef"
        service_name = "test_service"
        
        # Test save
        success = storage.save_api_key(service_name, test_api_key, test_password)
        if success:
            print("✅ API key saved successfully")
        else:
            print("❌ Failed to save API key")
            return False
        
        # Test load
        loaded_key = storage.load_api_key(service_name, test_password)
        if loaded_key == test_api_key:
            print("✅ API key loaded successfully")
        else:
            print(f"❌ API key mismatch: expected {test_api_key}, got {loaded_key}")
            return False
        
        # Test wrong password
        wrong_key = storage.load_api_key(service_name, "wrong_password")
        if wrong_key is None:
            print("✅ Wrong password correctly rejected")
        else:
            print("❌ Wrong password should have been rejected")
            return False
        
        # Cleanup
        test_path = os.path.join(os.path.expanduser('~'), test_file)
        if os.path.exists(test_path):
            os.remove(test_path)
            print("✅ Cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Secure storage test failed: {e}")
        return False

def test_models_list():
    """Test that our models list is properly formatted"""
    print("\n🧪 Testing models list...")
    
    try:
        from FIelOrganizer import OPENROUTER_MODELS
        
        if not OPENROUTER_MODELS:
            print("❌ Models list is empty")
            return False
        
        print(f"✅ Found {len(OPENROUTER_MODELS)} models")
        
        # Check format of each model
        for i, model in enumerate(OPENROUTER_MODELS[:5]):  # Check first 5
            if '/' in model:
                provider, model_name = model.split('/', 1)
                print(f"✅ Model {i+1}: {provider}/{model_name}")
            else:
                print(f"⚠️ Model {i+1}: {model} (unusual format)")
        
        if len(OPENROUTER_MODELS) > 5:
            print(f"... and {len(OPENROUTER_MODELS) - 5} more models")
        
        return True
        
    except Exception as e:
        print(f"❌ Models list test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 AI File Organizer - OpenRouter Integration Tests")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("OpenRouter Class", test_openrouter_class),
        ("Secure Storage", test_secure_storage),
        ("Models List", test_models_list),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'=' * 20} {test_name} {'=' * 20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} CRASHED: {e}")
    
    print(f"\n{'=' * 50}")
    print(f"🏁 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! OpenRouter integration is ready.")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
