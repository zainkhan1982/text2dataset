"""
Test script to specifically verify MONEY labels and UTF-8 symbol handling
"""

from labeling_fast import clean_text, is_meaningful_entity

def test_utf8_symbols():
    print("Testing UTF-8 Symbol Normalization")
    print("=" * 40)
    
    # Test cases with UTF-8 symbols
    test_cases = [
        ('"smart quotes"', '"smart quotes"'),
        ("'smart apostrophes'", "'smart apostrophes'"),
        ("en dash – and em dash —", "en dash - and em dash -"),
        ("non-breaking space\u00a0here", "non-breaking space here"),
        ("currency symbols: £10, €20, ¥30", "currency symbols: £10, €20, ¥30"),
        ("horizontal ellipsis…", "horizontal ellipsis..."),
        ("German quotes „text“", '"text"'),
    ]
    
    for original, expected in test_cases:
        result = clean_text(original)
        status = "✓" if result == expected else "✗"
        print(f"{status} {original!r} -> {result!r}")
    
    print()

def test_money_labels():
    print("Testing MONEY Entity Handling")
    print("=" * 40)
    
    # Test cases for MONEY entities
    test_cases = [
        ("$100", "MONEY", True),
        ("£50.99", "MONEY", True),
        ("€200", "MONEY", True),
        ("¥1000", "MONEY", True),
        ("100 dollars", "MONEY", True),
        ("50 USD", "MONEY", True),
        ("$", "MONEY", True),  # Single currency symbol
        ("£", "MONEY", True),  # Single currency symbol
        ("€", "MONEY", True),  # Single currency symbol
        ("¥", "MONEY", True),  # Single currency symbol
        ("123", "MONEY", False),  # Just numbers
        ("abc", "MONEY", False),  # Just letters
        ("the", "MONEY", False),  # Stop word
        ("and", "MONEY", False),  # Stop word
        ("", "MONEY", False),     # Empty string
        (" ", "MONEY", False),    # Whitespace
        ("!", "MONEY", False),    # Just punctuation
    ]
    
    for entity_text, label, expected in test_cases:
        result = is_meaningful_entity(entity_text, label)
        status = "✓" if result == expected else "✗"
        print(f"{status} {entity_text!r} ({label}) -> {result} (expected: {expected})")
    
    print()

def test_ambiguous_entities():
    print("Testing Ambiguous Entity Filtering")
    print("=" * 40)
    
    # Test cases for ambiguous/meaningless entities
    test_cases = [
        ("the", "ORG", False),
        ("and", "PERSON", False),
        ("or", "GPE", False),
        ("but", "MONEY", False),
        ("in", "DATE", False),
        ("on", "CARDINAL", False),
        ("at", "EVENT", False),
        ("to", "LANGUAGE", False),
        ("for", "LAW", False),
        ("of", "PRODUCT", False),
        ("with", "WORK_OF_ART", False),
        ("by", "FAC", False),
        ("is", "NORP", False),
        ("are", "LOC", False),
        ("was", "PERCENT", False),
        ("were", "TIME", False),
        ("be", "ORDINAL", False),
        ("been", "QUANTITY", False),
        ("being", "MONEY", False),
        ("have", "PERSON", False),
        ("has", "ORG", False),
        ("had", "GPE", False),
        ("do", "DATE", False),
        ("does", "CARDINAL", False),
        ("did", "EVENT", False),
        ("will", "LANGUAGE", False),
        ("would", "LAW", False),
        ("could", "PRODUCT", False),
        ("should", "WORK_OF_ART", False),
        ("may", "FAC", False),
        ("might", "NORP", False),
        ("must", "LOC", False),
        ("can", "PERCENT", False),
        ("a", "ORG", False),
        ("an", "PERSON", False),
        ("John", "PERSON", True),  # Valid entity
        ("Apple Inc.", "ORG", True),  # Valid entity
        ("$100", "MONEY", True),  # Valid entity
        ("New York", "GPE", True),  # Valid entity
    ]
    
    for entity_text, label, expected in test_cases:
        result = is_meaningful_entity(entity_text, label)
        status = "✓" if result == expected else "✗"
        print(f"{status} {entity_text!r} ({label}) -> {result} (expected: {expected})")

if __name__ == "__main__":
    test_utf8_symbols()
    test_money_labels()
    test_ambiguous_entities()