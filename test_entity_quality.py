"""
Test script to verify entity quality improvements
"""

from labeling_fast import label_entities_fast, convert_to_spacy_format
from labeling_smart import label_entities_smart

# Test text with various entities including MONEY labels and UTF-8 symbols
test_text = """
The company reported revenues of $1.2 million in 2023. 
John paid £500 for his new "smartphone" — a great deal!
The exchange rate is €1 = $1.10, and ¥100 = $0.85.
Contact us at info@example.com or call (555) 123-4567.
The meeting is scheduled for Jan 15, 2024.
This is a meaningless entity: "and" or "the".
"""

def test_entity_quality():
    print("Testing Entity Quality Improvements")
    print("=" * 50)
    
    # Split text into sentences for testing
    sentences = [s.strip() for s in test_text.split('\n') if s.strip()]
    
    print("Test sentences:")
    for i, sentence in enumerate(sentences, 1):
        print(f"{i}. {sentence}")
    
    print("\n" + "=" * 50)
    
    # Test Fast Mode
    print("Fast Mode Results:")
    fast_results = label_entities_fast(sentences)
    for result in fast_results:
        print(f"Text: {result['text']}")
        print(f"Entity: {result['entity']}")
        print(f"Label: {result['label']}")
        print("-" * 30)
    
    print("\n" + "=" * 50)
    
    # Test Smart Mode
    print("Smart Mode Results:")
    smart_results = label_entities_smart(sentences)
    for result in smart_results:
        print(f"Text: {result['text']}")
        print(f"Entity: {result['entity']}")
        print(f"Label: {result['label']}")
        print("-" * 30)
    
    print("\n" + "=" * 50)
    
    # Test spaCy format conversion
    print("spaCy Format Conversion (Fast Mode):")
    spacy_format = convert_to_spacy_format(sentences)
    for text, entities_dict in spacy_format:
        print(f"Text: {text}")
        print(f"Entities: {entities_dict}")
        print("-" * 30)

if __name__ == "__main__":
    test_entity_quality()