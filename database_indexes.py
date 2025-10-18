"""
Database indexing and optimization utilities
"""

import logging
from typing import List, Dict, Any, Optional
from pymongo import ASCENDING, DESCENDING, TEXT, HASHED
from bson import ObjectId

logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    """Database optimization and indexing manager."""
    
    def __init__(self, db):
        self.db = db
        self.indexes_created = set()
    
    def create_all_indexes(self):
        """Create all necessary indexes for optimal performance."""
        try:
            self.create_user_indexes()
            self.create_dataset_indexes()
            self.create_community_indexes()
            self.create_chat_indexes()
            self.create_collection_indexes()
            self.create_notification_indexes()
            self.create_api_key_indexes()
            logger.info("All database indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating database indexes: {e}")
            raise
    
    def create_user_indexes(self):
        """Create indexes for user collections."""
        if not self.db:
            return
        
        # Users collection indexes
        users_collection = self.db["users"]
        
        indexes = [
            # Username index (unique)
            {"keys": [("username", ASCENDING)], "options": {"unique": True}},
            # Created_at index for sorting
            {"keys": [("created_at", DESCENDING)]},
            # Email index (if email field exists)
            {"keys": [("email", ASCENDING)], "options": {"sparse": True}},
        ]
        
        for index in indexes:
            try:
                index_name = self._create_index(users_collection, index["keys"], index.get("options", {}))
                self.indexes_created.add(f"users.{index_name}")
            except Exception as e:
                logger.warning(f"Could not create user index: {e}")
    
    def create_dataset_indexes(self):
        """Create indexes for dataset history collections."""
        if not self.db:
            return
        
        # User datasets collection indexes
        user_datasets_collection = self.db["user_datasets"]
        
        indexes = [
            # User ID index for fast user dataset queries
            {"keys": [("user_id", ASCENDING)]},
            # User ID + timestamp for user's recent datasets
            {"keys": [("user_id", ASCENDING), ("timestamp", DESCENDING)]},
            # User dataset ID index (unique)
            {"keys": [("user_dataset_id", ASCENDING)], "options": {"unique": True}},
            # Filename index for searching
            {"keys": [("filename", TEXT)]},
            # Mode and format indexes for filtering
            {"keys": [("mode", ASCENDING)]},
            {"keys": [("format_type", ASCENDING)]},
            # Entity count index for filtering by size
            {"keys": [("entity_count", ASCENDING)]},
        ]
        
        for index in indexes:
            try:
                index_name = self._create_index(user_datasets_collection, index["keys"], index.get("options", {}))
                self.indexes_created.add(f"user_datasets.{index_name}")
            except Exception as e:
                logger.warning(f"Could not create user dataset index: {e}")
        
        # Dataset history collection indexes (for global history)
        history_collection = self.db["dataset_history"]
        
        indexes = [
            # Timestamp index for recent datasets
            {"keys": [("timestamp", DESCENDING)]},
            # Filename text search
            {"keys": [("filename", TEXT)]},
            # Mode and format indexes
            {"keys": [("mode", ASCENDING)]},
            {"keys": [("format", ASCENDING)]},
        ]
        
        for index in indexes:
            try:
                index_name = self._create_index(history_collection, index["keys"], index.get("options", {}))
                self.indexes_created.add(f"dataset_history.{index_name}")
            except Exception as e:
                logger.warning(f"Could not create history index: {e}")
    
    def create_community_indexes(self):
        """Create indexes for community datasets collections."""
        if not self.db:
            return
        
        # Community datasets collection indexes
        community_collection = self.db["community_datasets"]
        
        indexes = [
            # Timestamp index for recent datasets
            {"keys": [("timestamp", DESCENDING)]},
            # User name index for user's shared datasets
            {"keys": [("user_name", ASCENDING)]},
            # Likes index for popular datasets
            {"keys": [("likes", DESCENDING)]},
            # Download count index for popular datasets
            {"keys": [("download_count", DESCENDING)]},
            # Tags index for tag-based filtering
            {"keys": [("tags", ASCENDING)]},
            # Text search index for description and filename
            {"keys": [("description", TEXT), ("filename", TEXT)]},
            # Mode and format indexes
            {"keys": [("mode", ASCENDING)]},
            {"keys": [("format", ASCENDING)]},
            # Entity count index
            {"keys": [("entity_count", ASCENDING)]},
            # Compound index for user + timestamp
            {"keys": [("user_name", ASCENDING), ("timestamp", DESCENDING)]},
            # Compound index for tags + likes
            {"keys": [("tags", ASCENDING), ("likes", DESCENDING)]},
        ]
        
        for index in indexes:
            try:
                index_name = self._create_index(community_collection, index["keys"], index.get("options", {}))
                self.indexes_created.add(f"community_datasets.{index_name}")
            except Exception as e:
                logger.warning(f"Could not create community dataset index: {e}")
    
    def create_chat_indexes(self):
        """Create indexes for chat collections."""
        if not self.db:
            return
        
        # Dataset chat messages collection indexes
        chat_collection = self.db["dataset_chat_messages"]
        
        indexes = [
            # Dataset ID index for dataset-specific chats
            {"keys": [("dataset_id", ASCENDING)]},
            # Dataset ID + timestamp for chronological order
            {"keys": [("dataset_id", ASCENDING), ("timestamp", ASCENDING)]},
            # User name index for user's messages
            {"keys": [("user_name", ASCENDING)]},
            # Timestamp index for recent messages
            {"keys": [("timestamp", DESCENDING)]},
        ]
        
        for index in indexes:
            try:
                index_name = self._create_index(chat_collection, index["keys"], index.get("options", {}))
                self.indexes_created.add(f"dataset_chat_messages.{index_name}")
            except Exception as e:
                logger.warning(f"Could not create chat index: {e}")
        
        # Global chat messages collection indexes
        global_chat_collection = self.db["global_chat_messages"]
        
        indexes = [
            # Timestamp index for chronological order
            {"keys": [("timestamp", ASCENDING)]},
            # User name index for user's messages
            {"keys": [("user_name", ASCENDING)]},
            # Timestamp index for recent messages
            {"keys": [("timestamp", DESCENDING)]},
        ]
        
        for index in indexes:
            try:
                index_name = self._create_index(global_chat_collection, index["keys"], index.get("options", {}))
                self.indexes_created.add(f"global_chat_messages.{index_name}")
            except Exception as e:
                logger.warning(f"Could not create global chat index: {e}")
    
    def create_collection_indexes(self):
        """Create indexes for dataset collections."""
        if not self.db:
            return
        
        # Dataset collections collection indexes
        collections_collection = self.db["dataset_collections"]
        
        indexes = [
            # Created by index for user's collections
            {"keys": [("created_by", ASCENDING)]},
            # Created by + timestamp for user's recent collections
            {"keys": [("created_by", ASCENDING), ("timestamp", DESCENDING)]},
            # Public collections index
            {"keys": [("is_public", ASCENDING)]},
            # Timestamp index for recent collections
            {"keys": [("timestamp", DESCENDING)]},
            # Text search index for name and description
            {"keys": [("name", TEXT), ("description", TEXT)]},
            # Dataset count index
            {"keys": [("dataset_count", DESCENDING)]},
        ]
        
        for index in indexes:
            try:
                index_name = self._create_index(collections_collection, index["keys"], index.get("options", {}))
                self.indexes_created.add(f"dataset_collections.{index_name}")
            except Exception as e:
                logger.warning(f"Could not create collection index: {e}")
    
    def create_notification_indexes(self):
        """Create indexes for notifications collection."""
        if not self.db:
            return
        
        # Notifications collection indexes
        notifications_collection = self.db["notifications"]
        
        indexes = [
            # User name index for user's notifications
            {"keys": [("user_name", ASCENDING)]},
            # User name + is_read for unread notifications
            {"keys": [("user_name", ASCENDING), ("is_read", ASCENDING)]},
            # User name + timestamp for chronological order
            {"keys": [("user_name", ASCENDING), ("timestamp", DESCENDING)]},
            # Timestamp index for recent notifications
            {"keys": [("timestamp", DESCENDING)]},
            # Notification type index
            {"keys": [("type", ASCENDING)]},
        ]
        
        for index in indexes:
            try:
                index_name = self._create_index(notifications_collection, index["keys"], index.get("options", {}))
                self.indexes_created.add(f"notifications.{index_name}")
            except Exception as e:
                logger.warning(f"Could not create notification index: {e}")
    
    def create_api_key_indexes(self):
        """Create indexes for API keys collection."""
        if not self.db:
            return
        
        # API keys collection indexes
        api_keys_collection = self.db["api_keys"]
        
        indexes = [
            # API key hash index (unique)
            {"keys": [("key_hash", ASCENDING)], "options": {"unique": True}},
            # User name index for user's API keys
            {"keys": [("user_name", ASCENDING)]},
            # User name + created_at for user's recent keys
            {"keys": [("user_name", ASCENDING), ("created_at", DESCENDING)]},
            # Is active index for active keys
            {"keys": [("is_active", ASCENDING)]},
            # Created at index
            {"keys": [("created_at", DESCENDING)]},
        ]
        
        for index in indexes:
            try:
                index_name = self._create_index(api_keys_collection, index["keys"], index.get("options", {}))
                self.indexes_created.add(f"api_keys.{index_name}")
            except Exception as e:
                logger.warning(f"Could not create API key index: {e}")
    
    def _create_index(self, collection, keys: List, options: Dict = None) -> str:
        """Create an index and return its name."""
        try:
            options = options or {}
            index_name = collection.create_index(keys, **options)
            logger.debug(f"Created index: {index_name} on {collection.name}")
            return index_name
        except Exception as e:
            logger.error(f"Failed to create index {keys} on {collection.name}: {e}")
            raise
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about created indexes."""
        if not self.db:
            return {"error": "Database not available"}
        
        stats = {
            "total_indexes": len(self.indexes_created),
            "indexes_by_collection": {},
            "collection_stats": {}
        }
        
        # Group indexes by collection
        for index_name in self.indexes_created:
            collection_name = index_name.split('.')[0]
            if collection_name not in stats["indexes_by_collection"]:
                stats["indexes_by_collection"][collection_name] = []
            stats["indexes_by_collection"][collection_name].append(index_name)
        
        # Get collection statistics
        for collection_name in stats["indexes_by_collection"]:
            try:
                collection = self.db[collection_name]
                stats["collection_stats"][collection_name] = {
                    "document_count": collection.count_documents({}),
                    "index_count": len(list(collection.list_indexes())),
                    "size_bytes": collection.estimated_document_count() * 1024  # Rough estimate
                }
            except Exception as e:
                logger.warning(f"Could not get stats for collection {collection_name}: {e}")
                stats["collection_stats"][collection_name] = {"error": str(e)}
        
        return stats
    
    def analyze_query_performance(self, collection_name: str, query: Dict) -> Dict[str, Any]:
        """Analyze query performance using MongoDB's explain functionality."""
        if not self.db:
            return {"error": "Database not available"}
        
        try:
            collection = self.db[collection_name]
            explain_result = collection.find(query).explain()
            
            return {
                "collection": collection_name,
                "query": query,
                "execution_stats": explain_result.get("executionStats", {}),
                "winning_plan": explain_result.get("queryPlanner", {}).get("winningPlan", {}),
                "indexes_used": explain_result.get("queryPlanner", {}).get("winningPlan", {}).get("indexName"),
                "total_docs_examined": explain_result.get("executionStats", {}).get("totalDocsExamined", 0),
                "total_docs_returned": explain_result.get("executionStats", {}).get("totalDocsReturned", 0),
                "execution_time_ms": explain_result.get("executionStats", {}).get("executionTimeMillis", 0)
            }
        except Exception as e:
            return {"error": f"Could not analyze query: {e}"}
    
    def optimize_collection(self, collection_name: str) -> Dict[str, Any]:
        """Optimize a specific collection."""
        if not self.db:
            return {"error": "Database not available"}
        
        try:
            collection = self.db[collection_name]
            
            # Get collection stats
            stats = collection.aggregate([{"$collStats": {"storageStats": {}}}]).next()
            
            # Compact collection if needed
            if stats.get("storageStats", {}).get("fragmented", False):
                logger.info(f"Collection {collection_name} is fragmented, consider running compact")
            
            return {
                "collection": collection_name,
                "document_count": collection.count_documents({}),
                "index_count": len(list(collection.list_indexes())),
                "storage_size_bytes": stats.get("storageStats", {}).get("size", 0),
                "index_size_bytes": stats.get("storageStats", {}).get("totalIndexSize", 0),
                "is_fragmented": stats.get("storageStats", {}).get("fragmented", False),
                "recommendations": self._get_collection_recommendations(collection_name, stats)
            }
        except Exception as e:
            return {"error": f"Could not optimize collection {collection_name}: {e}"}
    
    def _get_collection_recommendations(self, collection_name: str, stats: Dict) -> List[str]:
        """Get optimization recommendations for a collection."""
        recommendations = []
        
        storage_stats = stats.get("storageStats", {})
        
        # Check for fragmentation
        if storage_stats.get("fragmented", False):
            recommendations.append("Consider running compact() to reduce fragmentation")
        
        # Check index size vs data size ratio
        data_size = storage_stats.get("size", 0)
        index_size = storage_stats.get("totalIndexSize", 0)
        
        if data_size > 0 and index_size / data_size > 0.5:
            recommendations.append("Index size is high relative to data size, consider reviewing indexes")
        
        # Check for unused indexes
        document_count = storage_stats.get("count", 0)
        if document_count < 1000:
            recommendations.append("Collection has few documents, consider if all indexes are necessary")
        
        return recommendations

def initialize_database_indexes(db):
    """Initialize all database indexes."""
    if not db:
        logger.warning("Database not available, skipping index creation")
        return
    
    optimizer = DatabaseOptimizer(db)
    optimizer.create_all_indexes()
    
    # Log index statistics
    stats = optimizer.get_index_stats()
    logger.info(f"Database optimization complete. Created {stats['total_indexes']} indexes")
    
    return optimizer
