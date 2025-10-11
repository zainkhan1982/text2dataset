"""
Simplified Fast Mode without KeyBERT to avoid transformer dependencies
"""

import spacy
from typing import List, Dict
import re

# Load spaCy model (you'll need to download it separately)
try:
    nlp = spacy.load("en_core_web_sm")
    SPACY_AVAILABLE = True
except OSError:
    # If model is not installed, we'll use a fallback approach
    nlp = None
    SPACY_AVAILABLE = False
    print("spaCy model 'en_core_web_sm' not found. Please install it with: python -m spacy download en_core_web_sm")

def label_entities_fast_simplified(sentences: List[str]) -> List[Dict]:
    """
    Label entities in sentences using rule-based NLP (spaCy only)
    
    Args:
        sentences (List[str]): List of sentences to process
        
    Returns:
        List[Dict]: List of dictionaries containing text, entity, and label
    """
    results = []
    
    for sentence in sentences:
        if not sentence.strip():
            continue
            
        # Use spaCy for named entity recognition
        entities = []
        if SPACY_AVAILABLE and nlp:
            try:
                doc = nlp(sentence)
                for ent in doc.ents:
                    entities.append({
                        "text": sentence,
                        "entity": ent.text,
                        "label": ent.label_
                    })
            except Exception as e:
                print(f"Error in spaCy NER: {e}")
                # Fallback to regex-based extraction
                entities = extract_entities_fallback(sentence)
        else:
            # Fallback: Simple regex-based entity extraction
            entities = extract_entities_fallback(sentence)
            
        results.extend(entities)
    
    return results

def extract_entities_fallback(sentence: str) -> List[Dict]:
    """
    Fallback method for entity extraction using regex patterns
    
    Args:
        sentence (str): Sentence to process
        
    Returns:
        List[Dict]: List of extracted entities
    """
    entities = []
    
    # Pattern for dates
    date_patterns = [
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
        r'\b\d{4}\b',
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b'
    ]
    
    for pattern in date_patterns:
        matches = re.findall(pattern, sentence, re.IGNORECASE)
        for match in matches:
            entities.append({
                "text": sentence,
                "entity": match,
                "label": "DATE"
            })
    
    # Pattern for emails
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, sentence)
    for email in emails:
        entities.append({
            "text": sentence,
            "entity": email,
            "label": "EMAIL"
        })
    
    # Pattern for phone numbers
    phone_pattern = r'(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}'
    phones = re.findall(phone_pattern, sentence)
    for phone in phones:
        entities.append({
            "text": sentence,
            "entity": phone,
            "label": "PHONE"
        })
    
    return entities

# Test the simplified fast mode
if __name__ == "__main__":
    test_sentences = [
        "Apple Inc. was founded by Steve Jobs in Cupertino, California.",
        "The World Health Organization announced new health guidelines today."
    ]
    
    print("Testing Simplified Fast Mode...")
    results = label_entities_fast_simplified(test_sentences)
    print(f"Results: {results}")
    print("Simplified Fast Mode test complete!")