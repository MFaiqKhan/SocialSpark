"""
Facebook Platform Posting Agent.

This agent is responsible for publishing content to Facebook.
"""

import os
import json
import logging
import base64
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.core.agent import BaseAgent
from src.core.models import Task, DataPart, Capability, TaskStatus
from src.core.utils import create_data_part, generate_id, extract_data_part_by_content_type
from src.core.storage import TaskStorage

from src.agents.platform_posting.facebook.api_client import FacebookApiClient


class FacebookPostingAgent(BaseAgent):
    """
    Facebook Platform Posting Agent.
    
    Handles publishing content to the Facebook platform.
    """
    
    def __init__(
        self,
        agent_id: str = "facebook-posting-agent",
        name: str = "Facebook Posting Agent",
        description: str = "Publishes content to Facebook",
        base_url: str = "http://localhost",
        port: int = 8002,
        connection_string: str = "mongodb://localhost:27017/",
        db_name: str = "socialspark_facebook_agent"
    ):
        """
        Initialize the Facebook Posting Agent.
        
        Args:
            agent_id: Unique identifier for this agent
            name: Human-readable name for this agent
            description: Detailed description of what this agent does
            base_url: Base URL for this agent's API
            port: Port for this agent's API
            connection_string: MongoDB connection string
            db_name: Database name for this agent
        """
        super().__init__(agent_id, name, description, "0.1.0", base_url, port)
        
        # Set up storage
        self.task_storage = TaskStorage(connection_string, db_name)
        
        # API client
        self.api_client = FacebookApiClient()
        
        # Register capabilities
        self._register_capabilities()
        
        # Register task handlers
        self._register_task_handlers()
    
    def _register_capabilities(self):
        """Register this agent's capabilities."""
        publish_post_capability = Capability(
            id="publish_post",
            name="Publish Post to Facebook",
            description="Publishes content to Facebook",
            parameters={
                "user_id": {"type": "string", "description": "User ID"},
                "platform_specific_content": {
                    "type": "object", 
                    "description": "Content specifically adapted for Facebook",
                    "properties": {
                        "text": {"type": "string", "description": "Text content"},
                        "image_reference": {"type": "string", "description": "Reference to image, if any"},
                        "hashtags": {"type": "array", "items": {"type": "string"}, "description": "Hashtags for this post"}
                    }
                },
                "facebook_token": {"type": "string", "description": "OAuth token for Facebook"},
                "socialspark_post_id": {"type": "string", "description": "SocialSpark internal post ID"}
            }
        )
        
        fetch_analytics_capability = Capability(
            id="fetch_platform_analytics",
            name="Fetch Facebook Analytics",
            description="Retrieves engagement analytics for a Facebook post",
            parameters={
                "platform_post_id": {"type": "string", "description": "Facebook post ID"},
                "facebook_token": {"type": "string", "description": "OAuth token for Facebook"}
            }
        )
        
        self.add_capability(publish_post_capability)
        self.add_capability(fetch_analytics_capability)
    
    def _register_task_handlers(self):
        """Register handlers for different task types."""
        self.register_task_handler("publish_post", self._handle_publish_post)
        self.register_task_handler("fetch_platform_analytics", self._handle_fetch_analytics)
        
    async def _handle_publish_post(self, task: Task) -> None:
        """
        Handle a publish post task.
        
        Args:
            task: The task to process
        """
        try:
            # Extract data parts
            data_part = extract_data_part_by_content_type(task.data_parts, "application/json")
            if not data_part:
                raise ValueError("No content data found in task")
                
            data = data_part.data
            user_id = data.get("user_id")
            content = data.get("platform_specific_content", {})
            facebook_token = data.get("facebook_token")
            socialspark_post_id = data.get("socialspark_post_id")
            facebook_page_id = data.get("facebook_page_id", "me")  # Default to user timeline if no page specified
            
            # Validate required fields
            if not user_id:
                raise ValueError("user_id is required")
            if not content:
                raise ValueError("platform_specific_content is required")
            if not facebook_token:
                raise ValueError("facebook_token is required")
            if not socialspark_post_id:
                raise ValueError("socialspark_post_id is required")
                
            # Extract content details
            text = content.get("text")
            image_reference = content.get("image_reference")
            
            if not text and not image_reference:
                raise ValueError("Post must have text and/or image")
                
            # Publish to Facebook
            response = await self.api_client.publish_post(
                access_token=facebook_token,
                message=text,
                image_path=image_reference,
                page_id=facebook_page_id
            )
            
            # Send status update back to Content & Scheduler agent
            if response.get("success"):
                facebook_post_id = response.get("post_id")
                
                await self._send_post_status_update(
                    socialspark_post_id=socialspark_post_id,
                    status="success",
                    platform_post_id=facebook_post_id
                )
                
                await self._send_published_post_report(
                    socialspark_post_id=socialspark_post_id,
                    user_id=user_id,
                    platform_post_id=facebook_post_id
                )
                
                # Update task metadata
                if not task.metadata:
                    task.metadata = {}
                task.metadata["facebook_post_id"] = facebook_post_id
                
                self.logger.info(f"Successfully published post {socialspark_post_id} to Facebook")
            else:
                error_message = response.get("error", "Unknown error")
                
                await self._send_post_status_update(
                    socialspark_post_id=socialspark_post_id,
                    status="failure",
                    error_message=error_message
                )
                
                # Update task metadata
                if not task.metadata:
                    task.metadata = {}
                task.metadata["error"] = error_message
                
                self.logger.error(f"Failed to publish post {socialspark_post_id} to Facebook: {error_message}")
                
            # Save task
            self.task_storage.save_task(task)
            
        except Exception as e:
            self.logger.error(f"Error processing publish task {task.id}: {str(e)}")
            if not task.metadata:
                task.metadata = {}
            task.metadata["error"] = str(e)
            task.update_status(TaskStatus.FAILED)
            
            # Try to send status update on error
            try:
                socialspark_post_id = data_part.data.get("socialspark_post_id") if data_part else None
                if socialspark_post_id:
                    await self._send_post_status_update(
                        socialspark_post_id=socialspark_post_id,
                        status="failure",
                        error_message=str(e)
                    )
            except Exception as status_error:
                self.logger.error(f"Failed to send status update: {str(status_error)}")
    
    async def _send_post_status_update(
        self, 
        socialspark_post_id: str, 
        status: str, 
        platform_post_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Send a post status update to the Content & Scheduler Agent.
        
        Args:
            socialspark_post_id: SocialSpark post ID
            status: Status of the post (success or failure)
            platform_post_id: Facebook post ID if successful
            error_message: Error message if failed
        """
        data = {
            "socialspark_post_id": socialspark_post_id,
            "platform": "facebook",
            "status": status
        }
        
        if platform_post_id:
            data["platform_post_id"] = platform_post_id
            
        if error_message:
            data["error_message"] = error_message
            
        data_parts = [
            {
                "id": generate_id(),
                "content_type": "application/json",
                "data": data
            }
        ]
        
        await self.send_task(
            target_agent_id="content-scheduler-agent",
            task_type="post_status_update",
            data_parts=data_parts
        )
    
    async def _send_published_post_report(
        self,
        socialspark_post_id: str,
        user_id: str,
        platform_post_id: str
    ) -> None:
        """
        Send a published post report to the Analytics Agent.
        
        Args:
            socialspark_post_id: SocialSpark post ID
            user_id: User ID
            platform_post_id: Facebook post ID
        """
        data = {
            "socialspark_post_id": socialspark_post_id,
            "user_id": user_id,
            "platform": "facebook",
            "platform_post_id": platform_post_id,
            "publish_time": datetime.now().isoformat()
        }
        
        data_parts = [
            {
                "id": generate_id(),
                "content_type": "application/json",
                "data": data
            }
        ]
        
        await self.send_task(
            target_agent_id="analytics-agent",
            task_type="report_published_post",
            data_parts=data_parts
        )
    
    async def _handle_fetch_analytics(self, task: Task) -> None:
        """
        Handle a fetch analytics task.
        
        Args:
            task: The task to process
        """
        try:
            # Extract data parts
            data_part = extract_data_part_by_content_type(task.data_parts, "application/json")
            if not data_part:
                raise ValueError("No content data found in task")
                
            data = data_part.data
            platform_post_id = data.get("platform_post_id")
            facebook_token = data.get("facebook_token")
            
            # Validate required fields
            if not platform_post_id:
                raise ValueError("platform_post_id is required")
            if not facebook_token:
                raise ValueError("facebook_token is required")
                
            # Fetch analytics from Facebook
            analytics = await self.api_client.get_post_analytics(
                access_token=facebook_token,
                post_id=platform_post_id
            )
            
            # Update task with analytics data
            if not task.metadata:
                task.metadata = {}
            task.metadata["analytics"] = analytics
            
            # Create response data part
            response_data = {
                "platform": "facebook",
                "platform_post_id": platform_post_id,
                "analytics": analytics
            }
            
            response_data_part = create_data_part(
                data=response_data,
                content_type="application/json"
            )
            
            task.add_data_part(response_data_part)
            
            # Save task
            self.task_storage.save_task(task)
            
            self.logger.info(f"Successfully fetched analytics for Facebook post {platform_post_id}")
            
        except Exception as e:
            self.logger.error(f"Error fetching analytics for task {task.id}: {str(e)}")
            if not task.metadata:
                task.metadata = {}
            task.metadata["error"] = str(e)
            task.update_status(TaskStatus.FAILED) 