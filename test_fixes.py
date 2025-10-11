"""
Test script to verify the fixes for MONEY labels, UTF-8 encoding, and ambiguous entities
"""

from labeling_fast import clean_text, is_meaningful_entity, label_entities_fast, extract_entities_fallback
from labeling_smart import label_entities_smart
import re

def test_utf8_encoding_fix():
    """Test the UTF-8 encoding fix for Â£ -> £"""
    print("Testing UTF-8 Encoding Fix")
    print("=" * 30)
    
    test_cases = [
        ("Â£60,000", "£60,000"),
        ("Â£2,000", "£2,000"),
        ("Â£5.60 an hour", "£5.60 an hour"),
    ]
    
    for original, expected in test_cases:
        result = clean_text(original)
        status = "✓" if result == expected else "✗"
        print(f"{status} {original!r} -> {result!r} (expected: {expected!r})")
    
    print()

def test_money_labeling():
    """Test MONEY labeling for problematic cases"""
    print("Testing MONEY Labeling")
    print("=" * 30)
    
    test_sentences = [
        "The salary is Â£60,000 per year.",
        "They paid Â£2,000 for the service.",
        "The rate is £5.60 an hour.",
        "It costs $15.50 per item.",
        "Payment is €100.00 upfront.",
    ]
    
    print("Fast Mode Results:")
    fast_results = label_entities_fast(test_sentences)
    money_count = 0
    for result in fast_results:
        if result['label'] == 'MONEY':
            money_count += 1
            print(f"  ✓ {result['entity']!r} -> {result['label']}")
    
    print(f"  Total MONEY entities found: {money_count}")
    print()

def test_time_mislabeling():
    """Test that time-like MONEY entities are correctly labeled as MONEY, not TIME"""
    print("Testing Time Mislabeling Fix")
    print("=" * 30)
    
    test_sentences = [
        "The rate is £5.60 an hour.",
        "She earns $25.00 per hour.",
        "The cost is €10.50 per hour.",
    ]
    
    print("Checking that time-like MONEY entities are labeled correctly:")
    fast_results = label_entities_fast(test_sentences)
    for result in fast_results:
        if 'hour' in result['entity'].lower():
            status = "✓" if result['label'] == 'MONEY' else "✗"
            print(f"  {status} {result['entity']!r} -> {result['label']}")
    
    print()

def test_ambiguous_entity_filtering():
    """Test filtering of ambiguous entities like 'the end of'"""
    print("Testing Ambiguous Entity Filtering")
    print("=" * 30)
    
    # Test the specific case mentioned
    ambiguous_entity = "the end of"
    is_meaningful = is_meaningful_entity(ambiguous_entity, "DATE")
    status = "✗" if is_meaningful else "✓"  # Should be filtered out
    print(f"  {status} {ambiguous_entity!r} -> {'MEANINGFUL' if is_meaningful else 'FILTERED'}")
    
    # Test other ambiguous entities
    test_cases = [
        ("the end of", "DATE", False),
        ("end of", "DATE", False),
        ("the beginning", "DATE", False),
        ("a period", "DATE", False),
    ]
    
    for entity, label, expected in test_cases:
        result = is_meaningful_entity(entity, label)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {entity!r} ({label}) -> {'MEANINGFUL' if result else 'FILTERED'}")
    
    print()

def test_regex_patterns():
    """Test that our regex patterns catch the problematic MONEY formats"""
    print("Testing Regex Patterns")
    print("=" * 30)
    
    # Enhanced money patterns that should catch hourly rates
    money_patterns = [
        r'\$[0-9,]+(?:\.[0-9]{2})?',
        r'£[0-9,]+(?:\.[0-9]{2})?',
        r'€[0-9,]+(?:\.[0-9]{2})?',
        r'¥[0-9,]+(?:\.[0-9]{2})?',
        r'[0-9,]+(?:\.[0-9]{2})?\s*(?:dollars|USD|pounds|GBP|euros|EUR|yen|JPY)',
        r'[£$€¥][0-9,]+(?:\.[0-9]{2})?\s*(?:an\s+hour|per\s+hour|hour)'  # Special pattern for hourly rates
    ]
    
    test_sentence = "The rate is £5.60 an hour and the fixed fee is £60,000."
    
    print(f"Test sentence: {test_sentence}")
    for pattern in money_patterns:
        matches = re.findall(pattern, test_sentence, re.IGNORECASE)
        if matches:
            print(f"  Pattern {pattern} matched: {matches}")
    
    print()

def test_full_integration():
    """Test the full integration with the problematic examples"""
    print("Testing Full Integration")
    print("=" * 30)
    
    # The exact problematic text from the issue
    problematic_text = "Â£60,000, Â£2,000, Â£5.60 an hour"
    
    print(f"Original problematic text: {problematic_text}")
    
    # Test with Fast Mode
    fast_results = label_entities_fast([problematic_text])
    print("\nFast Mode Results:")
    money_entities = [r for r in fast_results if r['label'] == 'MONEY']
    for entity in money_entities:
        print(f"  ✓ {entity['entity']!r} -> {entity['label']}")
    
    # Test with Smart Mode
    smart_results = label_entities_smart([problematic_text])
    print("\nSmart Mode Results:")
    money_entities = [r for r in smart_results if r['label'] == 'MONEY']
    for entity in money_entities:
        print(f"  ✓ {entity['entity']!r} -> {entity['label']}")
    
    print(f"\nExpected: 3 MONEY entities")
    print(f"Fast Mode found: {len([r for r in fast_results if r['label'] == 'MONEY'])} MONEY entities")
    print(f"Smart Mode found: {len([r for r in smart_results if r['label'] == 'MONEY'])} MONEY entities")

if __name__ == "__main__":
    test_utf8_encoding_fix()
    test_money_labeling()
    test_time_mislabeling()
    test_ambiguous_entity_filtering()
    test_regex_patterns()
    test_full_integration()