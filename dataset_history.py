"""
Dataset History Module - Track and manage previously created datasets
"""

import os
import json
import datetime
from typing import List, Dict
from pathlib import Path

class DatasetHistory:
    """Manage dataset creation history"""
    
    def __init__(self, history_file: str = "dataset_history.json"):
        """Initialize dataset history manager"""
        self.history_file = history_file
        self.history_dir = "history"
        self.ensure_history_dir()
        
    def ensure_history_dir(self):
        """Ensure history directory exists"""
        if not os.path.exists(self.history_dir):
            os.makedirs(self.history_dir)
            
    def add_to_history(self, filename: str, mode: str, format_type: str, entity_count: int = 0):
        """
        Add a dataset to history
        
        Args:
            filename (str): Name of the generated file
            mode (str): Processing mode (fast/smart)
            format_type (str): Output format (csv/json/spacy)
            entity_count (int): Number of entities in the dataset
        """
        # Create history entry
        entry = {
            "id": len(self.get_history()) + 1,
            "filename": filename,
            "mode": mode,
            "format": format_type,
            "entity_count": entity_count,
            "timestamp": datetime.datetime.now().isoformat(),
            "file_path": os.path.join("outputs", filename)
        }
        
        # Load existing history
        history = self.get_history()
        history.append(entry)
        
        # Save updated history
        history_path = os.path.join(self.history_dir, self.history_file)
        with open(history_path, 'w') as f:
            json.dump(history, f, indent=2)
            
    def get_history(self) -> List[Dict]:
        """
        Get dataset creation history
        
        Returns:
            List[Dict]: List of history entries
        """
        history_path = os.path.join(self.history_dir, self.history_file)
        if os.path.exists(history_path):
            try:
                with open(history_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return []
        return []
        
    def get_recent_datasets(self, limit: int = 10) -> List[Dict]:
        """
        Get most recent datasets
        
        Args:
            limit (int): Maximum number of datasets to return
            
        Returns:
            List[Dict]: List of recent history entries
        """
        history = self.get_history()
        # Sort by timestamp (newest first)
        history.sort(key=lambda x: x['timestamp'], reverse=True)
        return history[:limit]
        
    def get_dataset_by_id(self, dataset_id: int) -> Dict:
        """
        Get a specific dataset by ID
        
        Args:
            dataset_id (int): Dataset ID
            
        Returns:
            Dict: Dataset entry or empty dict if not found
        """
        history = self.get_history()
        for entry in history:
            if entry['id'] == dataset_id:
                return entry
        return {}
        
    def delete_dataset(self, dataset_id: int) -> bool:
        """
        Delete a dataset entry from history (not the actual file)
        
        Args:
            dataset_id (int): Dataset ID to delete
            
        Returns:
            bool: True if deleted, False if not found
        """
        history = self.get_history()
        original_length = len(history)
        history = [entry for entry in history if entry['id'] != dataset_id]
        
        if len(history) < original_length:
            # Save updated history
            history_path = os.path.join(self.history_dir, self.history_file)
            with open(history_path, 'w') as f:
                json.dump(history, f, indent=2)
            return True
        return False
        
    def clear_history(self):
        """Clear all history"""
        history_path = os.path.join(self.history_dir, self.history_file)
        if os.path.exists(history_path):
            os.remove(history_path)
            
    def get_file_info(self, file_path: str) -> Dict:
        """
        Get file information
        
        Args:
            file_path (str): Path to file
            
        Returns:
            Dict: File information
        """
        try:
            if os.path.exists(file_path):
                stat = os.stat(file_path)
                return {
                    "size": stat.st_size,
                    "created": datetime.datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "exists": True
                }
        except Exception:
            pass
        return {"exists": False}

# Global instance
dataset_history = DatasetHistory()

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
        
    return f"{size_bytes:.1f} {size_names[i]}"

if __name__ == "__main__":
    # Example usage
    history = DatasetHistory()
    
    # Add some sample entries
    history.add_to_history("dataset_1.csv", "fast", "csv", 150)
    history.add_to_history("dataset_2.json", "smart", "json", 200)
    history.add_to_history("dataset_3_spacy.json", "fast", "spacy", 175)
    
    # Display recent datasets
    print("Recent Datasets:")
    print("-" * 50)
    recent = history.get_recent_datasets()
    for entry in recent:
        print(f"ID: {entry['id']}")
        print(f"File: {entry['filename']}")
        print(f"Mode: {entry['mode']}")
        print(f"Format: {entry['format']}")
        print(f"Entities: {entry['entity_count']}")
        print(f"Created: {entry['timestamp']}")
        print("-" * 30)