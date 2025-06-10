"""
Utility functions for SocialSpark Orchestrator.

This module provides common utility functions used across the SocialSpark agents.
"""

import os
import json
import uuid
import logging
import base64
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from src.core.models import DataPart


def generate_id() -> str:
    """
    Generate a unique ID.
    
    Returns:
        A UUID as a string
    """
    return str(uuid.uuid4())


def create_data_part(
    data: Dict[str, Any], content_type: str = "application/json", metadata: Optional[Dict[str, Any]] = None
) -> DataPart:
    """
    Create a new data part.
    
    Args:
        data: The data payload
        content_type: MIME type of the data, defaults to application/json
        metadata: Optional metadata
        
    Returns:
        A new DataPart instance
    """
    return DataPart(
        id=generate_id(),
        content_type=content_type,
        data=data,
        metadata=metadata
    )


def encode_image(image_path: str) -> str:
    """
    Encode an image to base64 for transmission.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Base64-encoded image data as a string
    """
    try:
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode('utf-8')
            return encoded
    except Exception as e:
        logging.error(f"Error encoding image: {e}")
        return ""


def decode_image(base64_data: str, output_path: str) -> bool:
    """
    Decode a base64-encoded image and save it.
    
    Args:
        base64_data: Base64-encoded image data
        output_path: Path to save the decoded image
        
    Returns:
        True if successful, False otherwise
    """
    try:
        image_data = base64.b64decode(base64_data)
        with open(output_path, "wb") as image_file:
            image_file.write(image_data)
        return True
    except Exception as e:
        logging.error(f"Error decoding image: {e}")
        return False


def extract_data_part_by_content_type(task_data_parts: List[DataPart], content_type: str) -> Optional[DataPart]:
    """
    Extract a data part from a task by content type.
    
    Args:
        task_data_parts: List of data parts from a task
        content_type: Content type to look for
        
    Returns:
        Matching DataPart if found, None otherwise
    """
    for data_part in task_data_parts:
        if data_part.content_type == content_type:
            return data_part
    return None


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format a datetime object to a string.
    
    Args:
        dt: Datetime object to format
        format_str: Format string, defaults to ISO-like format
        
    Returns:
        Formatted datetime string
    """
    return dt.strftime(format_str)


def parse_datetime(dt_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    """
    Parse a datetime string to a datetime object.
    
    Args:
        dt_str: Datetime string to parse
        format_str: Format string, defaults to ISO-like format
        
    Returns:
        Datetime object if successful, None otherwise
    """
    try:
        return datetime.strptime(dt_str, format_str)
    except ValueError as e:
        logging.error(f"Error parsing datetime: {e}")
        return None


def save_to_json_file(data: Any, file_path: str) -> bool:
    """
    Save data to a JSON file.
    
    Args:
        data: Data to save
        file_path: Path to the output file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        return True
    except Exception as e:
        logging.error(f"Error saving to JSON file: {e}")
        return False


def load_from_json_file(file_path: str) -> Optional[Any]:
    """
    Load data from a JSON file.
    
    Args:
        file_path: Path to the input file
        
    Returns:
        Loaded data if successful, None otherwise
    """
    try:
        if not os.path.exists(file_path):
            return None
            
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading from JSON file: {e}")
        return None 