"""
Community Datasets Module - Allow users to share and discover datasets
"""

import os
import json
import datetime
from typing import List, Dict, Optional
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Try to import pymongo for MongoDB support
try:
    from pymongo import MongoClient
    MONGO_AVAILABLE = True
except ImportError:
    MONGO_AVAILABLE = False
    print("pymongo not installed. Install with: pip install pymongo")
    MongoClient = None

class CommunityDatasets:
    """Manage community-shared datasets"""
    
    def __init__(self, community_file: str = "community_datasets.json", 
                 mongodb_uri: Optional[str] = None, database_name: str = "text2dataset"):
        """Initialize community datasets manager"""
        self.community_file = community_file
        self.community_dir = "community"
        self.mongodb_uri = mongodb_uri
        self.database_name = database_name
        self.client = None
        self.db = None
        self.collection = None
        
        # Try to connect to MongoDB if URI is provided
        if mongodb_uri and MONGO_AVAILABLE and MongoClient:
            try:
                self.client = MongoClient(mongodb_uri)
                self.db = self.client[database_name]
                self.collection = self.db["community_datasets"]
                # Test connection
                self.client.admin.command('ping')
                self.use_mongodb = True
                print("Connected to MongoDB Atlas successfully")
            except Exception as e:
                print(f"Failed to connect to MongoDB: {e}")
                self.use_mongodb = False
                self.ensure_community_dir()
        else:
            self.use_mongodb = False
            self.ensure_community_dir()
            
    def ensure_community_dir(self):
        """Ensure community directory exists"""
        if not os.path.exists(self.community_dir):
            os.makedirs(self.community_dir)
            
    def share_dataset(self, filename: str, description: str, tags: List[str], 
                     mode: str, format_type: str, entity_count: int, 
                     user_name: str = "Anonymous", file_path: Optional[str] = None) -> bool:
        """
        Share a dataset with the community
        
        Args:
            filename (str): Name of the dataset file
            description (str): Description of the dataset
            tags (List[str]): Tags for the dataset
            mode (str): Processing mode (fast/smart)
            format_type (str): Output format (csv/json/spacy)
            entity_count (int): Number of entities in the dataset
            user_name (str): Name of the user sharing the dataset
            file_path (str, optional): Path to the dataset file
            
        Returns:
            bool: True if shared successfully
        """
        try:
            # Create community entry
            entry = {
                "filename": filename,
                "description": description,
                "tags": tags,
                "mode": mode,
                "format": format_type,
                "entity_count": entity_count,
                "user_name": user_name,
                "timestamp": datetime.datetime.now().isoformat(),
                "download_count": 0,
                "likes": 0
            }
            
            # Add file_path if provided
            if file_path:
                entry["file_path"] = file_path
            
            if self.use_mongodb and self.collection is not None:
                # Use MongoDB
                result = self.collection.insert_one(entry)
                entry["id"] = str(result.inserted_id)
            else:
                # Use file-based storage
                entry["id"] = self.generate_id()
                
                # Load existing community datasets
                community_datasets = self.get_community_datasets()
                community_datasets.append(entry)
                
                # Save updated community datasets
                community_path = os.path.join(self.community_dir, self.community_file)
                with open(community_path, 'w') as f:
                    json.dump(community_datasets, f, indent=2)
                
            return True
        except Exception as e:
            print(f"Error sharing dataset: {e}")
            return False
            
    def generate_id(self) -> int:
        """Generate a unique ID for a new dataset"""
        community_datasets = self.get_community_datasets()
        if not community_datasets:
            return 1
        # Find max ID and add 1
        max_id = 0
        for dataset in community_datasets:
            try:
                id_val = int(dataset['id'])
                if id_val > max_id:
                    max_id = id_val
            except (ValueError, TypeError):
                continue
        return max_id + 1
            
    def get_community_datasets(self) -> List[Dict]:
        """
        Get all community-shared datasets
        
        Returns:
            List[Dict]: List of community datasets
        """
        if self.use_mongodb and self.collection is not None:
            # Use MongoDB
            try:
                # Get all datasets and include the _id field this time
                datasets = list(self.collection.find({}))
                # Process datasets to ensure they have proper id field
                processed_datasets = []
                for dataset in datasets:
                    # Convert ObjectId to string for the id field
                    from bson import ObjectId
                    if '_id' in dataset:
                        dataset['id'] = str(dataset['_id'])
                        del dataset['_id']
                    processed_datasets.append(dataset)
                return processed_datasets
            except Exception as e:
                print(f"Error retrieving from MongoDB: {e}")
                return []
        else:
            # Use file-based storage
            community_path = os.path.join(self.community_dir, self.community_file)
            if os.path.exists(community_path):
                try:
                    with open(community_path, 'r') as f:
                        return json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    return []
            return []
        
    def get_dataset_by_id(self, dataset_id) -> Dict:
        """
        Get a specific community dataset by ID
        
        Args:
            dataset_id: Dataset ID (can be int or string for MongoDB ObjectId)
            
        Returns:
            Dict: Dataset entry or empty dict if not found
        """
        if self.use_mongodb and self.collection is not None:
            # Use MongoDB
            try:
                from bson import ObjectId
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
            community_datasets = self.get_community_datasets()
            # Handle both string and int IDs
            for entry in community_datasets:
                try:
                    if str(entry['id']) == str(dataset_id):
                        return entry
                except (KeyError, ValueError):
                    continue
            return {}
        
    def search_datasets(self, query: str = "", tags: Optional[List[str]] = None) -> List[Dict]:
        """
        Search community datasets by query and tags
        
        Args:
            query (str): Search query
            tags (List[str], optional): List of tags to filter by
            
        Returns:
            List[Dict]: List of matching datasets
        """
        community_datasets = self.get_community_datasets()
        
        if not query and not tags:
            return community_datasets
            
        results = []
        query = query.lower()
        
        for dataset in community_datasets:
            # Check query match in filename or description
            match = False
            if query:
                if (query in dataset['filename'].lower() or 
                    query in dataset['description'].lower()):
                    match = True
            else:
                match = True
                
            # Check tag match
            if tags and match:
                dataset_tags = [tag.lower() for tag in dataset['tags']]
                if not any(tag.lower() in dataset_tags for tag in tags):
                    match = False
                    
            if match:
                results.append(dataset)
                
        return results
        
    def get_popular_datasets(self, limit: int = 10) -> List[Dict]:
        """
        Get most popular datasets (by downloads + likes)
        
        Args:
            limit (int): Maximum number of datasets to return
            
        Returns:
            List[Dict]: List of popular datasets
        """
        community_datasets = self.get_community_datasets()
        # Sort by popularity score (downloads + likes)
        community_datasets.sort(key=lambda x: x.get('download_count', 0) + x.get('likes', 0), reverse=True)
        return community_datasets[:limit]
        
    def increment_download_count(self, dataset_id) -> bool:
        """
        Increment download count for a dataset
        
        Args:
            dataset_id: Dataset ID
            
        Returns:
            bool: True if incremented successfully
        """
        try:
            if self.use_mongodb and self.collection is not None:
                # Use MongoDB
                from bson import ObjectId
                # Try to update by ObjectId first
                if isinstance(dataset_id, str):
                    try:
                        result = self.collection.update_one(
                            {"_id": ObjectId(dataset_id)}, 
                            {"$inc": {"download_count": 1}}
                        )
                        if result.modified_count > 0:
                            return True
                    except Exception:
                        pass  # Fall back to updating by id field
                        
                # Update by id field
                result = self.collection.update_one(
                    {"id": dataset_id}, 
                    {"$inc": {"download_count": 1}}
                )
                return result.modified_count > 0
            else:
                # Use file-based storage
                community_datasets = self.get_community_datasets()
                updated = False
                for dataset in community_datasets:
                    try:
                        if str(dataset['id']) == str(dataset_id):
                            dataset['download_count'] = dataset.get('download_count', 0) + 1
                            updated = True
                            break
                    except (KeyError, ValueError):
                        continue
                        
                if updated:
                    # Save updated community datasets
                    community_path = os.path.join(self.community_dir, self.community_file)
                    with open(community_path, 'w') as f:
                        json.dump(community_datasets, f, indent=2)
                    return True
            return False
        except Exception as e:
            print(f"Error incrementing download count: {e}")
            return False
            
    def add_like(self, dataset_id) -> bool:
        """
        Add a like to a dataset
        
        Args:
            dataset_id: Dataset ID
            
        Returns:
            bool: True if liked successfully
        """
        try:
            if self.use_mongodb and self.collection is not None:
                # Use MongoDB
                from bson import ObjectId
                # Try to update by ObjectId first
                if isinstance(dataset_id, str):
                    try:
                        result = self.collection.update_one(
                            {"_id": ObjectId(dataset_id)}, 
                            {"$inc": {"likes": 1}}
                        )
                        if result.modified_count > 0:
                            return True
                    except Exception:
                        pass  # Fall back to updating by id field
                        
                # Update by id field
                result = self.collection.update_one(
                    {"id": dataset_id}, 
                    {"$inc": {"likes": 1}}
                )
                return result.modified_count > 0
            else:
                # Use file-based storage
                community_datasets = self.get_community_datasets()
                updated = False
                for dataset in community_datasets:
                    try:
                        if str(dataset['id']) == str(dataset_id):
                            dataset['likes'] = dataset.get('likes', 0) + 1
                            updated = True
                            break
                    except (KeyError, ValueError):
                        continue
                        
                if updated:
                    # Save updated community datasets
                    community_path = os.path.join(self.community_dir, self.community_file)
                    with open(community_path, 'w') as f:
                        json.dump(community_datasets, f, indent=2)
                    return True
            return False
        except Exception as e:
            print(f"Error adding like: {e}")
            return False

