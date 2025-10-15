"""
Community Datasets Module - Allow users to share and discover datasets
"""

import os
import json
import datetime
import uuid
from typing import List, Dict, Optional
from pathlib import Path
import io

# For MongoDB ObjectId handling
try:
    from bson import ObjectId
except ImportError:
    ObjectId = None

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Try to import pymongo and gridfs for MongoDB support
try:
    from pymongo import MongoClient
    from gridfs import GridFS
    MONGO_AVAILABLE = True
except ImportError:
    MONGO_AVAILABLE = False
    print("pymongo/gridfs not installed. Install with: pip install pymongo")
    MongoClient = None
    GridFS = None

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
        self.dataset_versions_collection = None  # For dataset versioning
        self.dataset_collections_collection = None  # For dataset collections
        self.notifications_collection = None  # For notifications
        self.api_keys_collection = None  # For API key management
        self.gridfs = None  # For GridFS file storage
        self.use_mongodb = False
        
        # Try to connect to MongoDB if URI is provided
        if mongodb_uri and MONGO_AVAILABLE and MongoClient:
            try:
                self.client = MongoClient(mongodb_uri)
                self.db = self.client[database_name]
                self.collection = self.db["community_datasets"]
                self.chat_collection = self.db["community_chats"]  # Collection for dataset-specific chat messages
                self.global_chat_collection = self.db["global_chats"]  # Collection for global chat messages
                self.dataset_versions_collection = self.db["dataset_versions"]  # Collection for dataset versioning
                self.dataset_collections_collection = self.db["dataset_collections"]  # Collection for dataset collections
                self.notifications_collection = self.db["notifications"]  # Collection for notifications
                self.api_keys_collection = self.db["api_keys"]  # Collection for API key management
                self.gridfs = GridFS(self.db) if GridFS else None
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
                     user_name: str = "Anonymous", file_content: Optional[bytes] = None) -> bool:
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
            file_content (bytes): Content of the file to store in GridFS
            
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
            
            if self.use_mongodb and self.collection is not None and self.gridfs is not None:
                # Use MongoDB with GridFS
                if file_content:
                    # Store file in GridFS and save the file ID in the entry
                    file_id = self.gridfs.put(file_content, filename=filename)
                    entry["file_id"] = str(file_id)
                result = self.collection.insert_one(entry)
                entry["id"] = str(result.inserted_id)
            else:
                # Use file-based storage
                entry["id"] = self.generate_id()
                
                # Save file to outputs directory
                if file_content:
                    file_path = os.path.join("outputs", filename)
                    os.makedirs("outputs", exist_ok=True)
                    with open(file_path, "wb") as f:
                        f.write(file_content)
                    entry["file_path"] = file_path
                
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
                    if '_id' in dataset and ObjectId is not None:
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
            community_datasets = self.get_community_datasets()
            # Handle both string and int IDs
            for entry in community_datasets:
                try:
                    if str(entry['id']) == str(dataset_id):
                        return entry
                except (KeyError, ValueError):
                    continue
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
        if self.use_mongodb and self.collection is not None and ObjectId is not None:
            # Use MongoDB
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
        
    def add_like(self, dataset_id, user_name = None) -> bool:
        """
        Add a like to a dataset
        
        Args:
            dataset_id: Dataset ID
            user_name: Name of the user liking the dataset (optional)
            
        Returns:
            bool: True if liked successfully
        """
        # If user_name is provided, check if user has already liked this dataset
        if user_name and self.use_mongodb and self.db is not None:
            try:
                # Check if user has already liked this dataset
                likes_collection = self.db["dataset_likes"]
                existing_like = likes_collection.find_one({
                    "dataset_id": dataset_id,
                    "user_name": user_name
                })
                
                if existing_like:
                    # User has already liked this dataset
                    return False
                    
                # Record the like
                likes_collection.insert_one({
                    "dataset_id": dataset_id,
                    "user_name": user_name,
                    "timestamp": datetime.datetime.now().isoformat()
                })
            except Exception as e:
                print(f"Error recording like: {e}")
                # Continue with the like process even if we can't record the user
        
        if self.use_mongodb and self.collection is not None and ObjectId is not None:
            # Use MongoDB
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
                    if '_id' in message and ObjectId is not None:
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
                    if '_id' in message and ObjectId is not None:
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
        Delete a dataset from the community (owners and admin only)
        
        Args:
            dataset_id (str): ID of the dataset to delete
            user_name (str): Name of the user requesting deletion
            
        Returns:
            bool: True if dataset was deleted successfully
        """
        # Check if user is admin or the owner of the dataset
        dataset = self.get_dataset_by_id(dataset_id)
        if not dataset:
            print(f"Dataset {dataset_id} not found")
            return False
            
        is_owner = dataset.get("user_name") == user_name
        is_admin = user_name == "admin"
        
        if not is_owner and not is_admin:
            print(f"User {user_name} is not authorized to delete dataset {dataset_id}")
            return False
            
        try:
            if self.use_mongodb and self.collection is not None and ObjectId is not None:
                # Use MongoDB
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

    def create_dataset_version(self, dataset_id: str, version_notes: str, user_name: str) -> bool:
        """
        Create a new version of a dataset
        
        Args:
            dataset_id (str): ID of the original dataset
            version_notes (str): Notes about changes in this version
            user_name (str): Name of the user creating the version
            
        Returns:
            bool: True if version was created successfully
        """
        try:
            # Get the original dataset
            original_dataset = self.get_dataset_by_id(dataset_id)
            if not original_dataset:
                return False
                
            # Create version entry
            version_entry = {
                "dataset_id": dataset_id,
                "version": self._get_next_version_number(dataset_id),
                "original_dataset": original_dataset,
                "version_notes": version_notes,
                "created_by": user_name,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            if self.use_mongodb and self.dataset_versions_collection is not None:
                # Use MongoDB for version storage
                self.dataset_versions_collection.insert_one(version_entry)
                return True
            else:
                # Use file-based storage for versions
                versions_file = os.path.join(self.community_dir, f"versions_{dataset_id}.json")
                versions = []
                if os.path.exists(versions_file):
                    try:
                        with open(versions_file, 'r') as f:
                            versions = json.load(f)
                    except (json.JSONDecodeError, FileNotFoundError):
                        versions = []
                
                versions.append(version_entry)
                
                with open(versions_file, 'w') as f:
                    json.dump(versions, f, indent=2)
                
                return True
        except Exception as e:
            print(f"Error creating dataset version: {e}")
            return False
            
    def _get_next_version_number(self, dataset_id: str) -> int:
        """
        Get the next version number for a dataset
        
        Args:
            dataset_id (str): ID of the dataset
            
        Returns:
            int: Next version number
        """
        try:
            if self.use_mongodb and self.dataset_versions_collection is not None:
                # Use MongoDB
                versions = list(self.dataset_versions_collection.find({"dataset_id": dataset_id}))
                return len(versions) + 1
            else:
                # Use file-based storage
                versions_file = os.path.join(self.community_dir, f"versions_{dataset_id}.json")
                if os.path.exists(versions_file):
                    try:
                        with open(versions_file, 'r') as f:
                            versions = json.load(f)
                        return len(versions) + 1
                    except (json.JSONDecodeError, FileNotFoundError):
                        return 1
                return 1
        except Exception:
            return 1
            
    def get_dataset_versions(self, dataset_id: str) -> List[Dict]:
        """
        Get all versions of a dataset
        
        Args:
            dataset_id (str): ID of the dataset
            
        Returns:
            List[Dict]: List of dataset versions
        """
        if self.use_mongodb and self.dataset_versions_collection is not None:
            # Use MongoDB
            try:
                versions = list(self.dataset_versions_collection.find({"dataset_id": dataset_id}))
                # Process versions to ensure they have proper id field
                processed_versions = []
                for version in versions:
                    # Convert ObjectId to string for the id field
                    if '_id' in version and ObjectId is not None:
                        version['id'] = str(version['_id'])
                        del version['_id']
                    processed_versions.append(version)
                return processed_versions
            except Exception as e:
                print(f"Error retrieving dataset versions from MongoDB: {e}")
                return []
        else:
            # Use file-based storage
            versions_file = os.path.join(self.community_dir, f"versions_{dataset_id}.json")
            if os.path.exists(versions_file):
                try:
                    with open(versions_file, 'r') as f:
                        return json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    return []
            return []
            
    def create_dataset_collection(self, name: str, description: str, is_public: bool, 
                                 dataset_ids: List[str], user_name: str) -> bool:
        """
        Create a collection of datasets
        
        Args:
            name (str): Name of the collection
            description (str): Description of the collection
            is_public (bool): Whether the collection is public
            dataset_ids (List[str]): List of dataset IDs in the collection
            user_name (str): Name of the user creating the collection
            
        Returns:
            bool: True if collection was created successfully
        """
        try:
            collection_entry = {
                "name": name,
                "description": description,
                "is_public": is_public,
                "dataset_ids": dataset_ids,
                "created_by": user_name,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            if self.use_mongodb and self.dataset_collections_collection is not None:
                # Use MongoDB for collection storage
                result = self.dataset_collections_collection.insert_one(collection_entry)
                collection_entry["id"] = str(result.inserted_id)
            else:
                # Use file-based storage for collections
                collection_entry["id"] = self._generate_collection_id()
                collections_file = os.path.join(self.community_dir, "dataset_collections.json")
                collections = []
                if os.path.exists(collections_file):
                    try:
                        with open(collections_file, 'r') as f:
                            collections = json.load(f)
                    except (json.JSONDecodeError, FileNotFoundError):
                        collections = []
                
                collections.append(collection_entry)
                
                with open(collections_file, 'w') as f:
                    json.dump(collections, f, indent=2)
                
            return True
        except Exception as e:
            print(f"Error creating dataset collection: {e}")
            return False
            
    def _generate_collection_id(self) -> str:
        """
        Generate a unique ID for a dataset collection
        
        Returns:
            str: Unique collection ID
        """
        return str(uuid.uuid4())
        
    def get_user_collections(self, user_name: str) -> List[Dict]:
        """
        Get all collections created by a user
        
        Args:
            user_name (str): Name of the user
            
        Returns:
            List[Dict]: List of user's collections
        """
        if self.use_mongodb and self.dataset_collections_collection is not None:
            # Use MongoDB
            try:
                collections = list(self.dataset_collections_collection.find({"created_by": user_name}))
                # Process collections to ensure they have proper id field
                processed_collections = []
                for collection in collections:
                    # Convert ObjectId to string for the id field
                    if '_id' in collection and ObjectId is not None:
                        collection['id'] = str(collection['_id'])
                        del collection['_id']
                    processed_collections.append(collection)
                return processed_collections
            except Exception as e:
                print(f"Error retrieving user collections from MongoDB: {e}")
                return []
        else:
            # Use file-based storage
            collections_file = os.path.join(self.community_dir, "dataset_collections.json")
            if os.path.exists(collections_file):
                try:
                    with open(collections_file, 'r') as f:
                        collections = json.load(f)
                    # Filter by user name
                    user_collections = [c for c in collections if c.get("created_by") == user_name]
                    return user_collections
                except (json.JSONDecodeError, FileNotFoundError):
                    return []
            return []

    def get_public_collections(self) -> List[Dict]:
        """
        Get all public collections
        
        Returns:
            List[Dict]: List of public collections
        """
        if self.use_mongodb and self.dataset_collections_collection is not None:
            # Use MongoDB
            try:
                collections = list(self.dataset_collections_collection.find({"is_public": True}))
                # Process collections to ensure they have proper id field
                processed_collections = []
                for collection in collections:
                    # Convert ObjectId to string for the id field
                    if '_id' in collection and ObjectId is not None:
                        collection['id'] = str(collection['_id'])
                        del collection['_id']
                    processed_collections.append(collection)
                return processed_collections
            except Exception as e:
                print(f"Error retrieving public collections from MongoDB: {e}")
                return []
        else:
            # Use file-based storage
            collections_file = os.path.join(self.community_dir, "dataset_collections.json")
            if os.path.exists(collections_file):
                try:
                    with open(collections_file, 'r') as f:
                        collections = json.load(f)
                    # Filter by public status
                    public_collections = [c for c in collections if c.get("is_public", False)]
                    return public_collections
                except (json.JSONDecodeError, FileNotFoundError):
                    return []
            return []

    def add_notification(self, user_name: str, message: str, notification_type: str) -> bool:
        """
        Add a notification for a user
        
        Args:
            user_name (str): Name of the user
            message (str): Notification message
            notification_type (str): Type of notification
            
        Returns:
            bool: True if notification was added successfully
        """
        try:
            notification_entry = {
                "user_name": user_name,
                "message": message,
                "type": notification_type,
                "timestamp": datetime.datetime.now().isoformat(),
                "read": False
            }
            
            if self.use_mongodb and self.notifications_collection is not None:
                # Use MongoDB for notifications
                result = self.notifications_collection.insert_one(notification_entry)
                notification_entry["id"] = str(result.inserted_id)
                return True
            else:
                # Use file-based storage for notifications
                notifications_file = os.path.join(self.community_dir, f"notifications_{user_name}.json")
                notifications = []
                if os.path.exists(notifications_file):
                    try:
                        with open(notifications_file, 'r') as f:
                            notifications = json.load(f)
                    except (json.JSONDecodeError, FileNotFoundError):
                        notifications = []
                
                # Generate a simple ID
                notification_entry["id"] = len(notifications) + 1
                notifications.append(notification_entry)
                
                with open(notifications_file, 'w') as f:
                    json.dump(notifications, f, indent=2)
                
                return True
        except Exception as e:
            print(f"Error adding notification: {e}")
            return False

    def get_user_notifications(self, user_name: str) -> List[Dict]:
        """
        Get all notifications for a user
        
        Args:
            user_name (str): Name of the user
            
        Returns:
            List[Dict]: List of user notifications
        """
        if self.use_mongodb and self.notifications_collection is not None:
            # Use MongoDB
            try:
                notifications = list(self.notifications_collection.find({"user_name": user_name}))
                # Process notifications to ensure they have proper id field
                processed_notifications = []
                for notification in notifications:
                    # Convert ObjectId to string for the id field
                    if '_id' in notification and ObjectId is not None:
                        notification['id'] = str(notification['_id'])
                        del notification['_id']
                    processed_notifications.append(notification)
                # Sort by timestamp (newest first)
                processed_notifications.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
                return processed_notifications
            except Exception as e:
                print(f"Error retrieving user notifications from MongoDB: {e}")
                return []
        else:
            # Use file-based storage
            notifications_file = os.path.join(self.community_dir, f"notifications_{user_name}.json")
            if os.path.exists(notifications_file):
                try:
                    with open(notifications_file, 'r') as f:
                        notifications = json.load(f)
                    # Sort by timestamp (newest first)
                    notifications.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
                    return notifications
                except (json.JSONDecodeError, FileNotFoundError):
                    return []
            return []

    def mark_notification_as_read(self, user_name: str, notification_id: str) -> bool:
        """
        Mark a notification as read
        
        Args:
            user_name (str): Name of the user
            notification_id (str): ID of the notification
            
        Returns:
            bool: True if notification was marked as read successfully
        """
        if self.use_mongodb and self.notifications_collection is not None and ObjectId is not None:
            # Use MongoDB
            try:
                # Try to update by ObjectId first
                if isinstance(notification_id, str):
                    try:
                        result = self.notifications_collection.update_one(
                            {"_id": ObjectId(notification_id), "user_name": user_name}, 
                            {"$set": {"read": True}}
                        )
                        if result.modified_count > 0:
                            return True
                    except Exception:
                        pass  # Fall back to updating by id field
                        
                # Update by id field
                result = self.notifications_collection.update_one(
                    {"id": notification_id, "user_name": user_name}, 
                    {"$set": {"read": True}}
                )
                return result.modified_count > 0
            except Exception as e:
                print(f"Error marking notification as read in MongoDB: {e}")
                return False
        else:
            # Use file-based storage
            notifications_file = os.path.join(self.community_dir, f"notifications_{user_name}.json")
            if os.path.exists(notifications_file):
                try:
                    with open(notifications_file, 'r') as f:
                        notifications = json.load(f)
                    
                    updated = False
                    for notification in notifications:
                        if str(notification.get('id')) == str(notification_id):
                            notification['read'] = True
                            updated = True
                            break
                    
                    if updated:
                        with open(notifications_file, 'w') as f:
                            json.dump(notifications, f, indent=2)
                        return True
                except (json.JSONDecodeError, FileNotFoundError):
                    pass
            return False

    def create_api_key(self, user_name: str, key_name: str) -> str:
        """
        Create an API key for a user
        
        Args:
            user_name (str): Name of the user
            key_name (str): Name for the API key
            
        Returns:
            str: Generated API key or empty string if failed
        """
        try:
            # Generate a unique API key
            import secrets
            api_key = secrets.token_urlsafe(32)
            
            key_entry = {
                "user_name": user_name,
                "key_name": key_name,
                "api_key": api_key,
                "created_at": datetime.datetime.now().isoformat(),
                "last_used": None
            }
            
            if self.use_mongodb and self.api_keys_collection is not None:
                # Use MongoDB for API keys
                self.api_keys_collection.insert_one(key_entry)
                return api_key
            else:
                # Use file-based storage for API keys
                api_keys_file = os.path.join(self.community_dir, f"api_keys_{user_name}.json")
                api_keys = []
                if os.path.exists(api_keys_file):
                    try:
                        with open(api_keys_file, 'r') as f:
                            api_keys = json.load(f)
                    except (json.JSONDecodeError, FileNotFoundError):
                        api_keys = []
                
                api_keys.append(key_entry)
                
                with open(api_keys_file, 'w') as f:
                    json.dump(api_keys, f, indent=2)
                
                return api_key
        except Exception as e:
            print(f"Error creating API key: {e}")
            return ""

    def validate_api_key(self, api_key: str) -> str:
        """
        Validate an API key and return the associated user name
        
        Args:
            api_key (str): API key to validate
            
        Returns:
            str: User name if valid, empty string if invalid
        """
        if self.use_mongodb and self.api_keys_collection is not None:
            # Use MongoDB
            try:
                key_entry = self.api_keys_collection.find_one({"api_key": api_key})
                if key_entry:
                    # Update last used timestamp
                    self.api_keys_collection.update_one(
                        {"_id": key_entry["_id"]}, 
                        {"$set": {"last_used": datetime.datetime.now().isoformat()}}
                    )
                    return key_entry["user_name"]
            except Exception as e:
                print(f"Error validating API key in MongoDB: {e}")
        else:
            # Use file-based storage
            # Check all user API key files
            import glob
            api_keys_files = glob.glob(os.path.join(self.community_dir, "api_keys_*.json"))
            for api_keys_file in api_keys_files:
                try:
                    with open(api_keys_file, 'r') as f:
                        api_keys = json.load(f)
                    for key_entry in api_keys:
                        if key_entry.get("api_key") == api_key:
                            # Update last used timestamp
                            key_entry["last_used"] = datetime.datetime.now().isoformat()
                            with open(api_keys_file, 'w') as f:
                                json.dump(api_keys, f, indent=2)
                            # Extract user name from filename
                            user_name = os.path.basename(api_keys_file)[9:-5]  # Remove "api_keys_" and ".json"
                            return user_name
                except (json.JSONDecodeError, FileNotFoundError):
                    continue
        return ""

    def calculate_dataset_quality_score(self, dataset_id: str) -> Dict:
        """
        Calculate quality metrics for a dataset
        
        Args:
            dataset_id (str): ID of the dataset
            
        Returns:
            Dict: Quality metrics
        """
        # Get the dataset
        dataset = self.get_dataset_by_id(dataset_id)
        if not dataset:
            return {}
        
        # Basic quality metrics
        quality_metrics = {
            "entity_count": dataset.get("entity_count", 0),
            "description_length": len(dataset.get("description", "")),
            "tag_count": len(dataset.get("tags", [])),
            "download_count": dataset.get("download_count", 0),
            "like_count": dataset.get("likes", 0),
            "engagement_score": dataset.get("download_count", 0) + dataset.get("likes", 0)
        }
        
        # Calculate overall quality score (simple weighted sum)
        quality_score = (
            min(quality_metrics["entity_count"] / 100, 1) * 30 +  # Entity count (max 30 points)
            min(quality_metrics["description_length"] / 100, 1) * 20 +  # Description length (max 20 points)
            min(quality_metrics["tag_count"] / 5, 1) * 10 +  # Tag count (max 10 points)
            min(quality_metrics["engagement_score"] / 50, 1) * 40  # Engagement (max 40 points)
        )
        
        quality_metrics["overall_score"] = round(quality_score, 2)
        
        return quality_metrics

# Create global instance with MongoDB support
import os
mongodb_uri = os.environ.get("MONGODB_URI", "mongodb+srv://Zain_admin:2ea898dxeI%40@cluster0.flv8jkk.mongodb.net/")
community_datasets = CommunityDatasets(mongodb_uri=mongodb_uri)