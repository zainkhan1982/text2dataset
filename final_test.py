"""
Final comprehensive test to demonstrate all entity quality improvements
"""

from labeling_fast import label_entities_fast, convert_to_spacy_format as convert_fast_to_spacy
from labeling_smart import label_entities_smart, convert_to_spacy_format as convert_smart_to_spacy

def test_comprehensive_improvements():
    print("Comprehensive Test of Entity Quality Improvements")
    print("=" * 60)
    
    # Test text with various challenging cases
    test_text = """
    The company reported revenues of $1.2 million in 2023.
    John paid £500 for his new "smartphone" — a great deal!
    The exchange rate is €1 = $1.10, and ¥100 = $0.85.
    Contact us at info@example.com or call (555) 123-4567.
    The meeting is scheduled for Jan 15, 2024.
    This is a meaningless entity: "and" or "the".
    Prices start at just $99.99 — limited time offer!
    Our European subsidiary earned €50,000 last quarter.
    The "special" characters: "smart" quotes and – dashes – are normalized.
    """
    
    # Split text into sentences for testing
    sentences = [s.strip() for s in test_text.split('\n') if s.strip()]
    
    print("Test sentences:")
    for i, sentence in enumerate(sentences, 1):
        print(f"{i}. {sentence}")
    
    print("\n" + "=" * 60)
    
    # Test Fast Mode
    print("Fast Mode Results:")
    fast_results = label_entities_fast(sentences)
    money_count = 0
    person_count = 0
    date_count = 0
    other_count = 0
    
    for result in fast_results:
        print(f"Text: {result['text']}")
        print(f"Entity: {result['entity']}")
        print(f"Label: {result['label']}")
        print("-" * 30)
        
        # Count entity types
        if result['label'] == 'MONEY':
            money_count += 1
        elif result['label'] == 'PERSON':
            person_count += 1
        elif result['label'] == 'DATE':
            date_count += 1
        else:
            other_count += 1
    
    print(f"Fast Mode Entity Summary:")
    print(f"  MONEY: {money_count}")
    print(f"  PERSON: {person_count}")
    print(f"  DATE: {date_count}")
    print(f"  OTHER: {other_count}")
    print(f"  TOTAL: {len(fast_results)}")
    
    print("\n" + "=" * 60)
    
    # Test Smart Mode
    print("Smart Mode Results:")
    smart_results = label_entities_smart(sentences)
    money_count = 0
    person_count = 0
    date_count = 0
    category_count = 0
    other_count = 0
    
    for result in smart_results:
        print(f"Text: {result['text']}")
        print(f"Entity: {result['entity']}")
        print(f"Label: {result['label']}")
        print("-" * 30)
        
        # Count entity types
        if result['label'] == 'MONEY':
            money_count += 1
        elif result['label'] == 'PERSON':
            person_count += 1
        elif result['label'] == 'DATE':
            date_count += 1
        elif result['label'].startswith('CATEGORY_'):
            category_count += 1
        else:
            other_count += 1
    
    print(f"Smart Mode Entity Summary:")
    print(f"  MONEY: {money_count}")
    print(f"  PERSON: {person_count}")
    print(f"  DATE: {date_count}")
    print(f"  CATEGORY: {category_count}")
    print(f"  OTHER: {other_count}")
    print(f"  TOTAL: {len(smart_results)}")
    
    print("\n" + "=" * 60)
    
    # Test spaCy format conversion
    print("spaCy Format Conversion (Fast Mode):")
    spacy_format = convert_fast_to_spacy(sentences)
    for text, entities_dict in spacy_format[:3]:  # Show first 3 for brevity
        print(f"Text: {text}")
        print(f"Entities: {entities_dict}")
        print("-" * 30)
    
    print("\n" + "=" * 60)
    
    # Demonstrate UTF-8 symbol normalization
    print("UTF-8 Symbol Normalization Examples:")
    from labeling_fast import clean_text
    
    utf8_examples = [
        '"smart quotes"',
        "en dash – and em dash —",
        "non-breaking space\u00a0here",
        "currency symbols: £10, €20, ¥30",
        "horizontal ellipsis…",
    ]
    
    for example in utf8_examples:
        normalized = clean_text(example)
        print(f"Original: {example!r}")
        print(f"Normalized: {normalized!r}")
        print("-" * 30)
    
    print("\n" + "=" * 60)
    
    # Demonstrate ambiguous entity filtering
    print("Ambiguous Entity Filtering Examples:")
    from labeling_fast import is_meaningful_entity
    
    ambiguous_examples = [
        ("the", "ORG"),
        ("and", "PERSON"),
        ("$", "MONEY"),
        ("abc", "MONEY"),
        ("John", "PERSON"),
        ("$100", "MONEY"),
    ]
    
    for entity_text, label in ambiguous_examples:
        is_meaningful = is_meaningful_entity(entity_text, label)
        status = "MEANINGFUL" if is_meaningful else "FILTERED OUT"
        print(f"Entity: {entity_text!r} ({label}) -> {status}")

if __name__ == "__main__":
    test_comprehensive_improvements()