"""
Base Agent Implementation for SocialSpark Orchestrator.

This module provides the base agent class that all specialized agents
in the SocialSpark ecosystem will inherit from.
"""

import uuid
import logging
from typing import Any, Dict, List, Optional, Callable, Awaitable, Union
from datetime import datetime

from fastapi import FastAPI, HTTPException, Body, BackgroundTasks
from fastapi.responses import JSONResponse

from src.core.models import AgentCard, Task, DataPart, Capability, TaskStatus
from src.core.client import A2AClient


class BaseAgent:
    """
    Base class for all A2A agents.
    
    Provides common functionality for A2A protocol compliance and task handling.
    """
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        version: str = "0.1.0",
        base_url: str = "http://localhost",
        port: int = 8000,
    ):
        """
        Initialize a base agent.
        
        Args:
            agent_id: Unique identifier for this agent
            name: Human-readable name for this agent
            description: Detailed description of what this agent does
            version: Version of this agent, defaults to 0.1.0
            base_url: Base URL for this agent's API, defaults to localhost
            port: Port for this agent's API, defaults to 8000
        """
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.version = version
        self.base_url = base_url
        self.port = port
        
        # Full URL for this agent's API
        self.agent_url = f"{base_url}:{port}"
        
        # Task handlers registered by the agent
        self.task_handlers = {}
        
        # Tasks being processed by this agent
        self.tasks = {}
        
        # A2A client for communicating with other agents
        self.client = A2AClient(agent_id, base_url)
        
        # Logger for this agent
        self.logger = logging.getLogger(f"a2a.agent.{agent_id}")
        
        # Agent's capabilities
        self.capabilities = []
        
        # Create FastAPI app for this agent
        self.app = self._create_app()
        
    def _create_app(self) -> FastAPI:
        """Create a FastAPI application for this agent."""
        app = FastAPI(title=f"{self.name} API", description=self.description, version=self.version)
        
        # Define agent card endpoint
        @app.get("/card", response_model=AgentCard)
        async def get_agent_card():
            return self.get_agent_card()
        
        # Define task endpoints
        @app.post("/tasks", status_code=201, response_model=Task)
        async def create_task(background_tasks: BackgroundTasks, task: Task = Body(...)):
            return await self._handle_incoming_task(background_tasks, task)
        
        @app.get("/tasks/{task_id}", response_model=Task)
        async def get_task(task_id: str):
            if task_id not in self.tasks:
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
            return self.tasks[task_id]
        
        @app.patch("/tasks/{task_id}", response_model=Task)
        async def update_task(task_id: str, update_data: Dict[str, Any] = Body(...)):
            if task_id not in self.tasks:
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
            
            task = self.tasks[task_id]
            
            # Update fields from the request
            for key, value in update_data.items():
                if hasattr(task, key):
                    if key == "status" and isinstance(value, str):
                        task.update_status(TaskStatus(value))
                    else:
                        setattr(task, key, value)
                    
            task.updated_at = datetime.now()
            return task
        
        return app
    
    def get_agent_card(self) -> AgentCard:
        """
        Get this agent's AgentCard for discovery.
        
        Returns:
            AgentCard representation of this agent
        """
        endpoints = {
            "card": f"{self.agent_url}/card",
            "tasks": f"{self.agent_url}/tasks"
        }
        
        return AgentCard(
            id=self.agent_id,
            name=self.name,
            description=self.description,
            version=self.version,
            capabilities=self.capabilities,
            endpoints=endpoints
        )
    
    def add_capability(self, capability: Capability) -> None:
        """
        Add a capability to this agent.
        
        Args:
            capability: Capability to add
        """
        self.capabilities.append(capability)
    
    def register_task_handler(self, task_type: str, handler: Callable[[Task], Awaitable[None]]) -> None:
        """
        Register a handler for a specific task type.
        
        Args:
            task_type: Type of task this handler can process
            handler: Async function to call when a task of this type is received
        """
        self.task_handlers[task_type] = handler
        self.logger.info(f"Registered handler for task type: {task_type}")
    
    async def _handle_incoming_task(self, background_tasks: BackgroundTasks, task: Task) -> Task:
        """
        Handle an incoming task from another agent.
        
        Args:
            background_tasks: FastAPI BackgroundTasks for async processing
            task: The task to handle
            
        Returns:
            The task (possibly updated)
            
        Raises:
            HTTPException: If the task is invalid or can't be handled
        """
        # Validate the task is for this agent
        if task.target_agent_id != self.agent_id:
            raise HTTPException(status_code=400, detail=f"Task target {task.target_agent_id} does not match this agent ({self.agent_id})")
        
        # Check if we have a handler for this task type
        if task.type not in self.task_handlers:
            raise HTTPException(status_code=400, detail=f"No handler for task type: {task.type}")
        
        # Store the task
        self.tasks[task.id] = task
        
        # Update status to in progress
        task.update_status(TaskStatus.IN_PROGRESS)
        
        # Process the task in the background
        background_tasks.add_task(self._process_task, task)
        
        return task
    
    async def _process_task(self, task: Task) -> None:
        """
        Process a task in the background.
        
        Args:
            task: The task to process
        """
        handler = self.task_handlers[task.type]
        
        try:
            self.logger.info(f"Processing task {task.id} of type {task.type}")
            await handler(task)
            task.update_status(TaskStatus.COMPLETED)
            self.logger.info(f"Successfully completed task {task.id}")
        except Exception as e:
            self.logger.error(f"Error processing task {task.id}: {str(e)}")
            task.update_status(TaskStatus.FAILED)
            if not task.metadata:
                task.metadata = {}
            task.metadata["error"] = str(e)
    
    async def send_task(
        self, 
        target_agent_id: str, 
        task_type: str, 
        data_parts: List[Dict[str, Any]] = None,
        parent_task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Task]:
        """
        Send a task to another agent.
        
        Args:
            target_agent_id: ID of the target agent
            task_type: Type of task to send
            data_parts: Data parts to include in the task
            parent_task_id: Optional ID of a parent task
            metadata: Optional additional metadata
            
        Returns:
            The created task if successful, None otherwise
        """
        return await self.client.create_task(
            target_agent_id=target_agent_id,
            task_type=task_type,
            data_parts=data_parts,
            parent_task_id=parent_task_id,
            metadata=metadata
        )
    
    def run(self, host: str = "0.0.0.0") -> None:
        """
        Run this agent's API server.
        
        This method doesn't return until the server is shut down.
        
        Args:
            host: Host to bind to, defaults to 0.0.0.0 (all interfaces)
        """
        import uvicorn
        uvicorn.run(self.app, host=host, port=self.port) 