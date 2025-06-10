"""
A2A Protocol Client for SocialSpark Orchestrator.

This module provides a client for agents to communicate with each other
using the Agent2Agent (A2A) protocol.
"""

import uuid
import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

import httpx

from src.core.models import AgentCard, Task, DataPart, TaskStatus


class A2AClient:
    """
    Client for A2A protocol communication.
    
    Used by agents to send tasks to other agents and retrieve task status.
    """
    
    def __init__(self, agent_id: str, base_url: str = "http://localhost:8000"):
        """
        Initialize an A2A client.
        
        Args:
            agent_id: ID of the agent using this client
            base_url: Base URL for A2A service, defaults to localhost:8000
        """
        self.agent_id = agent_id
        self.base_url = base_url
        self.logger = logging.getLogger(f"a2a.client.{agent_id}")
    
    async def discover_agent(self, agent_id: str) -> Optional[AgentCard]:
        """
        Discover an agent by its ID and retrieve its AgentCard.
        
        Args:
            agent_id: ID of the agent to discover
            
        Returns:
            AgentCard if found, None otherwise
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/agents/{agent_id}/card")
                if response.status_code == 200:
                    return AgentCard.model_validate(response.json())
                self.logger.warning(f"Failed to discover agent {agent_id}: {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"Error discovering agent {agent_id}: {e}")
            return None
    
    async def create_task(
        self, 
        target_agent_id: str, 
        task_type: str, 
        data_parts: List[Dict[str, Any]] = None,
        parent_task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Task]:
        """
        Create a new task to be sent to another agent.
        
        Args:
            target_agent_id: ID of the agent that should perform the task
            task_type: Type of task to be performed
            data_parts: Optional list of data parts to include
            parent_task_id: Optional ID of parent task if this is a subtask
            metadata: Optional additional metadata
            
        Returns:
            The created Task if successful, None otherwise
        """
        task_id = str(uuid.uuid4())
        now = datetime.now()
        
        task = Task(
            id=task_id,
            type=task_type,
            status=TaskStatus.PENDING,
            created_at=now,
            updated_at=now,
            source_agent_id=self.agent_id,
            target_agent_id=target_agent_id,
            parent_task_id=parent_task_id,
            metadata=metadata,
            data_parts=[]
        )
        
        # Add data parts if provided
        if data_parts:
            for dp_data in data_parts:
                dp_id = dp_data.get("id", str(uuid.uuid4()))
                content_type = dp_data.get("content_type", "application/json")
                data = dp_data.get("data", {})
                dp_metadata = dp_data.get("metadata")
                
                data_part = DataPart(
                    id=dp_id,
                    content_type=content_type,
                    data=data,
                    metadata=dp_metadata
                )
                task.add_data_part(data_part)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/agents/{target_agent_id}/tasks",
                    json=task.model_dump(),
                )
                if response.status_code == 201:
                    return Task.model_validate(response.json())
                self.logger.warning(f"Failed to create task: {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"Error creating task: {e}")
            return None
    
    async def get_task_status(self, target_agent_id: str, task_id: str) -> Optional[Task]:
        """
        Get the current status of a task.
        
        Args:
            target_agent_id: ID of the agent handling the task
            task_id: ID of the task to check
            
        Returns:
            Updated Task if found, None otherwise
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/agents/{target_agent_id}/tasks/{task_id}"
                )
                if response.status_code == 200:
                    return Task.model_validate(response.json())
                self.logger.warning(f"Failed to get task status: {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"Error getting task status: {e}")
            return None
    
    async def update_task_status(
        self, task_id: str, status: TaskStatus, metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Task]:
        """
        Update the status of a task this agent is handling.
        
        Args:
            task_id: ID of the task to update
            status: New status to set
            metadata: Optional additional metadata to update
            
        Returns:
            Updated Task if successful, None otherwise
        """
        try:
            update_data = {"status": status}
            if metadata:
                update_data["metadata"] = metadata
                
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.base_url}/agents/{self.agent_id}/tasks/{task_id}",
                    json=update_data,
                )
                if response.status_code == 200:
                    return Task.model_validate(response.json())
                self.logger.warning(f"Failed to update task status: {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"Error updating task status: {e}")
            return None 