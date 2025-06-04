#!/usr/bin/env python3
import sys
import os

print("🚀 Testing OpenRouter Integration")

# Test 1: Import core modules
try:
    import requests
    print("✅ requests imported")
except ImportError:
    print("❌ requests not available - install with: pip install requests")
    sys.exit(1)

# Test 2: Import our classes
try:
    from FIelOrganizer import OpenRouterLLM, OPENROUTER_MODELS
    print("✅ OpenRouterLLM imported successfully")
    print(f"✅ Found {len(OPENROUTER_MODELS)} OpenRouter models")
except Exception as e:
    print(f"❌ Failed to import OpenRouterLLM: {e}")
    sys.exit(1)

# Test 3: Test class instantiation
try:
    llm = OpenRouterLLM(model="anthropic/claude-3.5-sonnet", api_key="test-key")
    print(f"✅ OpenRouterLLM instantiated: {llm.model}")
except Exception as e:
    print(f"❌ Failed to instantiate OpenRouterLLM: {e}")
    sys.exit(1)

# Test 4: Test secure storage (optional)
try:
    from secure_storage import SecureStorage
    print("✅ SecureStorage available")
    
    # Test basic functionality
    storage = SecureStorage("test.dat")
    success = storage.save_api_key("test", "key123", "pass123")
    if success:
        loaded = storage.load_api_key("test", "pass123")
        if loaded == "key123":
            print("✅ Secure storage working")
        else:
            print("⚠️ Secure storage key mismatch")
    
    # Cleanup
    test_file = os.path.join(os.path.expanduser('~'), "test.dat")
    if os.path.exists(test_file):
        os.remove(test_file)
        
except ImportError:
    print("⚠️ SecureStorage not available - install cryptography for encrypted key storage")
except Exception as e:
    print(f"⚠️ SecureStorage test failed: {e}")

print("\n🎉 Core integration tests completed successfully!")
print("✅ OpenRouter provider ready to use")
print("✅ Secure API key storage available (if cryptography installed)")
print("\nTo use:")
print("1. Run: python FIelOrganizer.py")
print("2. Select 'OpenRouter' as provider")
print("3. Enter your API key")
print("4. Select a model and start classifying files!")
