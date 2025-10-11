"""
Smart Mode for Text2Dataset - Lightweight version
"""

from typing import List, Dict, Tuple
import spacy
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to load spaCy model for additional entity recognition
try:
    nlp = spacy.load("en_core_web_sm")
    logger.info("spaCy model loaded successfully")
except OSError:
    nlp = None
    logger.warning("spaCy model not found. Install with: python -m spacy download en_core_web_sm")

# Simple category classification without heavy models
def classify_category(text: str) -> str:
    """
    Simple rule-based category classification
    
    Args:
        text (str): Text to classify
        
    Returns:
        str: Category label
    """
    text_lower = text.lower()
    
    # Simple keyword-based classification
    if any(word in text_lower for word in ['tech', 'computer', 'software', 'digital', 'internet', 'app', 'ai', 'artificial']):
        return "CATEGORY_TECHNOLOGY"
    elif any(word in text_lower for word in ['sport', 'game', 'football', 'basketball', 'tennis', 'olympic', 'championship']):
        return "CATEGORY_SPORTS"
    elif any(word in text_lower for word in ['politic', 'government', 'election', 'president', 'minister', 'senator', 'congress']):
        return "CATEGORY_POLITICS"
    elif any(word in text_lower for word in ['business', 'market', 'economy', 'stock', 'finance', 'company', 'corporation']):
        return "CATEGORY_BUSINESS"
    elif any(word in text_lower for word in ['health', 'medical', 'doctor', 'hospital', 'disease', 'treatment']):
        return "CATEGORY_HEALTH"
    elif any(word in text_lower for word in ['entertain', 'movie', 'film', 'actor', 'celebrity', 'music', 'concert']):
        return "CATEGORY_ENTERTAINMENT"
    else:
        return "CATEGORY_GENERAL"

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

def label_entities_smart(sentences: List[str]) -> List[Dict]:
    """
    Label entities in sentences using spaCy NER + lightweight classification
    
    Args:
        sentences (List[str]): List of sentences to process
        
    Returns:
        List[Dict]: List of dictionaries containing text, entity, and label
    """
    results = []
    
    logger.info(f"Processing {len(sentences)} sentences with Smart Mode")
    
    for i, sentence in enumerate(sentences):
        if not sentence.strip():
            continue
            
        logger.info(f"Processing sentence {i+1}/{len(sentences)}: {sentence[:50]}...")
            
        # First, extract named entities using spaCy (if available)
        entities = []
        if nlp:
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
                logger.error(f"Error in spaCy NER for sentence: {e}")
                # Fallback: Add the whole sentence as an entity
                entities.append({
                    "text": sentence,
                    "entity": sentence,
                    "label": "SENTENCE"
                })
        else:
            # If spaCy is not available, add the whole sentence as an entity
            entities.append({
                "text": sentence,
                "entity": sentence,
                "label": "SENTENCE"
            })
        
        # Then classify the sentence using lightweight classification
        try:
            category = classify_category(sentence)
            entities.append({
                "text": sentence,
                "entity": sentence,
                "label": category
            })
            logger.info(f"Classification result: {category}")
        except Exception as e:
            logger.error(f"Error in text classification: {e}")
            # Fallback: Add a general category
            entities.append({
                "text": sentence,
                "entity": sentence,
                "label": "CATEGORY_GENERAL"
            })
        
        results.extend(entities)
    
    logger.info(f"Smart Mode processing complete. Generated {len(results)} entities.")
    return results

def convert_to_spacy_format(sentences: List[str]) -> List[Tuple[str, Dict]]:
    """
    Convert labeled data to spaCy training format: (text, {"entities": [(start, end, label), ...]})
    
    Args:
        sentences (List[str]): List of sentences to process
        
    Returns:
        List[Tuple[str, Dict]]: List of tuples in spaCy format
    """
    # Get labeled entities
    labeled_data = label_entities_smart(sentences)
    
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