"""
Dataset History Module - Track and manage previously created datasets
"""

import os
import json
import datetime
from typing import List, Dict, Optional
from pathlib import Path
import io

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Try to import pymongo and gridfs for MongoDB support
try:
    from pymongo import MongoClient
    from gridfs import GridFS
    from bson import ObjectId
    MONGO_AVAILABLE = True
except ImportError:
    MONGO_AVAILABLE = False
    print("pymongo/gridfs not installed. Install with: pip install pymongo")
    MongoClient = None
    GridFS = None
    ObjectId = None

class DatasetHistory:
    """Manage dataset creation history"""
    
    def __init__(self, history_file: str = "dataset_history.json", 
                 mongodb_uri: Optional[str] = None, database_name: str = "text2dataset"):
        """Initialize dataset history manager"""
        self.history_file = history_file
        self.history_dir = "history"
        self.mongodb_uri = mongodb_uri
        self.database_name = database_name
        self.client = None
        self.db = None
        self.collection = None
        self.gridfs = None
        self.use_mongodb = False
        
        # Try to connect to MongoDB if URI is provided
        if mongodb_uri and MONGO_AVAILABLE and MongoClient:
            try:
                self.client = MongoClient(mongodb_uri)
                self.db = self.client[database_name]
                self.collection = self.db["dataset_history"]
                self.gridfs = GridFS(self.db) if GridFS else None
                # Test connection
                self.client.admin.command('ping')
                self.use_mongodb = True
                print("Connected to MongoDB Atlas for history successfully")
            except Exception as e:
                print(f"Failed to connect to MongoDB for history: {e}")
                self.use_mongodb = False
                self.ensure_history_dir()
        else:
            self.use_mongodb = False
            self.ensure_history_dir()
            
    def ensure_history_dir(self):
        """Ensure history directory exists"""
        if not os.path.exists(self.history_dir):
            os.makedirs(self.history_dir)
            
    def add_to_history(self, filename: str, mode: str, format_type: str, entity_count: int = 0, file_content: Optional[bytes] = None):
        """
        Add a dataset to history
        
        Args:
            filename (str): Name of the generated file
            mode (str): Processing mode (fast/smart)
            format_type (str): Output format (csv/json/spacy)
            entity_count (int): Number of entities in the dataset
            file_content (bytes): Content of the file to store in GridFS
        """
        # Create history entry
        entry = {
            "filename": filename,
            "mode": mode,
            "format": format_type,
            "entity_count": entity_count,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        if self.use_mongodb and self.collection is not None and self.gridfs is not None:
            # Use MongoDB with GridFS
            if file_content:
                # Store file in GridFS and save the file ID in the entry
                file_id = self.gridfs.put(file_content, filename=filename)
                entry["file_id"] = str(file_id)
            result = self.collection.insert_one(entry)
            entry["id"] = str(result.inserted_id)
            print(f"Added to MongoDB history: {entry}")  # Debug line
        else:
            # Use file-based storage
            entry["id"] = len(self.get_history()) + 1
            file_path = os.path.join("outputs", filename)
            entry["file_path"] = file_path
            
            # Save file to outputs directory
            if file_content:
                os.makedirs("outputs", exist_ok=True)
                with open(file_path, "wb") as f:
                    f.write(file_content)
            
            # Load existing history
            history = self.get_history()
            history.append(entry)
            
            # Save updated history
            history_path = os.path.join(self.history_dir, self.history_file)
            with open(history_path, 'w') as f:
                json.dump(history, f, indent=2)
            print(f"Added to file history: {entry}")  # Debug line
            
    def get_history(self) -> List[Dict]:
        """
        Get dataset creation history
        
        Returns:
            List[Dict]: List of history entries
        """
        if self.use_mongodb and self.collection is not None:
            # Use MongoDB
            try:
                # Get all datasets and include the _id field this time
                datasets = list(self.collection.find({}))
                print(f"Retrieved {len(datasets)} datasets from MongoDB")  # Debug line
                # Process datasets to ensure they have proper id field
                processed_datasets = []
                for dataset in datasets:
                    # Convert ObjectId to string for the id field
                    if '_id' in dataset and ObjectId is not None:
                        dataset['id'] = str(dataset['_id'])
                        del dataset['_id']
                    processed_datasets.append(dataset)
                print(f"Processed datasets: {processed_datasets}")  # Debug line
                return processed_datasets
            except Exception as e:
                print(f"Error retrieving history from MongoDB: {e}")
                return []
        else:
            # Use file-based storage
            history_path = os.path.join(self.history_dir, self.history_file)
            if os.path.exists(history_path):
                try:
                    with open(history_path, 'r') as f:
                        data = json.load(f)
                        print(f"Retrieved {len(data)} datasets from file")  # Debug line
                        print(f"File datasets: {data}")  # Debug line
                        return data
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
        
    def get_dataset_by_id(self, dataset_id) -> Dict:
        """
        Get a specific dataset by ID
        
        Args:
            dataset_id: Dataset ID (can be int or string for MongoDB ObjectId)
            
        Returns:
            Dict: Dataset entry or empty dict if not found
        """
        if self.use_mongodb and self.collection is not None and ObjectId is not None:
            # Use MongoDB
            try:
                # Try to find by ObjectId if dataset_id is a string
                if isinstance(dataset_id, str):
                    try:
                        # First try to find by MongoDB ObjectId
                        dataset = self.collection.find_one({"_id": ObjectId(dataset_id)})
                        if dataset:
                            dataset["id"] = str(dataset["_id"])
                            del dataset["_id"]
                            return dataset
                        
                        # If that fails, try to find by id field
                        dataset = self.collection.find_one({"id": dataset_id})
                        if dataset:
                            # Make sure to convert ObjectId to string
                            dataset["id"] = str(dataset["_id"])
                            del dataset["_id"]
                            return dataset
                    except Exception:
                        # If ObjectId conversion fails, search by id field
                        dataset = self.collection.find_one({"id": dataset_id})
                        if dataset:
                            # Make sure to convert ObjectId to string
                            dataset["id"] = str(dataset["_id"])
                            del dataset["_id"]
                            return dataset
                else:
                    # For non-string IDs, search by id field
                    dataset = self.collection.find_one({"id": dataset_id})
                    if dataset:
                        # Make sure to convert ObjectId to string
                        dataset["id"] = str(dataset["_id"])
                        del dataset["_id"]
                        return dataset
                        
                return {}
            except Exception as e:
                print(f"Error retrieving dataset from MongoDB: {e}")
                return {}
        else:
            # Use file-based storage
            history = self.get_history()
            for entry in history:
                if entry['id'] == dataset_id:
                    return entry
            return {}
        
    def get_file_content(self, dataset: Dict) -> Optional[bytes]:
        """
        Get the file content for a dataset
        
        Args:
            dataset (Dict): Dataset entry
            
        Returns:
            bytes: File content or None if not found
        """
        if self.use_mongodb and self.gridfs is not None and ObjectId is not None:
            # Use MongoDB GridFS
            try:
                if "file_id" in dataset:
                    file_id = dataset["file_id"]
                    # Try to get file by ObjectId
                    try:
                        return self.gridfs.get(ObjectId(file_id)).read()
                    except Exception:
                        # If ObjectId conversion fails, return None
                        return None
                else:
                    # Try to find file by filename
                    grid_out = self.gridfs.find_one({"filename": dataset["filename"]})
                    if grid_out:
                        return grid_out.read()
                    return None
            except Exception as e:
                print(f"Error retrieving file from GridFS: {e}")
                return None
        else:
            # Use file-based storage
            file_path = dataset.get("file_path")
            if file_path and os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    return f.read()
            return None
        
    def delete_dataset(self, dataset_id) -> bool:
        """
        Delete a dataset entry from history (not the actual file)
        
        Args:
            dataset_id: Dataset ID to delete
            
        Returns:
            bool: True if deleted, False if not found
        """
        if self.use_mongodb and self.collection is not None and ObjectId is not None:
            # Use MongoDB
            try:
                # Try to delete by ObjectId first
                if isinstance(dataset_id, str):
                    try:
                        result = self.collection.delete_one({"_id": ObjectId(dataset_id)})
                        if result.deleted_count > 0:
                            return True
                    except Exception:
                        pass  # Fall back to deleting by id field
                        
                # Delete by id field
                result = self.collection.delete_one({"id": dataset_id})
                return result.deleted_count > 0
            except Exception as e:
                print(f"Error deleting dataset from MongoDB: {e}")
                return False
        else:
            # Use file-based storage
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
        if self.use_mongodb and self.collection is not None:
            # Use MongoDB
            try:
                self.collection.delete_many({})
            except Exception as e:
                print(f"Error clearing history in MongoDB: {e}")
        else:
            # Use file-based storage
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

    def delete_user_dataset(self, user_id: str, dataset_id: str) -> bool:
        """
        Delete a user's dataset entry from history (not the actual file)
        
        Args:
            user_id (str): User ID
            dataset_id (str): Dataset ID to delete
            
        Returns:
            bool: True if deleted, False if not found
        """
        if self.use_mongodb and self.db is not None:
            try:
                user_datasets_collection = self.db["user_datasets"]
                # Delete the specific user dataset
                result = user_datasets_collection.delete_one({
                    "user_id": user_id,
                    "user_dataset_id": dataset_id
                })
                return result.deleted_count > 0
            except Exception as e:
                print(f"Error deleting user dataset from MongoDB: {e}")
                return False
        else:
            # For file-based storage, we don't have user-specific datasets
            # This method is primarily for MongoDB implementation
            return False

# Create global instance with MongoDB support
import os
mongodb_uri = os.environ.get("MONGODB_URI", "mongodb+srv://Zain_admin:2ea898dxeI%40@cluster0.flv8jkk.mongodb.net/")
dataset_history = DatasetHistory(mongodb_uri=mongodb_uri)

def format_file_size(size_bytes: float) -> str:
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
    history = DatasetHistory(mongodb_uri=mongodb_uri)
    
    # Add some sample entries
    history.add_to_history("dataset_1.csv", "fast", "csv", 150)
    history.add_to_history("dataset_2.json", "smart", "json", 200)
    history.add_to_history("dataset_3_spacy.json", "fast", "spacy", 175)
    
    # Display recent datasets
    print("Recent Datasets:")
    print("-" * 50)
    recent = history.get_recent_datasets()
    for entry in recent:
        print(f"ID: {entry.get('id', 'N/A')}")
        print(f"File: {entry['filename']}")
        print(f"Mode: {entry['mode']}")
        print(f"Format: {entry['format']}")
        print(f"Entities: {entry['entity_count']}")
        print(f"Created: {entry['timestamp']}")
        print("-" * 30)