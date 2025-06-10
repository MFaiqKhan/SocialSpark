"""
Content & Scheduling Agent Implementation.

This agent is responsible for processing content, adapting it for different
platforms, and scheduling it for publication.
"""

import os
import json
import uuid
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import asyncio
from functools import partial

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.mongodb import MongoDBJobStore
from pymongo import MongoClient

from src.core.agent import BaseAgent
from src.core.models import Task, DataPart, Capability, TaskStatus
from src.core.utils import create_data_part, generate_id, extract_data_part_by_content_type
from src.core.storage import TaskStorage

from src.agents.content_scheduler.models import (
    ContentType, PostStatus, SocialPlatform, 
    PlatformSpecificContent, ScheduledPost, ContentAdaptationRules
)
from src.agents.content_scheduler.storage import PostStorage
from src.agents.content_scheduler.adapters import adapt_content_for_platform


class ContentSchedulerAgent(BaseAgent):
    """
    Content & Scheduling Agent.
    
    Handles content processing, adaptation, and scheduling.
    """
    
    def __init__(
        self,
        agent_id: str = "content-scheduler-agent",
        name: str = "Content & Scheduling Agent",
        description: str = "Processes, adapts, and schedules social media content",
        base_url: str = "http://localhost",
        port: int = 8001,
        connection_string: str = "mongodb://localhost:27017/",
        db_name: str = "socialspark",
        media_storage_path: str = "./media"
    ):
        """
        Initialize the Content & Scheduling Agent.
        
        Args:
            agent_id: Unique identifier for this agent
            name: Human-readable name for this agent
            description: Detailed description of what this agent does
            base_url: Base URL for this agent's API
            port: Port for this agent's API
            connection_string: MongoDB connection string
            db_name: Database name
            media_storage_path: Path to store media files
        """
        super().__init__(agent_id, name, description, "0.1.0", base_url, port)
        
        # Set up storage
        self.task_storage = TaskStorage(connection_string, db_name)
        self.post_storage = PostStorage(connection_string, db_name)
        self.media_storage_path = media_storage_path
        
        # Ensure media directory exists
        os.makedirs(self.media_storage_path, exist_ok=True)
        
        # Set up scheduler with MongoDB job store
        mongo_client = MongoClient(connection_string)
        jobstore = MongoDBJobStore(
            database=db_name, 
            collection='scheduler_jobs', 
            client=mongo_client,
            create_index=False
        )
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_jobstore(jobstore)
        
        # Platform-specific content adaptation rules
        self.adaptation_rules = {
            SocialPlatform.TWITTER: ContentAdaptationRules(
                platform=SocialPlatform.TWITTER,
                max_text_length=280,
                hashtag_format="#{}",
                image_requirements={"max_images": 4}
            ),
            SocialPlatform.FACEBOOK: ContentAdaptationRules(
                platform=SocialPlatform.FACEBOOK,
                max_text_length=5000,
                hashtag_format="#{}",
                image_requirements={}
            ),
            SocialPlatform.INSTAGRAM: ContentAdaptationRules(
                platform=SocialPlatform.INSTAGRAM,
                max_text_length=2200,
                hashtag_format="#{}",
                image_requirements={"required": True}
            ),
            SocialPlatform.LINKEDIN: ContentAdaptationRules(
                platform=SocialPlatform.LINKEDIN,
                max_text_length=3000,
                hashtag_format="#{}",
                image_requirements={}
            )
        }
        
        # Register capabilities
        self._register_capabilities()
        
        # Register task handlers
        self._register_task_handlers()
        
    def _register_capabilities(self):
        """Register this agent's capabilities."""
        process_schedule_capability = Capability(
            id="process_and_schedule_post",
            name="Process and Schedule Post",
            description="Process social media content and schedule it for publication on multiple platforms",
            parameters={
                "user_id": {"type": "string", "description": "User ID"},
                "raw_text": {"type": "string", "description": "Raw text content"},
                "image_data": {"type": "string", "description": "Optional base64-encoded image"},
                "target_platforms": {"type": "array", "items": {"type": "string"}, "description": "Platforms to publish to"},
                "schedule_time": {"type": "string", "description": "When to publish this post"},
                "social_media_credentials": {"type": "object", "description": "Social media credentials"}
            }
        )
        
        post_status_update_capability = Capability(
            id="post_status_update",
            name="Post Status Update",
            description="Handle updates on the status of posts published to social platforms",
            parameters={
                "socialspark_post_id": {"type": "string", "description": "SocialSpark post ID"},
                "platform": {"type": "string", "description": "Social media platform"},
                "status": {"type": "string", "description": "Post status"},
                "platform_post_id": {"type": "string", "description": "Platform-specific post ID"},
                "error_message": {"type": "string", "description": "Error message if any"}
            }
        )
        
        self.add_capability(process_schedule_capability)
        self.add_capability(post_status_update_capability)
    
    def _register_task_handlers(self):
        """Register handlers for different task types."""
        self.register_task_handler("process_and_schedule_post", self._handle_process_schedule_post)
        self.register_task_handler("post_status_update", self._handle_post_status_update)
    
    async def _handle_process_schedule_post(self, task: Task) -> None:
        """
        Handle a process and schedule post task.
        
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
            raw_text = data.get("raw_text")
            image_data = data.get("image_data")
            target_platforms = data.get("target_platforms", [])
            schedule_time_str = data.get("schedule_time")
            credentials = data.get("social_media_credentials", {})
            
            # Validate required fields
            if not user_id:
                raise ValueError("user_id is required")
            if not raw_text:
                raise ValueError("raw_text is required")
            if not target_platforms:
                raise ValueError("target_platforms is required")
            if not schedule_time_str:
                raise ValueError("schedule_time is required")
                
            # Parse target platforms
            platform_list = []
            for platform_str in target_platforms:
                try:
                    platform = SocialPlatform(platform_str.lower())
                    platform_list.append(platform)
                except ValueError:
                    self.logger.warning(f"Unsupported platform: {platform_str}")
            
            if not platform_list:
                raise ValueError("No valid target platforms specified")
                
            # Parse schedule time
            try:
                schedule_time = datetime.fromisoformat(schedule_time_str.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError(f"Invalid schedule time format: {schedule_time_str}")
                
            # Generate post ID
            post_id = generate_id()
            
            # Determine content type and save image if present
            content_type = ContentType.TEXT
            image_reference = None
            if image_data:
                content_type = ContentType.IMAGE
                image_path = os.path.join(self.media_storage_path, f"{post_id}.jpg")
                
                # Base64 decode and save image
                from src.core.utils import decode_image
                if decode_image(image_data, image_path):
                    image_reference = image_path
                else:
                    self.logger.error(f"Failed to save image for post {post_id}")
            
            # Create scheduled post
            post = ScheduledPost(
                id=post_id,
                user_id=user_id,
                raw_text=raw_text,
                content_type=content_type,
                image_reference=image_reference,
                target_platforms=[p.value for p in platform_list],
                schedule_time=schedule_time,
                status=PostStatus.SCHEDULED
            )
            
            # Store credentials if provided
            if credentials:
                post.credentials = credentials
            
            # Process and adapt content for each target platform
            for platform in platform_list:
                rules = self.adaptation_rules.get(platform)
                if not rules:
                    self.logger.warning(f"No adaptation rules for platform {platform.value}")
                    continue
                    
                # Adapt content
                adapted_content = adapt_content_for_platform(
                    raw_text=raw_text,
                    image_reference=image_reference,
                    platform=platform,
                    rules=rules
                )
                
                # Store adapted content
                post.platform_specific_content[platform.value] = adapted_content
            
            # Save post
            if not self.post_storage.save_post(post):
                raise ValueError(f"Failed to save post {post_id}")
                
            # Schedule publication
            self._schedule_post_publication(post)
            
            # Save task status
            self.task_storage.save_task(task)
            
            self.logger.info(f"Successfully processed and scheduled post {post_id}")
            
            # Update task metadata
            if not task.metadata:
                task.metadata = {}
            task.metadata["post_id"] = post_id
            task.metadata["schedule_time"] = schedule_time.isoformat()
            
        except Exception as e:
            self.logger.error(f"Error processing task {task.id}: {str(e)}")
            if not task.metadata:
                task.metadata = {}
            task.metadata["error"] = str(e)
            task.update_status(TaskStatus.FAILED)
            
    def _schedule_post_publication(self, post: ScheduledPost) -> None:
        """
        Schedule a post for publication.
        
        Args:
            post: The post to schedule
        """
        job_id = f"publish_post_{post.id}"
        
        # This is a special function that can be called from a background thread
        # but will execute the async _publish_post in the FastAPI event loop
        def publish_post_wrapper(post_id):
            # Store this post_id for async processing when FastAPI is running
            if not hasattr(self, '_publish_queue'):
                self._publish_queue = []
            self._publish_queue.append(post_id)
            self.logger.info(f"Queued post {post_id} for publication (will be processed when FastAPI is running)")
        
        # Schedule the job with the wrapper function
        self.scheduler.add_job(
            publish_post_wrapper,
            'date',
            run_date=post.schedule_time,
            args=[post.id],
            id=job_id,
            replace_existing=True
        )
        
        self.logger.info(f"Scheduled post {post.id} for publication at {post.schedule_time}")
        
    async def _publish_post(self, post_id: str) -> None:
        """
        Publish a post to all target platforms.
        
        Args:
            post_id: ID of the post to publish
        """
        # Load post
        post = self.post_storage.get_post(post_id)
        if not post:
            self.logger.error(f"Post {post_id} not found for publication")
            return
            
        # Update status
        post.status = PostStatus.PUBLISHED
        post.updated_at = datetime.now()
        self.post_storage.save_post(post)
        
        # Publish to each platform
        for platform in post.target_platforms:
            platform_enum = SocialPlatform(platform)
            platform_content = post.platform_specific_content.get(platform)
            
            if not platform_content:
                self.logger.warning(f"No content for platform {platform} in post {post_id}")
                continue
                
            # Determine target agent ID
            target_agent_id = f"{platform.lower()}-posting-agent"
            
            # Prepare data part
            data = {
                "user_id": post.user_id,
                "platform_specific_content": {
                    "text": platform_content.text,
                    "image_reference": platform_content.image_reference,
                    "hashtags": platform_content.hashtags,
                    "metadata": platform_content.metadata
                },
                f"{platform.lower()}_token": "PLACEHOLDER_TOKEN",  # This would come from credentials storage
                "socialspark_post_id": post_id
            }
            
            # Add platform-specific credentials
            if platform.lower() == "facebook" and hasattr(post, "credentials") and post.credentials:
                # Extract Facebook-specific credentials if available
                fb_credentials = post.credentials.get("facebook", {})
                if fb_credentials.get("page_id"):
                    data["facebook_page_id"] = fb_credentials.get("page_id")
            
            data_parts = [
                {
                    "id": generate_id(),
                    "content_type": "application/json",
                    "data": data
                }
            ]
            
            # Send task to platform posting agent
            try:
                await self.send_task(
                    target_agent_id=target_agent_id,
                    task_type="publish_post",
                    data_parts=data_parts
                )
                self.logger.info(f"Sent publish task for post {post_id} to {target_agent_id}")
            except Exception as e:
                self.logger.error(f"Error sending publish task for post {post_id} to {target_agent_id}: {str(e)}")
    
    async def _handle_post_status_update(self, task: Task) -> None:
        """
        Handle a post status update task.
        
        Args:
            task: The task to process
        """
        try:
            # Extract data parts
            data_part = extract_data_part_by_content_type(task.data_parts, "application/json")
            if not data_part:
                raise ValueError("No content data found in task")
                
            data = data_part.data
            post_id = data.get("socialspark_post_id")
            platform = data.get("platform")
            status = data.get("status")
            platform_post_id = data.get("platform_post_id")
            error_message = data.get("error_message")
            
            # Validate required fields
            if not post_id:
                raise ValueError("socialspark_post_id is required")
            if not platform:
                raise ValueError("platform is required")
            if not status:
                raise ValueError("status is required")
                
            # Load post
            post = self.post_storage.get_post(post_id)
            if not post:
                self.logger.error(f"Post {post_id} not found for status update")
                return
                
            # Update post with platform post ID if successful
            if status == "success" and platform_post_id:
                post.platform_post_ids[platform] = platform_post_id
                self.logger.info(f"Post {post_id} successfully published to {platform} with ID {platform_post_id}")
            elif status == "failure":
                self.logger.error(f"Failed to publish post {post_id} to {platform}: {error_message}")
                # Could implement retry logic here
            
            # Update post
            post.updated_at = datetime.now()
            self.post_storage.save_post(post)
            
            # Save task
            self.task_storage.save_task(task)
            
        except Exception as e:
            self.logger.error(f"Error processing task {task.id}: {str(e)}")
            if not task.metadata:
                task.metadata = {}
            task.metadata["error"] = str(e)
            task.update_status(TaskStatus.FAILED)
    
    def start(self) -> None:
        """Start the agent and the scheduler."""
        # Start the background scheduler
        if not self.scheduler.running:
            self.scheduler.start()
            
        # Initialize the publish queue if it doesn't exist
        if not hasattr(self, '_publish_queue'):
            self._publish_queue = []
            
        self.logger.info(f"Started {self.name} at {self.agent_url}")
        
    def run(self, host: str = "0.0.0.0") -> None:
        """
        Run the agent's API server and start the scheduler.
        
        Args:
            host: Host to bind to, defaults to 0.0.0.0 (all interfaces)
        """
        # Start the agent and scheduler
        self.start()
        
        # Register a startup event to process the queue
        from fastapi import FastAPI
        app = self.app
        
        @app.on_event("startup")
        async def process_publish_queue():
            """Process any posts that were scheduled while FastAPI was starting up."""
            self.logger.info("FastAPI started, processing queued posts...")
            if hasattr(self, '_publish_queue') and self._publish_queue:
                for post_id in list(self._publish_queue):
                    try:
                        await self._publish_post(post_id)
                        self._publish_queue.remove(post_id)
                    except Exception as e:
                        self.logger.error(f"Error processing queued post {post_id}: {e}")
            
            # Set up a background task to periodically check for new items in the queue
            import asyncio
            
            async def check_queue_periodically():
                while True:
                    await asyncio.sleep(30)  # Check every 30 seconds
                    if hasattr(self, '_publish_queue') and self._publish_queue:
                        for post_id in list(self._publish_queue):
                            try:
                                await self._publish_post(post_id)
                                self._publish_queue.remove(post_id)
                            except Exception as e:
                                self.logger.error(f"Error processing queued post {post_id}: {e}")
            
            # Start the background task
            asyncio.create_task(check_queue_periodically())
        
        # Run the FastAPI app
        super().run(host) 