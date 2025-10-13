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
        self.chat_collection = None  # For dataset-specific chat messages
        self.global_chat_collection = None  # For global chat messages
        
        # Try to connect to MongoDB if URI is provided
        if mongodb_uri and MONGO_AVAILABLE and MongoClient:
            try:
                self.client = MongoClient(mongodb_uri)
                self.db = self.client[database_name]
                self.collection = self.db["community_datasets"]
                self.chat_collection = self.db["community_chats"]  # Collection for dataset-specific chat messages
                self.global_chat_collection = self.db["global_chats"]  # Collection for global chat messages
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
        # Also ensure the community datasets file exists
        community_path = os.path.join(self.community_dir, self.community_file)
        if not os.path.exists(community_path):
            with open(community_path, 'w') as f:
                json.dump([], f)
            
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
            
            # Add file_path if provided, otherwise construct it
            if file_path:
                # Normalize the file path to ensure it's in the outputs directory
                if not os.path.isabs(file_path):
                    # If it's a relative path, make sure it's in outputs
                    # First normalize the path separators
                    file_path = file_path.replace("/", os.sep).replace("\\", os.sep)
                    
                    # Check if it already starts with outputs/ (handle both / and \ separators)
                    if not (file_path.startswith("outputs" + os.sep) or file_path.startswith("outputs")):
                        entry["file_path"] = os.path.join("outputs", file_path)
                    else:
                        # If it already starts with outputs/, normalize it
                        if file_path.startswith("outputs" + os.sep):
                            # Already correctly formatted
                            entry["file_path"] = file_path
                        elif file_path.startswith("outputs"):
                            # Convert to proper OS separator
                            entry["file_path"] = "outputs" + os.sep + file_path[7:]  # Skip "outputs/"
                        else:
                            entry["file_path"] = os.path.join("outputs", file_path)
                else:
                    # If it's an absolute path, keep it as is
                    entry["file_path"] = file_path
            else:
                # Construct file path based on filename
                entry["file_path"] = os.path.join("outputs", filename)
            
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

    def add_chat_message(self, dataset_id: str, user_name: str, message: str) -> bool:
        """
        Add a chat message to a dataset discussion
        
        Args:
            dataset_id (str): ID of the dataset
            user_name (str): Name of the user posting the message
            message (str): The chat message content
            
        Returns:
            bool: True if message was added successfully
        """
        try:
            chat_entry = {
                "dataset_id": dataset_id,
                "user_name": user_name,
                "message": message,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            if self.use_mongodb and self.chat_collection is not None:
                # Use MongoDB for chat messages
                self.chat_collection.insert_one(chat_entry)
                return True
            else:
                # Use file-based storage for chat messages
                chat_file = os.path.join(self.community_dir, f"chat_{dataset_id}.json")
                chats = []
                if os.path.exists(chat_file):
                    try:
                        with open(chat_file, 'r') as f:
                            chats = json.load(f)
                    except (json.JSONDecodeError, FileNotFoundError):
                        chats = []
                
                chats.append(chat_entry)
                
                with open(chat_file, 'w') as f:
                    json.dump(chats, f, indent=2)
                
                return True
        except Exception as e:
            print(f"Error adding chat message: {e}")
            return False
            
    def get_chat_messages(self, dataset_id: str) -> List[Dict]:
        """
        Get all chat messages for a specific dataset
        
        Args:
            dataset_id (str): ID of the dataset
            
        Returns:
            List[Dict]: List of chat messages
        """
        if self.use_mongodb and self.chat_collection is not None:
            # Use MongoDB for chat messages
            try:
                messages = list(self.chat_collection.find({"dataset_id": dataset_id}))
                # Process messages to ensure they have proper id field
                processed_messages = []
                for message in messages:
                    # Convert ObjectId to string for the id field
                    from bson import ObjectId
                    if '_id' in message:
                        message['id'] = str(message['_id'])
                        del message['_id']
                    processed_messages.append(message)
                # Sort by timestamp (oldest first)
                processed_messages.sort(key=lambda x: x.get('timestamp', ''))
                return processed_messages
            except Exception as e:
                print(f"Error retrieving chat messages from MongoDB: {e}")
                return []
        else:
            # Use file-based storage for chat messages
            chat_file = os.path.join(self.community_dir, f"chat_{dataset_id}.json")
            if os.path.exists(chat_file):
                try:
                    with open(chat_file, 'r') as f:
                        messages = json.load(f)
                    # Sort by timestamp (oldest first)
                    messages.sort(key=lambda x: x.get('timestamp', ''))
                    return messages
                except (json.JSONDecodeError, FileNotFoundError):
                    return []
            return []

    def add_global_chat_message(self, user_name: str, message: str) -> bool:
        """
        Add a message to the global chat
        
        Args:
            user_name (str): Name of the user posting the message
            message (str): The chat message content
            
        Returns:
            bool: True if message was added successfully
        """
        try:
            chat_entry = {
                "user_name": user_name,
                "message": message,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            if self.use_mongodb and self.global_chat_collection is not None:
                # Use MongoDB for global chat messages
                self.global_chat_collection.insert_one(chat_entry)
                return True
            else:
                # Use file-based storage for global chat messages
                global_chat_file = os.path.join(self.community_dir, "global_chat.json")
                chats = []
                if os.path.exists(global_chat_file):
                    try:
                        with open(global_chat_file, 'r') as f:
                            chats = json.load(f)
                    except (json.JSONDecodeError, FileNotFoundError):
                        chats = []
                
                chats.append(chat_entry)
                
                with open(global_chat_file, 'w') as f:
                    json.dump(chats, f, indent=2)
                
                return True
        except Exception as e:
            print(f"Error adding global chat message: {e}")
            return False
            
    def get_global_chat_messages(self, limit: int = 50) -> List[Dict]:
        """
        Get global chat messages
        
        Args:
            limit (int): Maximum number of messages to retrieve
            
        Returns:
            List[Dict]: List of global chat messages
        """
        if self.use_mongodb and self.global_chat_collection is not None:
            # Use MongoDB for global chat messages
            try:
                # Get latest messages (sorted by timestamp, newest first)
                messages = list(self.global_chat_collection.find({}).sort("timestamp", -1).limit(limit))
                # Process messages to ensure they have proper id field
                processed_messages = []
                for message in messages:
                    # Convert ObjectId to string for the id field
                    from bson import ObjectId
                    if '_id' in message:
                        message['id'] = str(message['_id'])
                        del message['_id']
                    processed_messages.append(message)
                # Sort by timestamp (oldest first for display)
                processed_messages.sort(key=lambda x: x.get('timestamp', ''))
                return processed_messages
            except Exception as e:
                print(f"Error retrieving global chat messages from MongoDB: {e}")
                return []
        else:
            # Use file-based storage for global chat messages
            global_chat_file = os.path.join(self.community_dir, "global_chat.json")
            if os.path.exists(global_chat_file):
                try:
                    with open(global_chat_file, 'r') as f:
                        messages = json.load(f)
                    # Sort by timestamp (oldest first for display)
                    messages.sort(key=lambda x: x.get('timestamp', ''))
                    # Return only the latest messages if there are more than the limit
                    if len(messages) > limit:
                        return messages[-limit:]
                    return messages
                except (json.JSONDecodeError, FileNotFoundError):
                    return []
            return []

    def delete_dataset(self, dataset_id: str, user_name: str) -> bool:
        """
        Delete a dataset from the community (admin only)
        
        Args:
            dataset_id (str): ID of the dataset to delete
            user_name (str): Name of the user requesting deletion
            
        Returns:
            bool: True if dataset was deleted successfully
        """
        # Check if user is admin
        if user_name != "admin":
            print(f"User {user_name} is not authorized to delete datasets")
            return False
            
        try:
            if self.use_mongodb and self.collection is not None:
                # Use MongoDB
                from bson import ObjectId
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
            else:
                # Use file-based storage
                community_datasets = self.get_community_datasets()
                updated_datasets = [dataset for dataset in community_datasets if str(dataset['id']) != str(dataset_id)]
                
                if len(updated_datasets) == len(community_datasets):
                    # No dataset was removed, meaning it wasn't found
                    return False
                
                # Save updated community datasets
                community_path = os.path.join(self.community_dir, self.community_file)
                with open(community_path, 'w') as f:
                    json.dump(updated_datasets, f, indent=2)
                
                return True
        except Exception as e:
            print(f"Error deleting dataset: {e}")
            return False
            
    def ban_user_from_chat(self, target_user: str, admin_user: str) -> bool:
        """
        Ban a user from chat (admin only)
        
        Args:
            target_user (str): Name of the user to ban
            admin_user (str): Name of the admin requesting the ban
            
        Returns:
            bool: True if user was banned successfully
        """
        # Check if user is admin
        if admin_user != "admin":
            print(f"User {admin_user} is not authorized to ban users")
            return False
            
        try:
            ban_entry = {
                "banned_user": target_user,
                "banned_by": admin_user,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            if self.use_mongodb and self.db is not None:
                # Use MongoDB - store bans in a separate collection
                ban_collection = self.db["chat_bans"]
                ban_collection.insert_one(ban_entry)
                return True
            else:
                # Use file-based storage for bans
                ban_file = os.path.join(self.community_dir, "chat_bans.json")
                bans = []
                if os.path.exists(ban_file):
                    try:
                        with open(ban_file, 'r') as f:
                            bans = json.load(f)
                    except (json.JSONDecodeError, FileNotFoundError):
                        bans = []
                
                bans.append(ban_entry)
                
                with open(ban_file, 'w') as f:
                    json.dump(bans, f, indent=2)
                
                return True
        except Exception as e:
            print(f"Error banning user: {e}")
            return False
            
    def is_user_banned(self, user_name: str) -> bool:
        """
        Check if a user is banned from chat
        
        Args:
            user_name (str): Name of the user to check
            
        Returns:
            bool: True if user is banned
        """
        try:
            if self.use_mongodb and self.db is not None:
                # Use MongoDB
                ban_collection = self.db["chat_bans"]
                ban = ban_collection.find_one({"banned_user": user_name})
                return ban is not None
            else:
                # Use file-based storage
                ban_file = os.path.join(self.community_dir, "chat_bans.json")
                if os.path.exists(ban_file):
                    try:
                        with open(ban_file, 'r') as f:
                            bans = json.load(f)
                        return any(ban["banned_user"] == user_name for ban in bans)
                    except (json.JSONDecodeError, FileNotFoundError):
                        return False
                return False
        except Exception as e:
            print(f"Error checking ban status: {e}")
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