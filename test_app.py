import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_preprocessing():
    print("Testing preprocessing module...")
    try:
        from preprocess import clean_text, split_sentences
        text = "Hello world! This is a test. How are you?"
        cleaned = clean_text(text)
        sentences = split_sentences(cleaned)
        print(f"Original: {text}")
        print(f"Cleaned: {cleaned}")
        print(f"Sentences: {sentences}")
        print("Preprocessing module: OK")
        return True
    except Exception as e:
        print(f"Preprocessing module error: {e}")
        return False

def test_fast_labeling():
    print("\nTesting fast labeling module...")
    try:
        from labeling_fast import label_entities_fast
        sentences = ["Apple Inc. was founded by Steve Jobs in California."]
        result = label_entities_fast(sentences)
        print(f"Input sentences: {sentences}")
        print(f"Labeling result: {result}")
        print("Fast labeling module: OK")
        return True
    except Exception as e:
        print(f"Fast labeling module error: {e}")
        return False

def test_smart_labeling():
    print("\nTesting smart labeling module...")
    try:
        from labeling_smart import label_entities_smart
        sentences = ["Apple Inc. was founded by Steve Jobs in California."]
        result = label_entities_smart(sentences)
        print(f"Input sentences: {sentences}")
        print(f"Labeling result: {result}")
        print("Smart labeling module: OK")
        return True
    except Exception as e:
        print(f"Smart labeling module error: {e}")
        return False

def test_exporter():
    print("\nTesting exporter module...")
    try:
        from exporter import export_to_csv, export_to_json
        import pandas as pd
        import os
        
        # Create test data
        data = [
            {"text": "Apple Inc. was founded by Steve Jobs.", "entity": "Apple Inc.", "label": "ORG"},
            {"text": "Apple Inc. was founded by Steve Jobs.", "entity": "Steve Jobs", "label": "PERSON"}
        ]
        df = pd.DataFrame(data)
        
        # Test CSV export
        export_to_csv(df, "test_output.csv")
        print("CSV export: OK")
        
        # Test JSON export
        export_to_json(df, "test_output.json")
        print("JSON export: OK")
        
        # Clean up test files
        if os.path.exists("test_output.csv"):
            os.remove("test_output.csv")
        if os.path.exists("test_output.json"):
            os.remove("test_output.json")
            
        print("Exporter module: OK")
        return True
    except Exception as e:
        print(f"Exporter module error: {e}")
        return False

if __name__ == "__main__":
    print("Running Text2Dataset module tests...\n")
    
    results = []
    results.append(test_preprocessing())
    results.append(test_fast_labeling())
    results.append(test_smart_labeling())
    results.append(test_exporter())
    
    print(f"\nTest Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("All tests passed! The application should work correctly.")
    else:
        print("Some tests failed. Please check the errors above.")