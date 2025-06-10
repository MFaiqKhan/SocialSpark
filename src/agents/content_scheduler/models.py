"""
Content & Scheduling Agent models.

This module defines data models specific to the Content & Scheduling Agent.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ContentType(str, Enum):
    """Types of social media content."""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    LINK = "link"
    MIXED = "mixed"


class PostStatus(str, Enum):
    """Status values for scheduled posts."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELED = "canceled"


class SocialPlatform(str, Enum):
    """Supported social media platforms."""
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"


class PlatformSpecificContent(BaseModel):
    """Content adapted for a specific platform."""
    platform: SocialPlatform = Field(..., description="Target social media platform")
    text: str = Field(..., description="Platform-specific text content")
    image_reference: Optional[str] = Field(None, description="Reference to image, if any")
    link: Optional[str] = Field(None, description="URL to include, if any")
    hashtags: List[str] = Field(default_factory=list, description="Hashtags for this post")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Platform-specific metadata")


class ScheduledPost(BaseModel):
    """A post scheduled for publication on one or more platforms."""
    id: str = Field(..., description="Unique identifier for this post")
    user_id: str = Field(..., description="ID of the user who owns this post")
    raw_text: str = Field(..., description="Original text content")
    content_type: ContentType = Field(..., description="Type of content")
    image_reference: Optional[str] = Field(None, description="Reference to image, if content contains an image")
    target_platforms: List[SocialPlatform] = Field(..., description="Platforms to publish to")
    schedule_time: datetime = Field(..., description="When to publish this post")
    status: PostStatus = Field(default=PostStatus.DRAFT, description="Current status of this post")
    platform_specific_content: Dict[str, PlatformSpecificContent] = Field(
        default_factory=dict, description="Content adapted for each platform"
    )
    platform_post_ids: Dict[str, str] = Field(
        default_factory=dict, description="IDs of the posts on each platform"
    )
    credentials: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Platform-specific credentials (e.g. page_id for Facebook)"
    )
    created_at: datetime = Field(default_factory=datetime.now, description="When this post was created")
    updated_at: datetime = Field(default_factory=datetime.now, description="When this post was last updated")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ContentAdaptationRules(BaseModel):
    """Rules for adapting content to different platforms."""
    platform: SocialPlatform = Field(..., description="Target platform")
    max_text_length: int = Field(..., description="Maximum text length for this platform")
    hashtag_format: str = Field(..., description="How hashtags should be formatted")
    image_requirements: Optional[Dict[str, Any]] = Field(None, description="Image requirements for this platform")


class SocialMediaCredentials(BaseModel):
    """Credentials for accessing a social media platform."""
    platform: SocialPlatform = Field(..., description="Platform these credentials are for")
    user_id: str = Field(..., description="ID of the user who owns these credentials")
    access_token: str = Field(..., description="OAuth access token")
    refresh_token: Optional[str] = Field(None, description="OAuth refresh token, if available")
    token_expiry: Optional[datetime] = Field(None, description="When the access token expires")
    account_name: str = Field(..., description="Name of the connected social media account")
    account_id: str = Field(..., description="ID of the connected social media account")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional platform-specific metadata") 