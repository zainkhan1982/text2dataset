import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    print("Testing module imports...")
    try:
        from preprocess import clean_text, split_sentences
        print("Preprocessing module: OK")
    except Exception as e:
        print(f"Preprocessing module error: {e}")
        return False
        
    try:
        from labeling_fast import label_entities_fast
        print("Fast labeling module: OK")
    except Exception as e:
        print(f"Fast labeling module error: {e}")
        return False
        
    try:
        from labeling_smart import label_entities_smart
        print("Smart labeling module: OK")
    except Exception as e:
        print(f"Smart labeling module error: {e}")
        return False
        
    try:
        from exporter import export_to_csv, export_to_json
        print("Exporter module: OK")
    except Exception as e:
        print(f"Exporter module error: {e}")
        return False
        
    try:
        from app import app
        print("App module: OK")
    except Exception as e:
        print(f"App module error: {e}")
        return False
        
    return True

def test_simple_functionality():
    print("\nTesting simple functionality...")
    try:
        from preprocess import clean_text, split_sentences
        
        # Test cleaning
        text = "  Hello    world!   This is a test.   "
        cleaned = clean_text(text)
        expected = "Hello world! This is a test."
        assert cleaned == expected, f"Expected '{expected}', got '{cleaned}'"
        print("Text cleaning: OK")
        
        # Test sentence splitting
        sentences = split_sentences(cleaned)
        expected = ["Hello world!", "This is a test."]
        assert sentences == expected, f"Expected {expected}, got {sentences}"
        print("Sentence splitting: OK")
        
        print("Simple functionality tests: OK")
        return True
    except Exception as e:
        print(f"Simple functionality test error: {e}")
        return False

if __name__ == "__main__":
    print("Running quick Text2Dataset tests...\n")
    
    import_result = test_imports()
    functionality_result = test_simple_functionality()
    
    if import_result and functionality_result:
        print("\nAll quick tests passed! The application structure is correct.")
    else:
        print("\nSome tests failed. Please check the errors above.")