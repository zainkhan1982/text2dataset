"""
Integration of the trained model with Text2Dataset
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import joblib
import re
import pandas as pd
from typing import List, Dict

# Try to load the trained model
try:
    model = joblib.load('../best_text_classifier.pkl')
    MODEL_LOADED = True
    print("✓ Trained model loaded successfully")
except FileNotFoundError:
    MODEL_LOADED = False
    print("⚠️  Trained model not found. Run simple_train_model.py first.")

def simple_preprocess(text):
    """Simple text preprocessing function"""
    # Convert to lowercase
    text = str(text).lower()
    
    # Remove extra whitespaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def classify_text(text: str) -> Dict:
    """
    Classify a single text using the trained model
    
    Args:
        text (str): Text to classify
        
    Returns:
        Dict: Classification result with label and confidence
    """
    if not MODEL_LOADED:
        return {
            "text": text,
            "entity": text,
            "label": "CATEGORY_UNAVAILABLE",
            "confidence": 0.0
        }
    
    try:
        # Preprocess the text
        processed_text = simple_preprocess(text)
        
        # Make prediction
        prediction = model.predict([processed_text])[0]
        
        # Get prediction probabilities
        probabilities = model.predict_proba([processed_text])[0]
        confidence = max(probabilities)
        
        # Map numeric labels to descriptive names (if known)
        label_names = {
            0: "POLITICS",
            1: "SPORTS",
            2: "BUSINESS",
            3: "ENTERTAINMENT",
            4: "TECHNOLOGY"
        }
        
        category_name = label_names.get(prediction, f"CATEGORY_{prediction}")
        
        return {
            "text": text,
            "entity": text,
            "label": category_name,
            "confidence": float(confidence)
        }
    except Exception as e:
        print(f"Error in text classification: {e}")
        return {
            "text": text,
            "entity": text,
            "label": "CATEGORY_ERROR",
            "confidence": 0.0
        }

def classify_texts(texts: List[str]) -> List[Dict]:
    """
    Classify multiple texts using the trained model
    
    Args:
        texts (List[str]): List of texts to classify
        
    Returns:
        List[Dict]: List of classification results
    """
    results = []
    for text in texts:
        result = classify_text(text)
        results.append(result)
    return results

# Test the integration
if __name__ == "__main__":
    # Test examples
    test_texts = [
        "The stock market reached new heights today with technology companies leading the surge.",
        "The football match ended in a draw with both teams showing excellent performance.",
        "New medical research shows promising results in cancer treatment."
    ]
    
    print("=== Text Classification Integration Test ===\n")
    
    results = classify_texts(test_texts)
    
    for i, result in enumerate(results, 1):
        print(f"{i}. Text: {result['text'][:100]}...")
        print(f"   Category: {result['label']}")
        print(f"   Confidence: {result['confidence']:.4f}")
        print()