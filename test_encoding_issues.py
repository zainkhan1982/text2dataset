"""
Test script to reproduce and fix encoding issues with MONEY labels
"""

from labeling_fast import clean_text, is_meaningful_entity, label_entities_fast
from labeling_smart import label_entities_smart
import re

def test_encoding_issues():
    print("Testing Encoding and MONEY Label Issues")
    print("=" * 50)
    
    # Test cases with encoding issues
    test_cases = [
        "Â£60,000",  # Should be £60,000
        "Â£2,000",   # Should be £2,000
        "Â£5.60 an hour",  # Should be £5.60 an hour
        "the end of",  # Ambiguous entity
    ]
    
    print("Testing UTF-8 normalization:")
    for case in test_cases:
        normalized = clean_text(case)
        print(f"Original: {case!r}")
        print(f"Normalized: {normalized!r}")
        print()
    
    # Test specific MONEY patterns
    print("Testing MONEY pattern matching:")
    money_patterns = [
        r'\$[0-9,]+(?:\.[0-9]{2})?',
        r'£[0-9,]+(?:\.[0-9]{2})?',
        r'€[0-9,]+(?:\.[0-9]{2})?',
        r'¥[0-9,]+(?:\.[0-9]{2})?',
        r'[0-9,]+(?:\.[0-9]{2})?\s*(?:dollars|USD|pounds|GBP|euros|EUR|yen|JPY)'
    ]
    
    test_sentence = "Â£60,000, Â£2,000, and Â£5.60 an hour"
    normalized_sentence = clean_text(test_sentence)
    
    print(f"Test sentence: {test_sentence}")
    print(f"Normalized: {normalized_sentence}")
    
    for pattern in money_patterns:
        matches = re.findall(pattern, normalized_sentence, re.IGNORECASE)
        if matches:
            print(f"Pattern {pattern} matched: {matches}")
    
    print("\nTesting full entity labeling:")
    
    # Test with full sentences
    test_sentences = [
        "The salary is Â£60,000 per year.",
        "They paid Â£2,000 for the service.",
        "The rate is Â£5.60 an hour.",
        "We met at the end of the conference."
    ]
    
    print("\nFast Mode Results:")
    fast_results = label_entities_fast(test_sentences)
    for result in fast_results:
        print(f"Text: {result['text']}")
        print(f"Entity: {result['entity']}")
        print(f"Label: {result['label']}")
        print("-" * 30)
    
    print("\nSmart Mode Results:")
    smart_results = label_entities_smart(test_sentences)
    for result in smart_results:
        if not result['label'].startswith('CATEGORY_'):  # Skip category labels for clarity
            print(f"Text: {result['text']}")
            print(f"Entity: {result['entity']}")
            print(f"Label: {result['label']}")
            print("-" * 30)

def test_problematic_sequences():
    """Test specific problematic sequences mentioned in the issue"""
    print("\nTesting Problematic Sequences")
    print("=" * 50)
    
    # The specific problematic text
    problematic_text = "Â£60,000, Â£2,000, Â£5.60 an hour"
    
    # Test our clean_text function
    cleaned = clean_text(problematic_text)
    print(f"Original: {problematic_text}")
    print(f"Cleaned:  {cleaned}")
    
    # Check for the Â character specifically
    if 'Â' in problematic_text:
        print("Found Â character - this indicates encoding issue")
        # Replace Â£ with £
        fixed = problematic_text.replace('Â£', '£')
        print(f"Fixed:    {fixed}")
    
    # Test entity extraction on the fixed text
    test_sentences = [problematic_text]
    print("\nEntity extraction on original text:")
    results = label_entities_fast(test_sentences)
    for result in results:
        print(f"Entity: {result['entity']}, Label: {result['label']}")

if __name__ == "__main__":
    test_encoding_issues()
    test_problematic_sequences()