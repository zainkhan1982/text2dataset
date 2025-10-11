import re
import nltk
from typing import List

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

def clean_text(text: str) -> str:
    """
    Clean and normalize text
    
    Args:
        text (str): Raw input text
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespaces
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespaces
    text = text.strip()
    
    return text

def split_sentences(text: str) -> List[str]:
    """
    Split text into sentences
    
    Args:
        text (str): Cleaned text
        
    Returns:
        List[str]: List of sentences
    """
    if not text:
        return []
    
    # Use NLTK sentence tokenizer
    try:
        from nltk.tokenize import sent_tokenize
        sentences = sent_tokenize(text)
    except Exception:
        # Fallback to simple regex-based splitting
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
    
    return sentences