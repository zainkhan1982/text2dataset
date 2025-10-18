"""
Test script for enhanced NLP module
"""

import sys
import os

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_nlp import EnhancedNLPProcessor, MultiLanguageProcessor, process_text_enhanced, process_multilanguage_text

def test_enhanced_nlp():
    """Test the enhanced NLP processor"""
    print("Testing Enhanced NLP Processor...")
    
    # Initialize the processor
    processor = EnhancedNLPProcessor()
    
    # Test entity extraction
    text = "Apple Inc. was founded by Steve Jobs in Cupertino, California. The company is worth over $1 trillion."
    sentences = [text]
    
    print(f"Input text: {text}")
    
    # Test entity extraction
    entities = process_text_enhanced(sentences)
    print(f"Extracted entities: {entities}")
    
    # Test text classification
    categories = ["technology", "business", "health", "sports", "politics"]
    classification = processor.classify_text_category(text, categories)
    print(f"Text classification: {classification}")
    
    # Test keyphrase extraction
    keyphrases = processor.extract_keyphrases(text)
    print(f"Keyphrases: {keyphrases}")
    
    print("Enhanced NLP test completed successfully!")

def test_multilanguage():
    """Test the multi-language processor"""
    print("\nTesting Multi-Language Processor...")
    
    # Initialize the processor
    processor = MultiLanguageProcessor()
    
    # Test language detection
    english_text = "This is an English sentence."
    spanish_text = "Esta es una frase en español."
    french_text = "C'est une phrase en français."
    
    print(f"English text: {english_text}")
    print(f"Detected language: {processor.detect_language(english_text)}")
    
    print(f"Spanish text: {spanish_text}")
    print(f"Detected language: {processor.detect_language(spanish_text)}")
    
    print(f"French text: {french_text}")
    print(f"Detected language: {processor.detect_language(french_text)}")
    
    # Test multi-language processing
    result = process_multilanguage_text(spanish_text, target_language="en")
    print(f"Spanish to English translation result: {result}")
    
    print("Multi-language test completed successfully!")

def test_integration():
    """Test the integration of enhanced NLP features"""
    print("\nTesting Integration...")
    
    # Test English text with enhanced NLP
    english_text = "Microsoft was founded by Bill Gates and Paul Allen in Seattle, Washington. The company develops software and hardware products."
    result = process_multilanguage_text(english_text, target_language="en")
    print(f"English text processing result: {result}")
    
    # Test Spanish text with translation
    spanish_text = "Microsoft fue fundada por Bill Gates y Paul Allen en Seattle, Washington. La empresa desarrolla productos de software y hardware."
    result = process_multilanguage_text(spanish_text, target_language="en")
    print(f"Spanish text processing result: {result}")
    
    print("Integration test completed successfully!")

if __name__ == "__main__":
    print("Running Enhanced NLP Tests...")
    print("=" * 50)
    
    try:
        test_enhanced_nlp()
        test_multilanguage()
        test_integration()
        
        print("\n" + "=" * 50)
        print("All tests completed successfully!")
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()