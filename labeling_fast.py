"""
Fast Mode for Text2Dataset - Simplified version without KeyBERT
"""

import spacy
from typing import List, Dict, Tuple
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

def label_entities_fast(sentences: List[str]) -> List[Dict]:
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
                    # Skip empty or whitespace-only entities
                    if not ent.text.strip():
                        continue
                        
                    # Fix MONEY labels and clean UTF-8 symbols
                    label = ent.label_
                    entity_text = ent.text.strip()
                    
                    # Handle MONEY entities specifically
                    if label == "MONEY":
                        # Remove extra whitespace and normalize currency symbols
                        entity_text = re.sub(r'\s+', ' ', entity_text)
                        entity_text = entity_text.replace('\u00a3', '£').replace('\u20ac', '€').replace('\u00a5', '¥')
                    
                    # Clean UTF-8 symbols and normalize text
                    entity_text = clean_text(entity_text)
                    
                    # Skip ambiguous or meaningless entity spans
                    if is_meaningful_entity(entity_text, label):
                        entities.append({
                            "text": sentence,
                            "entity": entity_text,
                            "label": label
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

def clean_text(text: str) -> str:
    """
    Clean text by normalizing UTF-8 symbols and removing extra whitespace
    
    Args:
        text (str): Text to clean
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    # Normalize common UTF-8 symbols
    text = text.replace('\u201c', '"').replace('\u201d', '"')  # Smart quotes
    text = text.replace('\u2018', "'").replace('\u2019', "'")  # Smart apostrophes
    text = text.replace('\u2013', '-').replace('\u2014', '-')  # En dash and em dash
    text = text.replace('\u00a0', ' ')  # Non-breaking space
    text = text.replace('\u00a3', '£').replace('\u20ac', '€').replace('\u00a5', '¥')  # Currency symbols
    text = text.replace('\u2026', '...')  # Horizontal ellipsis
    text = text.replace('\u201e', '"').replace('\u201c', '"')  # Double low-9 quotation mark
    text = text.replace('\u201a', "'").replace('\u2018', "'")  # Single low-9 quotation mark
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def is_meaningful_entity(entity_text: str, label: str) -> bool:
    """
    Check if an entity is meaningful and not ambiguous
    
    Args:
        entity_text (str): The entity text
        label (str): The entity label
        
    Returns:
        bool: True if entity is meaningful
    """
    # Remove empty or whitespace-only entities
    if not entity_text or not entity_text.strip():
        return False
    
    # Remove single character entities (except for specific cases)
    if len(entity_text.strip()) <= 1:
        # Allow currency symbols for MONEY entities
        if label == "MONEY" and entity_text.strip() in ['$', '£', '€', '¥']:
            return True
        return False
    
    # Remove entities that are just numbers or symbols
    if re.match(r'^[0-9\W]+$', entity_text.strip()):
        # Allow MONEY entities that contain currency symbols
        if label == "MONEY" and re.search(r'[£$€¥]', entity_text):
            return True
        return False
    
    # Remove entities that are common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can'}
    if entity_text.lower() in stop_words:
        return False
    
    # Remove entities with excessive punctuation
    if len(re.findall(r'[^\w\s]', entity_text)) > len(entity_text) / 2:
        return False
    
    # For MONEY entities, ensure they contain currency information
    if label == "MONEY":
        # Must contain at least one currency symbol or currency word
        currency_symbols = ['$','£','€','¥']
        currency_words = ['dollar', 'pound', 'euro', 'yen', 'usd', 'gbp', 'eur', 'jpy']
        has_symbol = any(symbol in entity_text for symbol in currency_symbols)
        has_word = any(word in entity_text.lower() for word in currency_words)
        if not (has_symbol or has_word):
            return False
    
    return True

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
            clean_match = clean_text(match)
            if is_meaningful_entity(clean_match, "DATE"):
                entities.append({
                    "text": sentence,
                    "entity": clean_match,
                    "label": "DATE"
                })
    
    # Pattern for emails
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, sentence)
    for email in emails:
        clean_email = clean_text(email)
        if is_meaningful_entity(clean_email, "EMAIL"):
            entities.append({
                "text": sentence,
                "entity": clean_email,
                "label": "EMAIL"
            })
    
    # Pattern for phone numbers
    phone_pattern = r'(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}'
    phones = re.findall(phone_pattern, sentence)
    for phone in phones:
        clean_phone = clean_text(phone)
        if is_meaningful_entity(clean_phone, "PHONE"):
            entities.append({
                "text": sentence,
                "entity": clean_phone,
                "label": "PHONE"
            })
    
    # Pattern for money/currency
    money_patterns = [
        r'\$[0-9,]+(?:\.[0-9]{2})?',
        r'£[0-9,]+(?:\.[0-9]{2})?',
        r'€[0-9,]+(?:\.[0-9]{2})?',
        r'¥[0-9,]+(?:\.[0-9]{2})?',
        r'[0-9,]+(?:\.[0-9]{2})?\s*(?:dollars|USD|pounds|GBP|euros|EUR|yen|JPY)'
    ]
    
    for pattern in money_patterns:
        matches = re.findall(pattern, sentence, re.IGNORECASE)
        for match in matches:
            clean_match = clean_text(match)
            if is_meaningful_entity(clean_match, "MONEY"):
                entities.append({
                    "text": sentence,
                    "entity": clean_match,
                    "label": "MONEY"
                })
    
    return entities

def convert_to_spacy_format(sentences: List[str]) -> List[Tuple[str, Dict]]:
    """
    Convert labeled data to spaCy training format: (text, {"entities": [(start, end, label), ...]})
    
    Args:
        sentences (List[str]): List of sentences to process
        
    Returns:
        List[Tuple[str, Dict]]: List of tuples in spaCy format
    """
    # Get labeled entities
    labeled_data = label_entities_fast(sentences)
    
    # Group by text
    text_entities = {}
    for item in labeled_data:
        text = item["text"]
        entity = item["entity"]
        label = item["label"]
        
        if text not in text_entities:
            text_entities[text] = []
        
        # Find the start and end positions of the entity in the text
        start = text.find(entity)
        if start != -1:  # Only add if entity is found
            end = start + len(entity)
            text_entities[text].append((start, end, label))
    
    # Convert to spaCy format
    spacy_format = []
    for text, entities in text_entities.items():
        spacy_format.append((text, {"entities": entities}))
    
    return spacy_format