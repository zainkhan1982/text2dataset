"""
Test both Fast Mode and Smart Mode
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_fast_mode():
    print("=== Testing Fast Mode ===")
    try:
        from labeling_fast import label_entities_fast
        sentences = [
            "Apple Inc. was founded by Steve Jobs in Cupertino, California.",
            "The World Health Organization announced new health guidelines today."
        ]
        results = label_entities_fast(sentences)
        print(f"✓ Fast Mode working. Generated {len(results)} entities")
        for result in results[:3]:  # Show first 3 results
            print(f"  - {result}")
        return True
    except Exception as e:
        print(f"✗ Fast Mode error: {e}")
        return False

def test_smart_mode():
    print("\n=== Testing Smart Mode ===")
    try:
        from labeling_smart import label_entities_smart
        sentences = [
            "Apple Inc. was founded by Steve Jobs in Cupertino, California.",
            "The World Health Organization announced new health guidelines today."
        ]
        results = label_entities_smart(sentences)
        print(f"✓ Smart Mode working. Generated {len(results)} entities")
        for result in results[-3:]:  # Show last 3 results (category classifications)
            print(f"  - {result}")
        return True
    except Exception as e:
        print(f"✗ Smart Mode error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Text2Dataset modes...\n")
    
    fast_result = test_fast_mode()
    smart_result = test_smart_mode()
    
    print(f"\n=== Summary ===")
    print(f"Fast Mode: {'✓ Working' if fast_result else '✗ Failed'}")
    print(f"Smart Mode: {'✓ Working' if smart_result else '✗ Failed'}")
    
    if fast_result and smart_result:
        print("\n🎉 Both modes are working correctly!")
    else:
        print("\n⚠️  Some modes need attention!")