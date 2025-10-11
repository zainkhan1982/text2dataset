"""
Test script to verify Â encoding fixes
"""

from labeling_fast import clean_text

def test_encoding_fixes():
    print("Testing Â Encoding Fixes")
    print("=" * 30)
    
    # Test cases with Â encoding issues
    test_cases = [
        ("Â£60,000", "£60,000"),
        ("Â£2,000", "£2,000"),
        ("Â£5.60 an hour", "£5.60 an hour"),
        ("The price is Â£100", "The price is £100"),
        ("Costs Â€50", "Costs €50"),
        ("Amount Â¥1000", "Amount ¥1000"),
        ("Â¢1.50 per item", "¢1.50 per item"),
        ("Â° Celsius", "° Celsius"),
        ("Â±5% tolerance", "±5% tolerance"),
        ("File Â§2.1", "File §2.1"),
    ]
    
    all_passed = True
    for original, expected in test_cases:
        result = clean_text(original)
        status = "✓" if result == expected else "✗"
        if result != expected:
            all_passed = False
        print(f"{status} {original!r} -> {result!r}")
    
    print()
    if all_passed:
        print("All tests PASSED! Â encoding issues have been fixed.")
    else:
        print("Some tests FAILED. Please check the implementation.")

if __name__ == "__main__":
    test_encoding_fixes()