"""
Enhanced NLP Module with Transformer-based Models for Deeper Text Understanding
"""

import torch
from transformers import (
    AutoTokenizer, 
    AutoModelForTokenClassification,
    AutoModelForSequenceClassification,
    pipeline,
    TranslationPipeline
)
from typing import List, Dict, Tuple, Optional, Any
import logging
import re
from collections import defaultdict

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedNLPProcessor:
    """Enhanced NLP processor with transformer-based models for deeper text understanding."""
    
    def __init__(self):
        """Initialize the enhanced NLP processor with transformer models."""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")
        
        # Initialize models as None for lazy loading
        self.ner_tokenizer = None
        self.ner_model = None
        self.ner_pipeline: Optional[Any] = None
        self.classifier_tokenizer = None
        self.classifier_model = None
        self.classifier_pipeline: Optional[Any] = None
        
        # Flag to track if models failed to load
        self.models_failed = False
    
    def _load_ner_model(self) -> bool:
        """Load NER model lazily when needed."""
        if self.ner_pipeline is not None:
            return True
            
        if self.models_failed:
            return False
            
        try:
            logger.info("Loading NER model...")
            # Named Entity Recognition model
            self.ner_tokenizer = AutoTokenizer.from_pretrained("dslim/bert-base-NER")
            self.ner_model = AutoModelForTokenClassification.from_pretrained("dslim/bert-base-NER")
            self.ner_pipeline = pipeline(
                "ner", 
                model=self.ner_model, 
                tokenizer=self.ner_tokenizer,
                aggregation_strategy="simple",
                device=0 if self.device == "cuda" else -1
            )
            logger.info("NER model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading NER model: {e}")
            self.models_failed = True
            return False
    
    def _load_classifier_model(self) -> bool:
        """Load classifier model lazily when needed."""
        if self.classifier_pipeline is not None:
            return True
            
        if self.models_failed:
            return False
            
        try:
            logger.info("Loading classifier model...")
            # Text classification model for better entity categorization
            self.classifier_tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-mnli")
            self.classifier_model = AutoModelForSequenceClassification.from_pretrained("facebook/bart-large-mnli")
            self.classifier_pipeline = pipeline(
                "zero-shot-classification",
                model=self.classifier_model,
                tokenizer=self.classifier_tokenizer,
                device=0 if self.device == "cuda" else -1
            )
            logger.info("Classifier model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading classifier model: {e}")
            self.models_failed = True
            return False
    
    def extract_entities_transformer(self, text: str) -> List[Dict]:
        """
        Extract named entities using transformer-based NER model.
        
        Args:
            text (str): Input text
            
        Returns:
            List[Dict]: List of entities with their labels and confidence scores
        """
        if not self._load_ner_model() or self.ner_pipeline is None:
            return []
        
        try:
            # Process text with NER pipeline
            entities = self.ner_pipeline(text)
            
            # Format entities
            formatted_entities = []
            for entity in entities:
                formatted_entities.append({
                    "text": text,
                    "entity": entity["word"],
                    "label": entity["entity_group"],
                    "confidence": entity["score"],
                    "start": entity["start"],
                    "end": entity["end"]
                })
            
            return formatted_entities
        except Exception as e:
            logger.error(f"Error in transformer NER: {e}")
            return []
    
    def classify_text_category(self, text: str, candidate_labels: List[str]) -> Dict:
        """
        Classify text into categories using zero-shot classification.
        
        Args:
            text (str): Input text
            candidate_labels (List[str]): Possible categories
            
        Returns:
            Dict: Classification result with labels and scores
        """
        if not self._load_classifier_model() or self.classifier_pipeline is None:
            return {"labels": candidate_labels, "scores": [0.0] * len(candidate_labels)}
        
        try:
            result = self.classifier_pipeline(text, candidate_labels)
            return {
                "labels": result["labels"],
                "scores": result["scores"]
            }
        except Exception as e:
            logger.error(f"Error in text classification: {e}")
            return {"labels": candidate_labels, "scores": [0.0] * len(candidate_labels)}
    
    def extract_keyphrases(self, text: str, top_k: int = 5) -> List[str]:
        """
        Extract keyphrases using transformer-based models.
        
        Args:
            text (str): Input text
            top_k (int): Number of keyphrases to extract
            
        Returns:
            List[str]: List of keyphrases
        """
        try:
            # Use the classifier to identify important concepts
            concepts = [
                "person", "organization", "location", "date", "time", 
                "money", "percentage", "product", "event", "law"
            ]
            
            # Classify the text to get relevant concepts
            result = self.classify_text_category(text, concepts)
            
            # Extract top concepts as keyphrases
            keyphrases = []
            for i, (label, score) in enumerate(zip(result["labels"], result["scores"])):
                if score > 0.1 and i < top_k:  # Threshold for relevance
                    keyphrases.append(label)
            
            return keyphrases
        except Exception as e:
            logger.error(f"Error in keyphrase extraction: {e}")
            return []
    
    def get_text_embeddings(self, texts: List[str]) -> torch.Tensor:
        """
        Get text embeddings using transformer models.
        
        Args:
            texts (List[str]): List of texts
            
        Returns:
            torch.Tensor: Text embeddings
        """
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            embeddings = model.encode(texts)
            return torch.tensor(embeddings)
        except Exception as e:
            logger.error(f"Error in text embedding: {e}")
            return torch.tensor([])

