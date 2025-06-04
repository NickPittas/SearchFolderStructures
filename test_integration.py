#!/usr/bin/env python3
"""
Quick integration test for the AI File Organizer with dual provider support.
This script verifies that both Ollama and OpenRouter providers can be instantiated.
"""

import sys
import os

# Add current directory to path to import the main module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    try:
        import requests
        print("✓ requests library available")
        
        from FIelOrganizer import OpenRouterLLM, OPENROUTER_MODELS
        print("✓ OpenRouterLLM class imported successfully")
        print(f"✓ {len(OPENROUTER_MODELS)} OpenRouter models defined")
        
        from langchain_ollama.llms import OllamaLLM
        print("✓ OllamaLLM class imported successfully")
        
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_openrouter_class():
    """Test OpenRouter class instantiation."""
    print("\nTesting OpenRouter class...")
    try:
        from FIelOrganizer import OpenRouterLLM
        
        # Test instantiation (with dummy API key)
        llm = OpenRouterLLM(
            model="anthropic/claude-3.5-sonnet", 
            api_key="dummy-key-for-testing"
        )
        
        print("✓ OpenRouterLLM instantiated successfully")
        print(f"✓ Model: {llm.model}")
        print(f"✓ Base URL: {llm.base_url}")
        
        return True
    except Exception as e:
        print(f"✗ OpenRouter test failed: {e}")
        return False

def test_ollama_class():
    """Test Ollama class instantiation."""
    print("\nTesting Ollama class...")
    try:
        from langchain_ollama.llms import OllamaLLM
        
        # Test instantiation
        llm = OllamaLLM(
            model="test-model", 
            base_url="http://localhost:11434"
        )
        
        print("✓ OllamaLLM instantiated successfully")
        print(f"✓ Model: {llm.model}")
        print(f"✓ Base URL: {llm.base_url}")
        
        return True
    except Exception as e:
        print(f"✗ Ollama test failed: {e}")
        return False

def test_gui_imports():
    """Test GUI components can be imported."""
    print("\nTesting GUI imports...")
    try:
        from PyQt5.QtWidgets import QApplication, QGroupBox
        print("✓ PyQt5 widgets imported successfully")
        
        from FIelOrganizer import FileClassifierApp
        print("✓ FileClassifierApp class imported successfully")
        
        return True
    except ImportError as e:
        print(f"✗ GUI import error: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 AI File Organizer Integration Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_openrouter_class,
        test_ollama_class,
        test_gui_imports
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"✓ Passed: {sum(results)}/{len(results)}")
    print(f"✗ Failed: {len(results) - sum(results)}/{len(results)}")
    
    if all(results):
        print("\n🎉 All tests passed! The integration looks good.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
