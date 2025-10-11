"""
Simple test to verify all fixes
"""

from labeling_fast import clean_text, is_meaningful_entity, label_entities_fast

# Test UTF-8 encoding fix
print("UTF-8 Encoding Fix:")
print(f"Â£60,000 -> {clean_text('Â£60,000')}")
print(f"Â£2,000 -> {clean_text('Â£2,000')}")
print(f"Â£5.60 an hour -> {clean_text('Â£5.60 an hour')}")
print()

# Test ambiguous entity filtering
print("Ambiguous Entity Filtering:")
print(f"'the end of' -> {'MEANINGFUL' if is_meaningful_entity('the end of', 'DATE') else 'FILTERED'}")
print()

# Test MONEY labeling
print("MONEY Labeling:")
test_sentences = [
    "The salary is Â£60,000 per year.",
    "They paid Â£2,000 for the service.",
    "The rate is £5.60 an hour."
]

results = label_entities_fast(test_sentences)
for result in results:
    if result['label'] == 'MONEY':
        print(f"  {result['entity']} -> {result['label']}")