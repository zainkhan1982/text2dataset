"""
Enhanced Smart Mode using our trained model instead of heavy transformers
"""

from typing import List, Dict
import spacy
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try to import our integration module
try:
    from integrate_model import classify_text, MODEL_LOADED
    INTEGRATION_AVAILABLE = True
    print("✓ Integration module loaded successfully")
except ImportError:
    INTEGRATION_AVAILABLE = False
    MODEL_LOADED = False
    print("⚠️  Integration module not available")

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

def label_entities_smart_enhanced(sentences: List[str]) -> List[Dict]:
    """
    Label entities in sentences using our trained model + spaCy NER
    
    Args:
        sentences (List[str]): List of sentences to process
        
    Returns:
        List[Dict]: List of dictionaries containing text, entity, and label
    """
    results = []
    
    logger.info(f"Processing {len(sentences)} sentences with Enhanced Smart Mode")
    
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
        
        # Then classify the sentence using our trained model
        try:
            if INTEGRATION_AVAILABLE and MODEL_LOADED:
                logger.info(f"Classifying sentence with our model: {sentence[:50]}...")
                classification_result = classify_text(sentence)
                
                # Add classification result
                entities.append({
                    "text": sentence,
                    "entity": sentence,
                    "label": classification_result["label"],
                    "confidence": classification_result["confidence"]
                })
                logger.info(f"Classification result: {classification_result['label']} (confidence: {classification_result['confidence']:.2f})")
            else:
                # Fallback: Add a general category
                logger.warning("Using fallback category as our model is not available")
                entities.append({
                    "text": sentence,
                    "entity": sentence,
                    "label": "CATEGORY_GENERAL"
                })
        except Exception as e:
            logger.error(f"Error in text classification: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Fallback: Add a general category
            entities.append({
                "text": sentence,
                "entity": sentence,
                "label": "CATEGORY_GENERAL"
            })
        
        results.extend(entities)
    
    logger.info(f"Enhanced Smart Mode processing complete. Generated {len(results)} entities.")
    return results

# Simple test
if __name__ == "__main__":
    test_sentences = [
        "Apple Inc. was founded by Steve Jobs in Cupertino, California.",
        "The World Health Organization announced new health guidelines today."
    ]
    
    print("Testing Enhanced Smart Mode...")
    results = label_entities_smart_enhanced(test_sentences)
    print(f"Results: {results}")
    print("Enhanced Smart Mode test complete!")