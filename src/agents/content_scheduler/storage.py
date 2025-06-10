"""
Post Storage for Content & Scheduling Agent.

This module provides persistence for scheduled posts.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.core.storage import MongoStorage
from src.agents.content_scheduler.models import ScheduledPost, PostStatus, PlatformSpecificContent


class PostStorage(MongoStorage):
    """
    Storage for scheduled posts.
    
    Provides persistence for scheduled posts across agent restarts.
    """
    
    def __init__(self, connection_string: str, db_name: str = "socialspark"):
        """
        Initialize post storage.
        
        Args:
            connection_string: MongoDB connection string
            db_name: Database name
        """
        super().__init__(connection_string, db_name)
        self.collection = self.db["posts"]
        self.async_collection = self.async_db["posts"]
        
    def _post_to_dict(self, post: ScheduledPost) -> Dict[str, Any]:
        """
        Convert a ScheduledPost to a dictionary for MongoDB storage.
        
        Args:
            post: Post to convert
            
        Returns:
            Dictionary representation of the post
        """
        post_dict = post.dict()
        
        # Convert datetime objects to strings
        post_dict["schedule_time"] = post.schedule_time.isoformat()
        post_dict["created_at"] = post.created_at.isoformat()
        post_dict["updated_at"] = post.updated_at.isoformat()
        
        # Convert enum values to strings
        post_dict["content_type"] = post.content_type.value
        post_dict["status"] = post.status.value
        
        # Convert platform specific content to a serializable format
        platform_specific_content = {}
        for platform, content in post.platform_specific_content.items():
            platform_specific_content[platform] = content.dict()
        post_dict["platform_specific_content"] = platform_specific_content
        
        # Use post.id as MongoDB _id
        post_dict["_id"] = post.id
        
        return post_dict
    
    def _dict_to_post(self, post_dict: Dict[str, Any]) -> ScheduledPost:
        """
        Convert a dictionary from MongoDB to a ScheduledPost.
        
        Args:
            post_dict: Dictionary to convert
            
        Returns:
            ScheduledPost object
        """
        # Remove MongoDB _id field
        if "_id" in post_dict:
            post_dict["id"] = post_dict.pop("_id")
        
        # Convert string dates to datetime objects
        if isinstance(post_dict.get("schedule_time"), str):
            post_dict["schedule_time"] = datetime.fromisoformat(post_dict["schedule_time"])
        if isinstance(post_dict.get("created_at"), str):
            post_dict["created_at"] = datetime.fromisoformat(post_dict["created_at"])
        if isinstance(post_dict.get("updated_at"), str):
            post_dict["updated_at"] = datetime.fromisoformat(post_dict["updated_at"])
        
        # Convert platform specific content
        platform_specific_content = {}
        for platform, content_dict in post_dict.get("platform_specific_content", {}).items():
            platform_specific_content[platform] = PlatformSpecificContent(**content_dict)
        post_dict["platform_specific_content"] = platform_specific_content
        
        # Convert string status to enum
        if isinstance(post_dict.get("status"), str):
            post_dict["status"] = PostStatus(post_dict["status"])
            
        # Convert string content type to enum
        if isinstance(post_dict.get("content_type"), str):
            from src.agents.content_scheduler.models import ContentType
            post_dict["content_type"] = ContentType(post_dict["content_type"])
        
        return ScheduledPost(**post_dict)
    
    def save_post(self, post: ScheduledPost) -> bool:
        """
        Save a post to the database.
        
        Args:
            post: Post to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            post_dict = self._post_to_dict(post)
            result = self.collection.replace_one({"_id": post.id}, post_dict, upsert=True)
            return True
        except Exception as e:
            self.logger.error(f"Error saving post {post.id}: {e}")
            return False
    
    async def save_post_async(self, post: ScheduledPost) -> bool:
        """
        Save a post to the database asynchronously.
        
        Args:
            post: Post to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            post_dict = self._post_to_dict(post)
            result = await self.async_collection.replace_one({"_id": post.id}, post_dict, upsert=True)
            return True
        except Exception as e:
            self.logger.error(f"Error saving post {post.id} asynchronously: {e}")
            return False
    
    def get_post(self, post_id: str) -> Optional[ScheduledPost]:
        """
        Get a post by ID.
        
        Args:
            post_id: ID of the post to retrieve
            
        Returns:
            ScheduledPost if found, None otherwise
        """
        try:
            post_dict = self.collection.find_one({"_id": post_id})
            if not post_dict:
                return None
            return self._dict_to_post(post_dict)
        except Exception as e:
            self.logger.error(f"Error getting post {post_id}: {e}")
            return None
    
    async def get_post_async(self, post_id: str) -> Optional[ScheduledPost]:
        """
        Get a post by ID asynchronously.
        
        Args:
            post_id: ID of the post to retrieve
            
        Returns:
            ScheduledPost if found, None otherwise
        """
        try:
            post_dict = await self.async_collection.find_one({"_id": post_id})
            if not post_dict:
                return None
            return self._dict_to_post(post_dict)
        except Exception as e:
            self.logger.error(f"Error getting post {post_id} asynchronously: {e}")
            return None
    
    def get_posts_by_status(
        self, status: PostStatus, limit: int = 100
    ) -> List[ScheduledPost]:
        """
        Get posts by status.
        
        Args:
            status: Status to filter by
            limit: Maximum number of posts to retrieve
            
        Returns:
            List of scheduled posts
        """
        try:
            posts = []
            cursor = self.collection.find({"status": status.value}).sort("schedule_time", 1).limit(limit)
            for post_dict in cursor:
                posts.append(self._dict_to_post(post_dict))
            return posts
        except Exception as e:
            self.logger.error(f"Error getting posts by status {status}: {e}")
            return []
    
    async def get_posts_by_status_async(
        self, status: PostStatus, limit: int = 100
    ) -> List[ScheduledPost]:
        """
        Get posts by status asynchronously.
        
        Args:
            status: Status to filter by
            limit: Maximum number of posts to retrieve
            
        Returns:
            List of scheduled posts
        """
        try:
            posts = []
            cursor = self.async_collection.find({"status": status.value}).sort("schedule_time", 1).limit(limit)
            async for post_dict in cursor:
                posts.append(self._dict_to_post(post_dict))
            return posts
        except Exception as e:
            self.logger.error(f"Error getting posts by status {status} asynchronously: {e}")
            return []
    
    def get_posts_by_user(
        self, user_id: str, limit: int = 100
    ) -> List[ScheduledPost]:
        """
        Get posts by user.
        
        Args:
            user_id: User ID to filter by
            limit: Maximum number of posts to retrieve
            
        Returns:
            List of scheduled posts
        """
        try:
            posts = []
            cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
            for post_dict in cursor:
                posts.append(self._dict_to_post(post_dict))
            return posts
        except Exception as e:
            self.logger.error(f"Error getting posts by user {user_id}: {e}")
            return []
    
    async def get_posts_by_user_async(
        self, user_id: str, limit: int = 100
    ) -> List[ScheduledPost]:
        """
        Get posts by user asynchronously.
        
        Args:
            user_id: User ID to filter by
            limit: Maximum number of posts to retrieve
            
        Returns:
            List of scheduled posts
        """
        try:
            posts = []
            cursor = self.async_collection.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
            async for post_dict in cursor:
                posts.append(self._dict_to_post(post_dict))
            return posts
        except Exception as e:
            self.logger.error(f"Error getting posts by user {user_id} asynchronously: {e}")
            return []
    
    def delete_post(self, post_id: str) -> bool:
        """
        Delete a post from storage.
        
        Args:
            post_id: ID of the post to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.collection.delete_one({"_id": post_id})
            return result.deleted_count > 0
        except Exception as e:
            self.logger.error(f"Error deleting post {post_id}: {e}")
            return False
    
    async def delete_post_async(self, post_id: str) -> bool:
        """
        Delete a post from storage asynchronously.
        
        Args:
            post_id: ID of the post to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = await self.async_collection.delete_one({"_id": post_id})
            return result.deleted_count > 0
        except Exception as e:
            self.logger.error(f"Error deleting post {post_id} asynchronously: {e}")
            return False 