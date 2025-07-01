import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def get_api_key() -> str:
    """
    Dependency function to get API key for endpoints.
    In Flask, this is simpler since we handle rotation in the client.
    """
    # Return a placeholder since we handle rotation in the client
    api_key = os.getenv("SURFE_API_KEY", "default_key")
    return api_key

def validate_request_data(data: dict) -> bool:
    """Validate common request data structure"""
    if not isinstance(data, dict):
        return False
    
    # Basic validation for people search
    has_company_filters = bool(data.get("companies"))
    has_people_filters = bool(data.get("people"))
    
    return has_company_filters or has_people_filters