class MultiLanguageProcessor:
    """Multi-language NLP processor supporting various languages."""
    
    def __init__(self):
        """Initialize multi-language processor."""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.supported_languages = {
            "en": "English",
            "es": "Spanish", 
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "ar": "Arabic"
        }
        
        # Initialize translation models as None for lazy loading
        self.translation_models: Dict[str, Tuple[str, Optional[Any], Optional[Any]]] = {}
        self.loaded_models: Dict[str, Tuple[Any, Any]] = {}
    
    def _load_translation_model(self, model_key: str) -> Optional[Tuple[Any, Any]]:
        """Load translation model lazily when needed."""
        if model_key in self.loaded_models:
            return self.loaded_models[model_key]
            
        try:
            from transformers import MarianMTModel, MarianTokenizer
            
            # Check if we have a model for this language pair
            if model_key not in self.translation_models:
                # Add default models for common language pairs
                default_models = {
                    "en-es": "Helsinki-NLP/opus-mt-en-es",
                    "es-en": "Helsinki-NLP/opus-mt-es-en",
                    "en-fr": "Helsinki-NLP/opus-mt-en-fr",
                    "fr-en": "Helsinki-NLP/opus-mt-fr-en",
                    "en-de": "Helsinki-NLP/opus-mt-en-de",
                    "de-en": "Helsinki-NLP/opus-mt-de-en",
                }
                if model_key in default_models:
                    self.translation_models[model_key] = (default_models[model_key], None, None)
                else:
                    logger.warning(f"No translation model available for {model_key}")
                    return None
            
            # Load model if not already loaded
            model_name, tokenizer, model = self.translation_models[model_key]
            if tokenizer is None or model is None:
                logger.info(f"Loading translation model {model_name}...")
                tokenizer = MarianTokenizer.from_pretrained(model_name)
                model = MarianMTModel.from_pretrained(model_name)
                self.translation_models[model_key] = (model_name, tokenizer, model)
                self.loaded_models[model_key] = (tokenizer, model)
                logger.info(f"Translation model {model_name} loaded successfully")
            
            return (tokenizer, model)
        except Exception as e:
            logger.error(f"Error loading translation model {model_key}: {e}")
            return None
    
    def detect_language(self, text: str) -> str:
        """
        Detect language of text (simplified implementation).
        
        Args:
            text (str): Input text
            
        Returns:
            str: Detected language code
        """
        try:
            # Simple heuristic-based language detection
            # In practice, you would use a proper language detection library
            text = text.lower()
            
            # Character-based detection
            if re.search(r'[\u4e00-\u9fff]', text):
                return "zh"  # Chinese
            elif re.search(r'[\u3040-\u309f\u30a0-\u30ff]', text):
                return "ja"  # Japanese
            elif re.search(r'[\uac00-\ud7af]', text):
                return "ko"  # Korean
            elif re.search(r'[\u0600-\u06ff]', text):
                return "ar"  # Arabic
            
            # Word-based detection for European languages
            spanish_words = {"el", "la", "de", "que", "y", "a", "en", "un", "es", "se"}
            french_words = {"le", "la", "de", "et", "est", "en", "un", "que", "je", "il"}
            german_words = {"der", "die", "und", "in", "den", "von", "zu", "das", "mit", "ist"}
            
            words = set(re.findall(r'\b\w+\b', text.lower()))
            
            spanish_count = len(words.intersection(spanish_words))
            french_count = len(words.intersection(french_words))
            german_count = len(words.intersection(german_words))
            
            if spanish_count > french_count and spanish_count > german_count:
                return "es"
            elif french_count > spanish_count and french_count > german_count:
                return "fr"
            elif german_count > spanish_count and german_count > french_count:
                return "de"
            else:
                return "en"  # Default to English
        except Exception as e:
            logger.error(f"Error in language detection: {e}")
            return "en"
    
    def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Translate text between languages.
        
        Args:
            text (str): Text to translate
            source_lang (str): Source language code
            target_lang (str): Target language code
            
        Returns:
            str: Translated text
        """
        try:
            model_key = f"{source_lang}-{target_lang}"
            
            # Load model if needed
            model_components = self._load_translation_model(model_key)
            if model_components is None:
                logger.warning(f"Could not load translation model for {model_key}")
                return text
            
            tokenizer, model = model_components
            
            # Translate
            inputs = tokenizer(text, return_tensors="pt", padding=True)
            translated = model.generate(**inputs)
            result = tokenizer.decode(translated[0], skip_special_tokens=True)
            
            return result
        except Exception as e:
            logger.error(f"Error in text translation: {e}")
            return text

# Global instances (lazy loading - models won't be loaded until first use)
enhanced_nlp_processor = EnhancedNLPProcessor()
multi_language_processor = MultiLanguageProcessor()

def process_text_enhanced(sentences: List[str]) -> List[Dict]:
    """
    Process text with enhanced NLP for deeper understanding.
    
    Args:
        sentences (List[str]): List of sentences to process
        
    Returns:
        List[Dict]: Enhanced entity extraction results
    """
    results = []
    
    for sentence in sentences:
        if not sentence.strip():
            continue
            
        # Extract entities using transformer model
        entities = enhanced_nlp_processor.extract_entities_transformer(sentence)
        
        # Add confidence scores and better categorization
        for entity in entities:
            # Add keyphrase context
            keyphrases = enhanced_nlp_processor.extract_keyphrases(sentence)
            entity["keyphrases"] = keyphrases
            
            # Add text embedding for similarity comparisons
            # (simplified - in practice you would store embeddings for later use)
            entity["embedding_available"] = True
            
        results.extend(entities)
    
    return results

def process_multilanguage_text(text: str, target_language: str = "en") -> Dict:
    """
    Process multi-language text with translation and enhanced NLP.
    
    Args:
        text (str): Input text
        target_language (str): Target language for processing (default: English)
        
    Returns:
        Dict: Processing results including translation and NLP analysis
    """
    # Detect source language
    source_language = multi_language_processor.detect_language(text)
    
    # Translate if needed
    translated_text = text
    if source_language != target_language:
        translated_text = multi_language_processor.translate_text(
            text, source_language, target_language
        )
    
    # Process with enhanced NLP
    # Split into sentences (simplified)
    sentences = [s.strip() for s in translated_text.split('.') if s.strip()]
    entities = process_text_enhanced(sentences)
    
    return {
        "original_text": text,
        "source_language": source_language,
        "translated_text": translated_text,
        "target_language": target_language,
        "entities": entities,
        "language_detected": source_language != target_language
    }