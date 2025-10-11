"""
Lightweight Smart Mode - Optimized version that doesn't load heavy transformers
"""

from typing import List, Dict
import spacy
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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
    if any(word in text_lower for word in ['tech', 'computer', 'software', 'digital', 'internet', 'app']):
        return "CATEGORY_TECHNOLOGY"
    elif any(word in text_lower for word in ['sport', 'game', 'football', 'basketball', 'tennis', 'olympic']):
        return "CATEGORY_SPORTS"
    elif any(word in text_lower for word in ['politic', 'government', 'election', 'president', 'minister']):
        return "CATEGORY_POLITICS"
    elif any(word in text_lower for word in ['business', 'market', 'economy', 'stock', 'finance', 'company']):
        return "CATEGORY_BUSINESS"
    elif any(word in text_lower for word in ['health', 'medical', 'doctor', 'hospital', 'disease']):
        return "CATEGORY_HEALTH"
    else:
        return "CATEGORY_GENERAL"

def label_entities_smart_lightweight(sentences: List[str]) -> List[Dict]:
    """
    Label entities in sentences using spaCy NER + lightweight classification
    
    Args:
        sentences (List[str]): List of sentences to process
        
    Returns:
        List[Dict]: List of dictionaries containing text, entity, and label
    """
    results = []
    
    logger.info(f"Processing {len(sentences)} sentences with Lightweight Smart Mode")
    
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
                    entities.append({
                        "text": sentence,
                        "entity": ent.text,
                        "label": ent.label_
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
    
    logger.info(f"Lightweight Smart Mode processing complete. Generated {len(results)} entities.")
    return results

# Simple test
if __name__ == "__main__":
    test_sentences = [
        "Apple Inc. was founded by Steve Jobs in Cupertino, California.",
        "The World Health Organization announced new health guidelines today.",
        "The stock market reached new heights today with technology companies leading the surge."
    ]
    
    print("Testing Lightweight Smart Mode...")
    results = label_entities_smart_lightweight(test_sentences)
    print(f"Results: {results}")
    print("Lightweight Smart Mode test complete!")