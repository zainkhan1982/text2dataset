"""
Test script for lazy loading of transformer models
"""

import sys
import os
import time

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_lazy_loading():
    """Test that transformer models are loaded lazily"""
    print("Testing lazy loading of transformer models...")
    
    # Import the enhanced NLP module - this should not load models yet
    start_time = time.time()
    from enhanced_nlp import EnhancedNLPProcessor
    import_time = time.time() - start_time
    
    print(f"Module import time: {import_time:.2f} seconds")
    
    # Create an instance - this should also not load models yet
    start_time = time.time()
    processor = EnhancedNLPProcessor()
    instantiation_time = time.time() - start_time
    
    print(f"Processor instantiation time: {instantiation_time:.2f} seconds")
    
    # Check that models are not loaded yet
    print(f"NER pipeline loaded: {processor.ner_pipeline is not None}")
    print(f"Classifier pipeline loaded: {processor.classifier_pipeline is not None}")
    
    # Now try to use a model - this should trigger loading
    print("\nTesting model loading...")
    start_time = time.time()
    entities = processor.extract_entities_transformer("Apple Inc. is a technology company.")
    loading_time = time.time() - start_time
    
    print(f"Model loading and inference time: {loading_time:.2f} seconds")
    print(f"Entities found: {len(entities)}")
    
    # Check that models are now loaded
    print(f"NER pipeline loaded: {processor.ner_pipeline is not None}")
    print(f"Classifier pipeline loaded: {processor.classifier_pipeline is not None}")
    
    print("\nLazy loading test completed!")

if __name__ == "__main__":
    test_lazy_loading()