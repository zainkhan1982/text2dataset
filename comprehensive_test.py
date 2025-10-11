"""
Comprehensive test to verify all fixes for MONEY labels, UTF-8 encoding, and ambiguous entities
"""

from labeling_fast import clean_text, is_meaningful_entity, label_entities_fast
from labeling_smart import label_entities_smart

def test_all_fixes():
    print("Comprehensive Test of All Fixes")
    print("=" * 50)
    
    # 1. Test UTF-8 encoding fix
    print("1. UTF-8 Encoding Fix:")
    test_cases = [
        ("Â£60,000", "£60,000"),
        ("Â£2,000", "£2,000"),
        ("Â£5.60 an hour", "£5.60 an hour"),
    ]
    
    for original, expected in test_cases:
        result = clean_text(original)
        status = "✓" if result == expected else "✗"
        print(f"   {status} {original!r} -> {result!r}")
    
    print()
    
    # 2. Test ambiguous entity filtering
    print("2. Ambiguous Entity Filtering:")
    ambiguous_cases = [
        "the end of",
        "the beginning of",
        "a period",
    ]
    
    for case in ambiguous_cases:
        is_meaningful = is_meaningful_entity(case, "DATE")
        status = "✓" if not is_meaningful else "✗"  # Should be filtered out
        print(f"   {status} {case!r} -> {'MEANINGFUL' if is_meaningful else 'FILTERED'}")
    
    print()
    
    # 3. Test MONEY labeling for problematic cases
    print("3. MONEY Labeling:")
    test_sentences = [
        "The salary is Â£60,000 per year.",
        "They paid Â£2,000 for the service.",
        "The rate is £5.60 an hour.",
    ]
    
    print("   Fast Mode Results:")
    fast_results = label_entities_fast(test_sentences)
    money_count = 0
    for result in fast_results:
        if result['label'] == 'MONEY':
            money_count += 1
            print(f"     ✓ {result['entity']!r} -> {result['label']}")
    
    print(f"   Fast Mode found {money_count} MONEY entities")
    
    print("   Smart Mode Results:")
    smart_results = label_entities_smart(test_sentences)
    money_count = 0
    for result in smart_results:
        if result['label'] == 'MONEY':
            money_count += 1
            print(f"     ✓ {result['entity']!r} -> {result['label']}")
    
    print(f"   Smart Mode found {money_count} MONEY entities")
    
    print()
    
    # 4. Test the exact problematic text from the issue
    print("4. Exact Problematic Text Test:")
    problematic_text = "Â£60,000, Â£2,000, Â£5.60 an hour"
    print(f"   Text: {problematic_text}")
    
    fast_results = label_entities_fast([problematic_text])
    money_entities = [r for r in fast_results if r['label'] == 'MONEY']
    print(f"   Fast Mode found {len(money_entities)} MONEY entities:")
    for entity in money_entities:
        print(f"     ✓ {entity['entity']!r} -> {entity['label']}")
    
    smart_results = label_entities_smart([problematic_text])
    money_entities = [r for r in smart_results if r['label'] == 'MONEY']
    print(f"   Smart Mode found {len(money_entities)} MONEY entities:")
    for entity in money_entities:
        print(f"     ✓ {entity['entity']!r} -> {entity['label']}")
    
    print()
    
    # 5. Verify no redundant full-text entries
    print("5. Redundant Full-Text Entry Check:")
    # Check that we don't have full sentences labeled as CATEGORY_*
    test_sentences = [
        "This is a test sentence about technology.",
        "Another sentence about business matters.",
    ]
    
    smart_results = label_entities_smart(test_sentences)
    category_entities = [r for r in smart_results if r['label'].startswith('CATEGORY_') and r['entity'] == r['text']]
    if category_entities:
        print(f"   ✗ Found {len(category_entities)} redundant full-text CATEGORY entries")
        for entity in category_entities:
            print(f"     {entity['entity'][:50]}... -> {entity['label']}")
    else:
        print("   ✓ No redundant full-text CATEGORY entries found")
    
    print()
    print("All tests completed!")

if __name__ == "__main__":
    test_all_fixes()