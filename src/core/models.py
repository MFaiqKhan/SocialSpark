"""
A2A Protocol Data Models for SocialSpark Orchestrator.

These models define the core data structures used for communication
between agents in the Agent2Agent (A2A) protocol implementation.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Status values for A2A tasks."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class DataPart(BaseModel):
    """
    Represents a data part in an A2A task.
    
    Data parts are structured pieces of information exchanged between agents.
    """
    id: str = Field(..., description="Unique identifier for this data part")
    content_type: str = Field(..., description="MIME type of the data")
    data: Dict[str, Any] = Field(..., description="The actual data payload")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata about this data part")


class Task(BaseModel):
    """
    Represents an A2A task or message between agents.
    
    Tasks are the primary mechanism for agents to request actions from each other.
    """
    id: str = Field(..., description="Unique identifier for this task")
    type: str = Field(..., description="The type of task to be performed")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Current status of the task")
    created_at: datetime = Field(default_factory=datetime.now, description="When the task was created")
    updated_at: datetime = Field(default_factory=datetime.now, description="When the task was last updated")
    source_agent_id: str = Field(..., description="ID of the agent creating the task")
    target_agent_id: str = Field(..., description="ID of the agent that should perform the task")
    data_parts: List[DataPart] = Field(default_factory=list, description="Data parts containing task information")
    parent_task_id: Optional[str] = Field(None, description="ID of a parent task, if this is a subtask")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata about this task")
    
    def add_data_part(self, data_part: DataPart) -> None:
        """Add a data part to this task."""
        self.data_parts.append(data_part)
        self.updated_at = datetime.now()
    
    def update_status(self, status: TaskStatus) -> None:
        """Update the status of this task."""
        self.status = status
        self.updated_at = datetime.now()


class Capability(BaseModel):
    """
    Defines a capability that an agent can perform.
    
    Part of the AgentCard discovery mechanism in A2A.
    """
    id: str = Field(..., description="Unique identifier for this capability")
    name: str = Field(..., description="Human-readable name of the capability")
    description: str = Field(..., description="Detailed description of what this capability does")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Parameters that this capability accepts")
    required_capabilities: Optional[List[str]] = Field(None, description="IDs of capabilities required for this one to work")


class AgentCard(BaseModel):
    """
    Represents information about an agent in the A2A ecosystem.
    
    AgentCards are used for discovery and capability advertisement.
    """
    id: str = Field(..., description="Unique identifier for this agent")
    name: str = Field(..., description="Human-readable name of the agent")
    description: str = Field(..., description="Detailed description of what this agent does")
    version: str = Field(..., description="Version of this agent")
    capabilities: List[Capability] = Field(default_factory=list, description="List of capabilities this agent supports")
    endpoints: Dict[str, str] = Field(..., description="API endpoints this agent exposes")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata about this agent")
    
    def add_capability(self, capability: Capability) -> None:
        """Add a capability to this agent."""
        self.capabilities.append(capability) 