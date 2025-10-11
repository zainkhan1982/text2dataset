"""
Simple verification script for the fixes
"""

# Test the key functions directly
import labeling_fast
import labeling_smart

print("Testing UTF-8 encoding fix:")
test_input = "Â£60,000"
result = labeling_fast.clean_text(test_input)
print(f"  Input: {test_input!r}")
print(f"  Output: {result!r}")
print(f"  Expected: '£60,000'")
print(f"  Status: {'PASS' if result == '£60,000' else 'FAIL'}")
print()

print("Testing ambiguous entity filtering:")
test_entity = "the end of"
result = labeling_fast.is_meaningful_entity(test_entity, "DATE")
print(f"  Entity: {test_entity!r}")
print(f"  Label: DATE")
print(f"  Result: {result}")
print(f"  Expected: False (should be filtered)")
print(f"  Status: {'PASS' if not result else 'FAIL'}")
print()

print("Testing MONEY entity detection:")
test_sentence = "The rate is £5.60 an hour."
print(f"  Sentence: {test_sentence}")
results = labeling_fast.label_entities_fast([test_sentence])
money_entities = [r for r in results if r['label'] == 'MONEY']
print(f"  MONEY entities found: {len(money_entities)}")
for entity in money_entities:
    print(f"    - {entity['entity']!r}")
print(f"  Expected: 1 MONEY entity")
print(f"  Status: {'PASS' if len(money_entities) == 1 else 'FAIL'}")