"""
Content Adaptation for Content & Scheduling Agent.

This module provides functionality to adapt content for different social platforms.
"""

import re
import logging
from typing import List, Set, Dict, Any, Optional

from src.agents.content_scheduler.models import (
    SocialPlatform, PlatformSpecificContent, ContentAdaptationRules
)


def extract_hashtags(text: str) -> List[str]:
    """
    Extract hashtags from text.
    
    Args:
        text: Text to extract hashtags from
        
    Returns:
        List of hashtags (without the # symbol)
    """
    # Find all hashtags in the text (word starting with # and containing only word chars)
    matches = re.findall(r'#(\w+)', text)
    return matches


def format_hashtags(hashtags: List[str], hashtag_format: str) -> List[str]:
    """
    Format hashtags according to platform-specific format.
    
    Args:
        hashtags: List of hashtags (without the # symbol)
        hashtag_format: Format string for hashtags, where {} is replaced with the hashtag text
        
    Returns:
        List of formatted hashtags
    """
    return [hashtag_format.format(tag) for tag in hashtags]


def truncate_text(text: str, max_length: int) -> str:
    """
    Truncate text to maximum length while preserving whole words.
    
    Args:
        text: Text to truncate
        max_length: Maximum length in characters
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
        
    # Truncate to max_length
    truncated = text[:max_length]
    
    # Find the last space to avoid cutting words
    last_space = truncated.rfind(' ')
    if last_space > 0:
        truncated = truncated[:last_space]
    
    # Add ellipsis if truncated
    if len(truncated) < len(text):
        truncated += "..."
        
    return truncated


def adapt_content_for_platform(
    raw_text: str,
    image_reference: Optional[str],
    platform: SocialPlatform,
    rules: ContentAdaptationRules
) -> PlatformSpecificContent:
    """
    Adapt content for a specific platform.
    
    Args:
        raw_text: Original text content
        image_reference: Reference to image file, if any
        platform: Target social platform
        rules: Content adaptation rules for the platform
        
    Returns:
        Platform-specific content
    """
    # Extract hashtags from the raw text
    hashtags = extract_hashtags(raw_text)
    
    # Format hashtags according to platform rules
    formatted_hashtags = format_hashtags(hashtags, rules.hashtag_format)
    
    # Remove hashtags from text (we'll add them back formatted)
    clean_text = re.sub(r'#\w+', '', raw_text).strip()
    
    # Truncate text if necessary
    max_text_length = rules.max_text_length
    if hashtags:
        # Reserve some characters for hashtags if present
        hashtag_text = " ".join(formatted_hashtags)
        max_content_length = max_text_length - len(hashtag_text) - 1  # -1 for space
        if max_content_length < 0:
            max_content_length = int(max_text_length / 2)  # Fallback if there are too many hashtags
            
        truncated_text = truncate_text(clean_text, max_content_length)
        
        # Add hashtags back at the end
        if truncated_text and hashtag_text:
            adapted_text = f"{truncated_text} {hashtag_text}"
        else:
            adapted_text = truncated_text or hashtag_text
    else:
        # No hashtags, just truncate the text
        adapted_text = truncate_text(clean_text, max_text_length)
    
    # Check if image is allowed/required for this platform
    adapted_image_reference = image_reference
    platform_metadata = {}
    
    image_requirements = rules.image_requirements or {}
    
    # Handle platform-specific image requirements
    if platform == SocialPlatform.INSTAGRAM and image_requirements.get("required", False) and not image_reference:
        # Instagram requires an image
        platform_metadata["warning"] = "Instagram requires an image for posts"
    
    if platform == SocialPlatform.TWITTER and image_reference and image_requirements.get("max_images", 0) > 0:
        # Twitter supports multiple images, but we're just using one here
        platform_metadata["images_count"] = 1
    
    return PlatformSpecificContent(
        platform=platform,
        text=adapted_text,
        image_reference=adapted_image_reference,
        hashtags=hashtags,
        metadata=platform_metadata
    ) 