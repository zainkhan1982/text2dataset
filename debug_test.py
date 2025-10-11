"""
Debug test for MONEY entity detection
"""

from labeling_fast import clean_text, is_meaningful_entity, extract_entities_fallback

# Test the full fallback extraction
sentence = 'The rate is £5.60 an hour.'
print("Testing sentence:", sentence)

# Clean the sentence
cleaned = clean_text(sentence)
print("Cleaned:", repr(cleaned))

# Test fallback extraction
results = extract_entities_fallback(sentence)
print("Fallback extraction results:")
for result in results:
    print(f"  {result['entity']!r} -> {result['label']}")

# Test individual components
import re
pattern = r'[£$€¥][0-9,]+(?:\.[0-9]{2})?\s*(?:an\s+hour|per\s+hour|hour)'
matches = re.findall(pattern, cleaned, re.IGNORECASE)
print("Regex matches:", matches)

for match in matches:
    meaningful = is_meaningful_entity(match, 'MONEY')
    print(f"Match: {match!r}, Meaningful: {meaningful}")