# Global instance with MongoDB support
import os
mongodb_uri = os.environ.get("MONGODB_URI", "mongodb+srv://Zain_admin:2ea898dxeI%40@cluster0.flv8jkk.mongodb.net/")
community_datasets = CommunityDatasets(mongodb_uri=mongodb_uri)

if __name__ == "__main__":
    # Example usage
    community = CommunityDatasets(mongodb_uri=mongodb_uri)
    
    # Add some sample entries
    community.share_dataset(
        filename="news_articles.csv",
        description="Dataset of news articles with named entities",
        tags=["news", "NER", "articles"],
        mode="smart",
        format_type="csv",
        entity_count=1250,
        user_name="John Doe"
    )
    
    community.share_dataset(
        filename="financial_reports.json",
        description="Financial reports with monetary entities",
        tags=["finance", "money", "reports"],
        mode="fast",
        format_type="json",
        entity_count=875,
        user_name="Jane Smith"
    )
    
    # Display community datasets
    print("Community Datasets:")
    print("-" * 50)
    datasets = community.get_community_datasets()
    for dataset in datasets:
        print(f"ID: {dataset['id']}")
        print(f"File: {dataset['filename']}")
        print(f"Description: {dataset['description']}")
        print(f"Tags: {', '.join(dataset['tags'])}")
        print(f"Mode: {dataset['mode']}")
        print(f"Format: {dataset['format']}")
        print(f"Entities: {dataset['entity_count']}")
        print(f"Shared by: {dataset['user_name']}")
        print(f"Likes: {dataset['likes']}, Downloads: {dataset['download_count']}")
        print("-" * 30)