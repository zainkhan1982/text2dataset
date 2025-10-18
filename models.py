"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel, validator
import re
from typing import Optional, List

class UserRegistration(BaseModel):
    """User registration model."""
    username: str
    password: str
    confirm_password: str
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class UserLogin(BaseModel):
    """User login model."""
    username: str
    password: str

class TextInput(BaseModel):
    """Text input model for dataset generation."""
    text_input: str
    output_format: str = "csv"
    mode: str = "fast"
    custom_name: Optional[str] = None
    language: Optional[str] = "en"
    use_enhanced_nlp: bool = False
    
    @validator('text_input')
    def validate_text_input(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('Text input must be at least 10 characters long')
        if len(v) > 1000000:  # 1MB limit
            raise ValueError('Text input is too large (max 1MB)')
        return v.strip()
    
    @validator('output_format')
    def validate_output_format(cls, v):
        if v not in ['csv', 'json', 'spacy']:
            raise ValueError('Output format must be csv, json, or spacy')
        return v
    
    @validator('mode')
    def validate_mode(cls, v):
        if v not in ['fast', 'smart', 'enhanced']:
            raise ValueError('Mode must be fast, smart, or enhanced')
        return v

class DatasetShare(BaseModel):
    """Dataset sharing model."""
    dataset_id: str
    description: str
    tags: str = ""
    
    @validator('description')
    def validate_description(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Description must be at least 10 characters long')
        if len(v) > 1000:
            raise ValueError('Description is too long (max 1000 characters)')
        return v.strip()

class ChatMessage(BaseModel):
    """Chat message model."""
    message: str
    
    @validator('message')
    def validate_message(cls, v):
        if not v or len(v.strip()) < 1:
            raise ValueError('Message cannot be empty')
        if len(v) > 1000:
            raise ValueError('Message is too long (max 1000 characters)')
        return v.strip()

class DatasetCollection(BaseModel):
    """Dataset collection model."""
    name: str
    description: str = ""
    is_public: bool = False
    dataset_ids: List[str] = []
    
    @validator('name')
    def validate_name(cls, v):
        if len(v.strip()) < 3:
            raise ValueError('Collection name must be at least 3 characters long')
        if len(v) > 100:
            raise ValueError('Collection name is too long (max 100 characters)')
        return v.strip()

class APIKeyRequest(BaseModel):
    """API key creation model."""
    key_name: str
    
    @validator('key_name')
    def validate_key_name(cls, v):
        if len(v.strip()) < 3:
            raise ValueError('Key name must be at least 3 characters long')
        if len(v) > 50:
            raise ValueError('Key name is too long (max 50 characters)')
        return v.strip()

class DatasetVersion(BaseModel):
    """Dataset version model."""
    version_notes: str
    
    @validator('version_notes')
    def validate_version_notes(cls, v):
        if len(v.strip()) < 5:
            raise ValueError('Version notes must be at least 5 characters long')
        if len(v) > 500:
            raise ValueError('Version notes are too long (max 500 characters)')
        return v.strip()
