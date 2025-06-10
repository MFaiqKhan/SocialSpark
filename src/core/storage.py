"""
Storage utilities for SocialSpark Orchestrator.

This module provides storage classes for persisting tasks and other data.
"""

import logging
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

import motor.motor_asyncio
from pymongo import MongoClient
from bson.objectid import ObjectId

from src.core.models import Task, TaskStatus, DataPart


class MongoStorage:
    """Base class for MongoDB storage."""
    
    def __init__(self, connection_string: str, db_name: str = "socialspark"):
        """
        Initialize MongoDB storage.
        
        Args:
            connection_string: MongoDB connection string
            db_name: Database name
        """
        # Create sync client for non-async operations
        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]
        
        # Create async client for async operations
        self.async_client = motor.motor_asyncio.AsyncIOMotorClient(connection_string)
        self.async_db = self.async_client[db_name]
        
        self.logger = logging.getLogger(f"socialspark.storage.{self.__class__.__name__}")


class TaskStorage(MongoStorage):
    """Storage for A2A tasks."""
    
    def __init__(self, connection_string: str, db_name: str = "socialspark"):
        """
        Initialize task storage.
        
        Args:
            connection_string: MongoDB connection string
            db_name: Database name
        """
        super().__init__(connection_string, db_name)
        self.collection = self.db["tasks"]
        self.async_collection = self.async_db["tasks"]
    
    def _task_to_dict(self, task: Task) -> Dict[str, Any]:
        """
        Convert a Task to a dictionary for MongoDB storage.
        
        Args:
            task: Task to convert
            
        Returns:
            Dictionary representation of the task
        """
        task_dict = task.dict()
        
        # Convert datetime objects to strings
        task_dict["created_at"] = task.created_at.isoformat()
        task_dict["updated_at"] = task.updated_at.isoformat()
        
        # Use task.id as MongoDB _id
        task_dict["_id"] = task.id
        
        return task_dict
    
    def _dict_to_task(self, task_dict: Dict[str, Any]) -> Task:
        """
        Convert a dictionary from MongoDB to a Task.
        
        Args:
            task_dict: Dictionary to convert
            
        Returns:
            Task object
        """
        # Remove MongoDB _id field
        if "_id" in task_dict:
            task_dict["id"] = task_dict.pop("_id")
        
        # Convert string dates to datetime objects
        if isinstance(task_dict.get("created_at"), str):
            task_dict["created_at"] = datetime.fromisoformat(task_dict["created_at"])
        if isinstance(task_dict.get("updated_at"), str):
            task_dict["updated_at"] = datetime.fromisoformat(task_dict["updated_at"])
        
        # Convert data_parts dictionaries to DataPart objects
        data_parts = []
        for dp_dict in task_dict.get("data_parts", []):
            data_parts.append(DataPart(**dp_dict))
        task_dict["data_parts"] = data_parts
        
        # Convert status string to TaskStatus enum
        if isinstance(task_dict.get("status"), str):
            task_dict["status"] = TaskStatus(task_dict["status"])
        
        return Task(**task_dict)
    
    def save_task(self, task: Task) -> bool:
        """
        Save a task to the database.
        
        Args:
            task: Task to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            task_dict = self._task_to_dict(task)
            result = self.collection.replace_one({"_id": task.id}, task_dict, upsert=True)
            return True
        except Exception as e:
            self.logger.error(f"Error saving task {task.id}: {e}")
            return False
    
    async def save_task_async(self, task: Task) -> bool:
        """
        Save a task to the database asynchronously.
        
        Args:
            task: Task to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            task_dict = self._task_to_dict(task)
            result = await self.async_collection.replace_one({"_id": task.id}, task_dict, upsert=True)
            return True
        except Exception as e:
            self.logger.error(f"Error saving task {task.id} asynchronously: {e}")
            return False
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get a task from the database.
        
        Args:
            task_id: ID of the task to get
            
        Returns:
            Task if found, None otherwise
        """
        try:
            task_dict = self.collection.find_one({"_id": task_id})
            if not task_dict:
                return None
            return self._dict_to_task(task_dict)
        except Exception as e:
            self.logger.error(f"Error getting task {task_id}: {e}")
            return None
    
    async def get_task_async(self, task_id: str) -> Optional[Task]:
        """
        Get a task from the database asynchronously.
        
        Args:
            task_id: ID of the task to get
            
        Returns:
            Task if found, None otherwise
        """
        try:
            task_dict = await self.async_collection.find_one({"_id": task_id})
            if not task_dict:
                return None
            return self._dict_to_task(task_dict)
        except Exception as e:
            self.logger.error(f"Error getting task {task_id} asynchronously: {e}")
            return None
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """
        Get all tasks with a specific status.
        
        Args:
            status: Status to filter by
            
        Returns:
            List of tasks with the specified status
        """
        try:
            tasks = []
            cursor = self.collection.find({"status": status.value})
            for task_dict in cursor:
                tasks.append(self._dict_to_task(task_dict))
            return tasks
        except Exception as e:
            self.logger.error(f"Error getting tasks by status {status}: {e}")
            return []
    
    async def get_tasks_by_status_async(self, status: TaskStatus) -> List[Task]:
        """
        Get all tasks with a specific status asynchronously.
        
        Args:
            status: Status to filter by
            
        Returns:
            List of tasks with the specified status
        """
        try:
            tasks = []
            cursor = self.async_collection.find({"status": status.value})
            async for task_dict in cursor:
                tasks.append(self._dict_to_task(task_dict))
            return tasks
        except Exception as e:
            self.logger.error(f"Error getting tasks by status {status} asynchronously: {e}")
            return []
    
    def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """
        Update the status of a task.
        
        Args:
            task_id: ID of the task to update
            status: New status
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.collection.update_one(
                {"_id": task_id},
                {"$set": {"status": status.value, "updated_at": datetime.now().isoformat()}}
            )
            return result.modified_count > 0
        except Exception as e:
            self.logger.error(f"Error updating task {task_id} status to {status}: {e}")
            return False
    
    async def update_task_status_async(self, task_id: str, status: TaskStatus) -> bool:
        """
        Update the status of a task asynchronously.
        
        Args:
            task_id: ID of the task to update
            status: New status
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = await self.async_collection.update_one(
                {"_id": task_id},
                {"$set": {"status": status.value, "updated_at": datetime.now().isoformat()}}
            )
            return result.modified_count > 0
        except Exception as e:
            self.logger.error(f"Error updating task {task_id} status to {status} asynchronously: {e}")
            return False 